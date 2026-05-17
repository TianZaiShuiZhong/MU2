import json
import os
import sys
import io
import zipfile

import requests

from agent import UniversalDataAgent
from mineru_client import MinerUClient

PDF_URL = "https://notice.10jqka.com.cn/api/pdf/e8639a5eb576c085.pdf"
TARGET_METRICS = ["营业收入", "资产总计", "负债合计", "所有者权益合计"]
PAGE_RANGES = "114-130"


def main() -> int:
    if not os.environ.get("MINERU_API_TOKEN"):
        raise RuntimeError("MINERU_API_TOKEN is not set")
    if not (os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_API_TOKEN")):
        raise RuntimeError("DEEPSEEK_API_KEY/DEEPSEEK_API_TOKEN is not set")

    client = MinerUClient()
    print(f"mineru_base_url={client.base_url}")
    task_id = client.submit_task(PDF_URL, page_ranges=PAGE_RANGES)
    print(f"mineru_task_id={task_id}")

    agent = UniversalDataAgent()

    mineru_result = client.poll_task_result(task_id, timeout_seconds=900, poll_interval=10)
    print(f"mineru_result_keys={sorted(mineru_result.keys())}")
    print(f"mineru_result_summary={json.dumps(mineru_result, ensure_ascii=False)[:1500]}")

    zip_url = mineru_result.get("full_zip_url") or mineru_result.get("download_url")
    if zip_url:
        content = requests.get(zip_url, timeout=120).content
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            markdown_files = [name for name in archive.namelist() if name.endswith(".md")]
            print(f"markdown_files={markdown_files}")
            if markdown_files:
                markdown_text = archive.read(markdown_files[0]).decode("utf-8", errors="ignore")
                print("markdown_preview_start")
                print(markdown_text[:6000])
                print("markdown_preview_end")
                direct_candidates = agent._extract_financial_candidates(markdown_text, TARGET_METRICS)
                print(f"direct_candidates={json.dumps(direct_candidates, ensure_ascii=False)}")

    try:
        structured = agent.process_parsed_data(mineru_result, TARGET_METRICS, "financial")
        print(f"structured_result={json.dumps(structured, ensure_ascii=False, indent=2)}")
    except Exception as exc:
        print(f"agent_error={type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
