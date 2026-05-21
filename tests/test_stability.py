import asyncio
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_agent import main


class FakeMinerUClient:
    def __init__(self):
        self.task_counter = 0

    def submit_task(
        self,
        file_url: str,
        is_html: bool = False,
        enable_ocr: bool = False,
        page_ranges: str | None = None,
    ) -> str:
        self.task_counter += 1
        return f"fake-mineru-task-{self.task_counter}"

    def poll_task_result(self, task_id: str, timeout_seconds: int = 300, poll_interval: int = 5) -> dict:
        return {
            "task_id": task_id,
            "state": "done",
            "full_zip_url": "https://example.com/fake-result.zip",
        }


class FakeUniversalDataAgent:
    def process_parsed_data(self, mineru_result: dict, target_metrics: list[str], scenario: str = "financial") -> dict:
        return {metric: f"value-for-{metric}" for metric in target_metrics}


async def run_one_job(index: int) -> None:
    request = main.ProcessRequest(
        task_name=f"stability-job-{index}",
        file_url="https://example.com/sample.pdf",
        target_metrics=["营业收入", "资产总计", "负债合计", "所有者权益合计"],
        is_html=False,
        scenario="financial",
    )
    job_id = str(uuid.uuid4())
    main.set_task(
        job_id,
        {
            "status": "queued",
            "created_at": main.utc_now_iso(),
            "updated_at": main.utc_now_iso(),
        },
    )
    await asyncio.to_thread(main.agent_background_task, request, job_id)
    status_response = await main.get_status(job_id)
    data = status_response["data"]
    assert data["status"] == "success", data
    assert data["result"]["营业收入"] == "value-for-营业收入", data


async def main_async() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "task_db.json"

        original_task_db_path = main.TASK_DB_PATH
        original_task_db = main.task_db
        original_mineru_client = main.MinerUClient
        original_agent = main.UniversalDataAgent

        try:
            main.TASK_DB_PATH = temp_path
            main.task_db = {}
            main.MinerUClient = FakeMinerUClient
            main.UniversalDataAgent = FakeUniversalDataAgent

            await asyncio.gather(*(run_one_job(index) for index in range(8)))

            main.set_task(
                "expired-job",
                {
                    "status": "success",
                    "created_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
                    "updated_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
                    "result": {"营业收入": "stale"},
                },
            )
            removed = main.cleanup_task_db()
            assert removed >= 1, removed
            assert "expired-job" not in main.task_db, main.task_db

            health = await main.health_check()
            assert health["data"]["status"] == "healthy", health
            assert health["data"]["task_count"] >= 8, health

            print(
                "stability validation passed | "
                f"parallel_jobs=8 | removed_expired={removed} | task_count={health['data']['task_count']}"
            )
        finally:
            main.TASK_DB_PATH = original_task_db_path
            main.task_db = original_task_db
            main.MinerUClient = original_mineru_client
            main.UniversalDataAgent = original_agent


if __name__ == "__main__":
    asyncio.run(main_async())
