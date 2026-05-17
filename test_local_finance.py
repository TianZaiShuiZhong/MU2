import asyncio
import tempfile
from pathlib import Path

from fastapi import BackgroundTasks

import main


class FakeMinerUClient:
    def submit_task(
        self,
        file_url: str,
        is_html: bool = False,
        enable_ocr: bool = False,
        page_ranges: str | None = None,
    ) -> str:
        return "fake-mineru-task-id"

    def poll_task_result(self, task_id: str, timeout_seconds: int = 300, poll_interval: int = 5) -> dict:
        return {"full_zip_url": "https://example.com/fake-result.zip"}


class FakeUniversalDataAgent:
    def process_parsed_data(self, mineru_result: dict, target_metrics: list[str], scenario: str = "financial") -> dict:
        return {
            metric: f"value-for-{metric}"
            for metric in target_metrics
        }


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

            request = main.ProcessRequest(
                task_name="local smoke test",
                file_url="https://example.com/sample.pdf",
                target_metrics=["营业收入", "资产总计"],
                is_html=False,
                scenario="financial",
            )

            background_tasks = BackgroundTasks()
            response = await main.start_process(request, background_tasks)
            job_id = response["job_id"]

            await asyncio.to_thread(main.agent_background_task, request, job_id)

            status_response = await main.get_status(job_id)
            data = status_response["data"]
            assert data["status"] == "success", data
            assert data["result"]["营业收入"] == "value-for-营业收入"
            assert temp_path.exists(), "task_db.json was not created"

            health = await main.health_check()
            assert health["data"]["status"] == "healthy", health
            assert health["data"]["task_count"] >= 1, health

            print("local smoke test passed")
        finally:
            main.TASK_DB_PATH = original_task_db_path
            main.task_db = original_task_db
            main.MinerUClient = original_mineru_client
            main.UniversalDataAgent = original_agent


if __name__ == "__main__":
    asyncio.run(main_async())
