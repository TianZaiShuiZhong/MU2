import io
import zipfile
from unittest.mock import patch

from agent import UniversalDataAgent


class FakeResponse:
    def __init__(self, text: str = "", content: bytes = b""):
        self.text = text
        self.content = content

    def raise_for_status(self) -> None:
        return None


def build_zip_with_markdown(markdown: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("full.md", markdown)
    return buffer.getvalue()


def main() -> None:
    agent = UniversalDataAgent(llm_api_key="unit-test-key")

    with patch("agent.requests.get", return_value=FakeResponse(text="# Markdown from lightweight API")):
        markdown = agent.download_and_extract_md({"markdown_url": "https://example.com/full.md"})
        assert markdown == "# Markdown from lightweight API"

    zip_bytes = build_zip_with_markdown("# Markdown from zip")
    with patch("agent.requests.get", return_value=FakeResponse(content=zip_bytes)):
        markdown = agent.download_and_extract_md({"full_zip_url": "https://example.com/result.zip"})
        assert markdown == "# Markdown from zip"

    valid, reason = agent._verify_results(
        {"资产总计": "100", "负债合计": "40", "所有者权益合计": "60"},
        "financial",
        ["资产总计", "负债合计", "所有者权益合计"],
    )
    assert valid, reason

    invalid, reason = agent._verify_results(
        {"资产总计": "100", "负债合计": "40", "所有者权益合计": "50"},
        "financial",
        ["资产总计", "负债合计", "所有者权益合计"],
    )
    assert not invalid, reason

    financial_table = (
        "<table><tr><td>营业收入</td><td>40</td><td>101,450,670</td><td>90,736,582</td></tr>"
        "<tr><td>资产总计</td><td></td><td>150,634,906</td><td>141,202,135</td></tr>"
        "<tr><td>流动负债合计</td><td></td><td>74,394,975</td><td>86,370,516</td></tr>"
        "<tr><td>负债合计</td><td></td><td>104,512,400</td><td>103,247,837</td></tr>"
        "<tr><td>归属于母公司普通股股东权益合计</td><td></td><td>43,296,808</td><td>28,826,868</td></tr>"
        "<tr><td>股东权益合计</td><td></td><td>46,122,506</td><td>37,954,298</td></tr></table>"
    )
    extracted = agent._extract_financial_candidates(
        financial_table,
        ["营业收入", "资产总计", "负债合计", "所有者权益合计"],
    )
    assert extracted["营业收入"] == "101450670", extracted
    assert extracted["负债合计"] == "104512400", extracted
    assert extracted["所有者权益合计"] == "46122506", extracted

    print("agent unit validation passed")


if __name__ == "__main__":
    main()
