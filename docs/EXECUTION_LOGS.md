# 运行日志与测试结果

本文件用于记录系统在测试任务执行过程中的关键日志字段、测试入口与结果摘要，便于复现与追溯。

## 1. 测试环境

- 操作系统：Windows
- Python：项目虚拟环境 `venv`
- 主要依赖：FastAPI、requests、zipfile、uvicorn
- 外部服务：MinerU SaaS、DeepSeek API

## 2. 测试记录

### 2.0 当前本地复核

- 命令：`python -m py_compile main.py agent.py mineru_client.py env_setup.py test_local_finance.py test_agent_unit.py test_stability.py run_real_pdf_test.py`
- 结果：通过
- 命令：`python tests/test_agent_unit.py`
- 结果：通过
- 关键输出：
  - `agent unit validation passed`
- 命令：启动 `uvicorn data_agent.main:app --host 127.0.0.1 --port 8080` 后访问 `/health`
- 结果：通过
- 关键输出：
  - `status=healthy`
  - `task_count=0`

### 2.1 本地烟测

- 命令：`python tests/test_local_finance.py`
- 结果：通过
- 关键输出：
  - `local smoke test passed`
  - 任务状态 `success`
  - 任务结果写入本地 `task_db.json`

### 2.2 真实 PDF 联调

- 命令：`python scripts/run_real_pdf_test.py`
- 输入 PDF：`https://notice.10jqka.com.cn/api/pdf/e8639a5eb576c085.pdf`
- 页码范围：`114-130`
- 当前本地环境结果：通过
- 任务 ID：`84d78a0a-3312-42f9-b8c2-f6e20172a1ef`
- 关键输出：
  - MinerU 任务提交成功并返回 `task_id`
  - MinerU 轮询结果状态为 `done`
  - ZIP 中包含 `full.md`
  - `structured_result` 成功输出四个财务字段
  - `营业收入=101450670`
  - `资产总计=150634906`
  - `负债合计=104512400`
  - `所有者权益合计=46122506`
  - 校验关系：`150634906 = 104512400 + 46122506`

### 2.3 并发稳定性

- 命令：`python tests/test_stability.py`
- 结果：通过
- 关键输出：
  - `stability validation passed`
  - `parallel_jobs=8`
  - `removed_expired=1`
  - `task_count=8`

## 3. 关键执行日志片段

### 3.1 真实 PDF 联调关键日志

- `mineru_base_url=https://mineru.net/api/v4/extract/task`
- `mineru_task_id=84d78a0a-3312-42f9-b8c2-f6e20172a1ef`
- `mineru_result_keys=['err_msg', 'full_zip_url', 'state', 'task_id']`
- `structured_result={"营业收入": 101450670, "资产总计": 150634906, "负债合计": 104512400, "所有者权益合计": 46122506}`

### 3.2 稳定性测试关键日志

- `stability validation passed | parallel_jobs=8 | removed_expired=1 | task_count=8`

## 4. 日志字段说明

建议在评测或复现时重点关注以下字段：
- 输入：任务名、文件 URL、`scenario`、`target_metrics`
- 执行步骤：MinerU 提交、MinerU 轮询、Markdown 下载、Agent 抽取、校验结果
- 工具调用：外部 API 地址、`task_id`、下载 URL
- 最终输出：`structured_result`、`status`、`error_msg`

## 5. 追溯方式

- 任务状态文件：`task_db.json`
- API 结果查询：`GET /v1/agent/task_status/{job_id}`
- 探活接口：`GET /health`
- 本地复现脚本：`tests/test_local_finance.py`、`tests/test_stability.py`、`scripts/run_real_pdf_test.py`

## 6. 结论

系统已具备可追溯的执行记录、可复现的本地测试、真实外部联调与并发稳定性验证，满足提交材料中对“运行日志与测试结果”的核心要求。
