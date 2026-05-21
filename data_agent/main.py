from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
from datetime import datetime, timezone
import json
import logging
import threading

from data_agent.mineru_client import MinerUClient
from data_agent.agent import UniversalDataAgent

app = FastAPI(title="Data Agent - 财报核心指标精准解析", version="1.0")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataAgentAPI")

TASK_DB_PATH = Path(__file__).resolve().parent.parent / "task_db.json"
task_db_lock = threading.Lock()
TASK_RETENTION_SECONDS = 24 * 60 * 60

TERMINAL_STATUSES = {"success", "failed"}

# 模型声明 (用于评测系统 API 传递参数)
class ProcessRequest(BaseModel):
    task_name: str
    file_url: str
    target_metrics: List[str] # 比如 ["营业收入", "净利润", "总资产"]
    is_html: Optional[bool] = False
    scenario: Optional[str] = "financial"  # 新增：支持多场景路由
    page_ranges: Optional[str] = None  # 可选：限制 MinerU 解析页码，如 "1-30"

def load_task_db() -> dict:
    if not TASK_DB_PATH.exists():
        return {}

    try:
        return json.loads(TASK_DB_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning(f"加载任务状态文件失败，将使用空状态: {exc}")
        return {}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def set_task(job_id: str, payload: dict) -> None:
    with task_db_lock:
        task_db[job_id] = payload
        TASK_DB_PATH.write_text(json.dumps(task_db, ensure_ascii=False, indent=2), encoding="utf-8")


def update_task(job_id: str, **fields) -> None:
    with task_db_lock:
        current = task_db.get(job_id, {})
        current.update(fields)
        current["updated_at"] = utc_now_iso()
        task_db[job_id] = current
        TASK_DB_PATH.write_text(json.dumps(task_db, ensure_ascii=False, indent=2), encoding="utf-8")


def cleanup_task_db() -> int:
    cutoff = datetime.now(timezone.utc).timestamp() - TASK_RETENTION_SECONDS
    removed = 0

    with task_db_lock:
        for job_id, record in list(task_db.items()):
            if record.get("status") not in TERMINAL_STATUSES:
                continue

            timestamp_text = record.get("updated_at") or record.get("created_at")
            timestamp = parse_iso_datetime(timestamp_text) if timestamp_text else None
            if timestamp is None:
                continue

            if timestamp.timestamp() < cutoff:
                task_db.pop(job_id, None)
                removed += 1

        if removed:
            TASK_DB_PATH.write_text(json.dumps(task_db, ensure_ascii=False, indent=2), encoding="utf-8")

    return removed


# 存储任务结果，使用本地 JSON 文件做最小持久化
task_db = load_task_db()


@app.on_event("startup")
async def startup_cleanup():
    removed = cleanup_task_db()
    if removed:
        logger.info(f"启动时清理了 {removed} 条过期任务记录")

def agent_background_task(req: ProcessRequest, job_id: str):
    """
    后台任务：调用 MinerU 提取，并在完成后由 Agent 调用大模型解析。
    """
    try:
        # 1. 提交底座大模型解析 (工具调用阶段)
        client = MinerUClient()
        mineru_task_id = client.submit_task(req.file_url, req.is_html, page_ranges=req.page_ranges)
        
        # 更新状态
        update_task(job_id, status="parsing_document", mineru_task_id=mineru_task_id)
        
        # 2. 轮询结果 (长耗时操作)
        mineru_result = client.poll_task_result(mineru_task_id)
        update_task(job_id, status="agent_processing")
        
        # 3. Agent 核心提取与认知
        agent = UniversalDataAgent()
        structured_data = agent.process_parsed_data(mineru_result, req.target_metrics, req.scenario)
        
        # 4. 落地最终结构化结果
        set_task(job_id, {
            "status": "success",
            "created_at": task_db.get(job_id, {}).get("created_at", utc_now_iso()),
            "updated_at": utc_now_iso(),
            "result": structured_data
        })
        
    except Exception as e:
        logging.error(f"任务 {job_id} 执行出错: {str(e)}")
        set_task(job_id, {
            "status": "failed",
            "created_at": task_db.get(job_id, {}).get("created_at", utc_now_iso()),
            "updated_at": utc_now_iso(),
            "error_msg": str(e)
        })

@app.post("/v1/agent/process")
async def start_process(req: ProcessRequest, background_tasks: BackgroundTasks):
    """
    赛事评测系统对接 API：提交文档和抽取指标，开启异步 Agent 处理
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    set_task(job_id, {
        "status": "queued",
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso()
    })
    
    # 放入后台执行，防止超时
    background_tasks.add_task(agent_background_task, req, job_id)
    
    return {"code": 0, "msg": "ok", "job_id": job_id}

@app.get("/v1/agent/task_status/{job_id}")
async def get_status(job_id: str):
    """
    查询 Agent 处理进度与结果
    """
    if job_id not in task_db:
        raise HTTPException(status_code=404, detail="Job ID not found")
        
    return {"code": 0, "msg": "ok", "data": task_db[job_id]}

@app.get("/health")
async def health_check():
    cleanup_task_db()
    return {
        "code": 0,
        "msg": "ok",
        "data": {
            "status": "healthy",
            "task_count": len(task_db)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("data_agent.main:app", host="0.0.0.0", port=8080, reload=True)
