import argparse
import json
import os
import sys
import io
import zipfile
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_agent.agent import UniversalDataAgent
from data_agent.mineru_client import MinerUClient

PDF_URL = "https://notice.10jqka.com.cn/api/pdf/e8639a5eb576c085.pdf"
TARGET_METRICS = ["营业收入", "资产总计", "负债合计", "所有者权益合计"]
PAGE_RANGES = "114-130"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a real MinerU + Data Agent PDF validation.")
    parser.add_argument(
        "--pdf-url",
        default=PDF_URL,
        help="PDF URL to submit to MinerU.",
    )
    parser.add_argument(
        "--page-ranges",
        default=PAGE_RANGES,
        help='Optional page range passed to MinerU, for example "114-130". Use "" to parse all pages.',
    )
    parser.add_argument(
        "--metrics",
        nargs="+",
        default=TARGET_METRICS,
        help="Target metric names to extract.",
    )
    parser.add_argument(
        "--scenario",
        default="financial",
        choices=["financial", "coreference_cross_page", "low_quality_ocr", "industry_spec"],
        help="Agent scenario.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=900,
        help="Maximum seconds to wait for MinerU result.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    page_ranges = args.page_ranges or None

    if not os.environ.get("MINERU_API_TOKEN"):
        raise RuntimeError("MINERU_API_TOKEN is not set")
    if not (os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_API_TOKEN")):
        raise RuntimeError("DEEPSEEK_API_KEY/DEEPSEEK_API_TOKEN is not set")

    client = MinerUClient()
    print(f"pdf_url={args.pdf_url}")
    print(f"page_ranges={page_ranges}")
    print(f"scenario={args.scenario}")
    print(f"target_metrics={json.dumps(args.metrics, ensure_ascii=False)}")
    print(f"mineru_base_url={client.base_url}")
    task_id = client.submit_task(args.pdf_url, page_ranges=page_ranges)
    print(f"mineru_task_id={task_id}")

    agent = UniversalDataAgent()

    mineru_result = client.poll_task_result(task_id, timeout_seconds=args.timeout_seconds, poll_interval=10)
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
                direct_candidates = agent._extract_financial_candidates(markdown_text, args.metrics)
                print(f"direct_candidates={json.dumps(direct_candidates, ensure_ascii=False)}")

    try:
        structured = agent.process_parsed_data(mineru_result, args.metrics, args.scenario)
        print(f"structured_result={json.dumps(structured, ensure_ascii=False, indent=2)}")
    except Exception as exc:
        print(f"agent_error={type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
