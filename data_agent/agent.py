import json
import logging
import os
import requests
import zipfile
import io
import re

from data_agent.env_setup import load_environment

load_environment()

logger = logging.getLogger("FinanceAgent")

class UniversalDataAgent:
    def __init__(self, llm_api_key: str = None):
        """
        大语言模型初始化（接入 DeepSeek）
        """
        self.api_key = llm_api_key or os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_API_TOKEN")
        if not self.api_key:
            raise ValueError("未配置 DeepSeek API 密钥，请设置 DEEPSEEK_API_KEY 或 DEEPSEEK_API_TOKEN")
        self.llm_base_url = "https://api.deepseek.com/chat/completions"

    def process_parsed_data(self, mineru_result: dict, target_metrics: list[str], scenario: str = "financial") -> dict:
        """
        核心能力二：复杂任务规划与自动执行，将数据清洗与处理。
        具备基于规则的反思（Reflection）与多场景认知。
        """
        markdown_text = self.download_and_extract_md(mineru_result)
        context_text = self._build_context_pack(markdown_text, target_metrics, scenario)

        if scenario == "financial":
            direct_result = self._extract_financial_candidates(markdown_text, target_metrics)
            if direct_result:
                is_valid, reason = self._verify_results(direct_result, scenario, target_metrics)
                if is_valid:
                    logger.info("直接从 Markdown 行内提取到可用财务结果，跳过大模型。")
                    return direct_result
                logger.warning(f"直接提取结果未通过校验: {reason}。将交给大模型二次整理。")
        
        # 1. 根据赛题需求，动态切换大模型认知体系与提示词工程 (Prompt Engineering)
        if scenario == "financial":
            system_prompt = (
                "你是一个专业的金融审计 Data Agent。任务是从财报 Markdown 里提取核心指标，优先依据资产负债表、利润表、会计数据和财务指标摘要等关键章节。\n"
                "要求：1. 原样提取数字，不做四舍五入；2. 只使用给出的上下文，不要臆测；3. 跨页断裂或无法确认的数据标记为空；4. 严禁输出 markdown 代码块，严格 JSON 输出。"
            )
        elif scenario == "coreference_cross_page":
            system_prompt = (
                "你是一个精通逻辑编织与阅读理解的 Data Agent。你的任务是解决【跨页合并与全局指代消解】。\n"
                "解析后的 Markdown 中可能有由于分页被打断的长句子，以及'它'、'该公司'等代词。\n"
                "要求：1. 将分页割裂的指代拼接到主语上；2. 从文中准确抽取出目标指标内容，并输出最完整的上下文含义；3. 严格 JSON 输出。"
            )
        elif scenario == "low_quality_ocr":
            system_prompt = (
                "你是一台超强鲁棒性的纠错 Agent。用户提交的 PDF 由于光线不均/签章遮挡导致 OCR 输出的文本存在错别字、碎片化。\n"
                "任务：结合语境修复被遮盖的词汇，还原真实的关键信息，并以严格 JSON 格式输出。"
            )
        elif scenario == "industry_spec":
            system_prompt = (
                "你是一个专业的行业合规审查 Agent。请根据隐含的规范和指标名称审查以下文本是否合规。\n"
                "提取数据必须包含具体的数值及是否符合标准的判定描述，并以严格 JSON 格式输出。"
            )
        else:
            system_prompt = "请帮助用户从文本中以 JSON 格式提取下列关键信息。"
        
        user_prompt = (
            f"场景:{scenario}。请提取以下指标: {', '.join(target_metrics)}。\n"
            "请优先从以下关键章节中寻找对应数值：会计数据和财务指标摘要、合并资产负债表、母公司资产负债表、合并利润表、母公司利润表、财务报表附注。\n"
            "如果同一指标在多个位置出现，以年度报告正文财务报表中的最新、最完整口径为准。\n"
            f"解析内容如下:\n{context_text}"
        )
        
        max_retries = 2
        last_reason = ""
        for attempt in range(max_retries):
            logger.info(f"第 {attempt + 1} 次向 DeepSeek 发起 {scenario} 场景下提取请求...")
            extraction_result = self._call_deepseek(system_prompt, user_prompt, target_metrics)
            
            # 使用 Agent 内置的审计工具进行反思验证
            is_valid, reason = self._verify_results(extraction_result, scenario, target_metrics)
            if is_valid:
                logger.info("审计校验通过，数据无幻觉！")
                return extraction_result
            else:
                last_reason = reason
                logger.warning(f"数据校验未通过: {reason}。触发 Agent 思考与重试机制...")
                # 将错误原因喂给大模型，让它自我纠正（Reflection）
                user_prompt += f"\n\n【重要反馈】：你上一次提取的结果未能通过审计规则校验，原因是：{reason}。请重新仔细阅读相关表格，仔细核对数字，确保准确无误后再输出 JSON。"
                
        raise RuntimeError(f"达到最大重试次数，未能产出通过校验的结果: {last_reason}")

    def download_and_extract_md(self, result: dict) -> str:
        """
        从 MinerU 接口返回的结果中获取 Markdown。

        精准解析 API 通常返回 full_zip_url，Agent 轻量解析 API 通常返回
        markdown_url。这里同时兼容两种形态，方便评测端切换 MinerU 接口。
        """
        markdown_url = (
            result.get("markdown_url") or
            result.get("extract_result", {}).get("markdown_url")
        )
        if markdown_url:
            try:
                logger.info(f"正在下载 Markdown: {markdown_url}")
                res = requests.get(markdown_url, timeout=(15, 300))
                res.raise_for_status()
                return res.text
            except Exception as e:
                raise RuntimeError(f"下载 Markdown 失败: {e}") from e

        # 尝试从各类常见的返回字段中找下载链接
        download_url = (
            result.get("full_zip_url") or 
            result.get("download_url") or 
            result.get("extract_result", {}).get("full_zip_url") or
            result.get("extract_result", {}).get("download_url")
        )
            
        if not download_url:
            raise ValueError("MinerU 结果中未找到 full_zip_url、download_url 或 markdown_url，无法继续解析")

        try:
            logger.info(f"正在下载解析结果 ZIP: {download_url}")
            last_error = None
            for attempt in range(3):
                try:
                    res = requests.get(download_url, timeout=(15, 600))
                    res.raise_for_status()

                    with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                        # 寻找压缩包里所有的 .md 文件
                        md_files = [f for f in z.namelist() if f.endswith('.md')]
                        if not md_files:
                            raise ValueError("ZIP 包内未找到 Markdown 文件")

                        # 读取首个 Markdown 文件
                        with z.open(md_files[0]) as f:
                            return f.read().decode('utf-8', errors='ignore')
                except Exception as exc:
                    last_error = exc
                    logger.warning(f"第 {attempt + 1} 次下载或解压失败: {exc}")
            raise last_error if last_error else RuntimeError("下载或解压 Markdown 失败")
                    
        except Exception as e:
            raise RuntimeError(f"下载或解压 Markdown 失败: {e}") from e

    def _build_context_pack(self, markdown_text: str, target_metrics: list[str], scenario: str) -> str:
        lines = markdown_text.splitlines()
        keywords = set(target_metrics)

        if scenario == "financial":
            keywords.update({
                "会计数据和财务指标摘要",
                "合并资产负债表",
                "母公司资产负债表",
                "合并利润表",
                "母公司利润表",
                "财务报表及附注",
                "资产总计",
                "负债合计",
                "所有者权益合计",
                "所有者权益",
                "资产总额",
                "负债和所有者权益总计",
            })

        matched_line_indexes: list[int] = []
        for index, line in enumerate(lines):
            if any(keyword in line for keyword in keywords):
                start = max(0, index - 8)
                end = min(len(lines), index + 16)
                matched_line_indexes.extend(range(start, end))

        if not matched_line_indexes:
            return markdown_text[:18000]

        unique_indexes = sorted(set(matched_line_indexes))
        packed_lines: list[str] = []
        last_index = None

        for index in unique_indexes:
            if last_index is not None and index - last_index > 1:
                packed_lines.append("\n---\n")
            packed_lines.append(lines[index])
            last_index = index

        packed_text = "\n".join(packed_lines).strip()
        return packed_text[:18000]

    def _extract_financial_candidates(self, markdown_text: str, target_metrics: list[str]) -> dict:
        lines: list[str] = []
        for raw_line in markdown_text.splitlines():
            if "<tr" in raw_line and "</tr>" in raw_line:
                lines.extend(row for row in raw_line.split("</tr>") if row.strip())
            else:
                lines.append(raw_line)

        target_results: dict[str, str] = {}
        number_pattern = re.compile(r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
        metric_aliases = {
            "所有者权益合计": ["所有者权益合计", "股东权益合计"],
            "股东权益合计": ["股东权益合计", "所有者权益合计"],
        }

        def _aliases_for(metric: str) -> list[str]:
            return metric_aliases.get(metric, [metric])

        def _is_subtotal_row(line: str, metric: str) -> bool:
            subtotal_prefixes = {
                "资产总计": ("流动资产合计", "非流动资产合计"),
                "负债合计": ("流动负债合计", "非流动负债合计"),
                "所有者权益合计": ("归属于母公司",),
                "股东权益合计": ("归属于母公司",),
            }
            return any(prefix in line for prefix in subtotal_prefixes.get(metric, ()))

        def _pick_number_after_metric(line: str, metric: str) -> str | None:
            metric_index = line.find(metric)
            search_text = line[metric_index + len(metric):] if metric_index >= 0 else line
            candidates = number_pattern.findall(search_text.replace("，", ","))
            if not candidates:
                return None
            for candidate_index, candidate in enumerate(candidates):
                normalized = candidate.replace(",", "")
                if len(normalized) == 4 and normalized.isdigit() and normalized.startswith(("19", "20")):
                    continue
                if (
                    "<td" in line
                    and len(candidates) > candidate_index + 1
                    and normalized.lstrip("+-").isdigit()
                    and abs(int(normalized)) <= 300
                ):
                    continue
                return normalized
            return None

        for metric in target_metrics:
            matched_value = None
            for index, line in enumerate(lines):
                matched_alias = next((alias for alias in _aliases_for(metric) if alias in line), None)
                if not matched_alias or _is_subtotal_row(line, metric):
                    continue

                # 先尝试同一行中 metric 后面的数值
                matched_value = _pick_number_after_metric(line, matched_alias)
                if matched_value:
                    break

                # 再尝试向后几行找数值，兼容表格被拆行的情况
                for offset in range(1, 4):
                    if index + offset >= len(lines):
                        break
                    candidate = _pick_number_after_metric(lines[index + offset], matched_alias)
                    if candidate:
                        matched_value = candidate
                        break
                if matched_value:
                    break

            if matched_value is not None:
                target_results[metric] = matched_value

        if (
            "所有者权益合计" in target_metrics
            and "所有者权益合计" not in target_results
            and "资产总计" in target_results
            and "负债合计" in target_results
        ):
            asset_value = float(target_results["资产总计"])
            liability_value = float(target_results["负债合计"])
            equity_value = asset_value - liability_value
            if equity_value >= 0:
                target_results["所有者权益合计"] = f"{equity_value:.2f}".rstrip("0").rstrip(".")

        return target_results

    def _call_deepseek(self, system_prompt: str, user_prompt: str, target: list) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,  # 设为极低温度，防止大模型发生“幻觉”
            "response_format": {"type": "json_object"}
        }
        
        try:
            res = requests.post(self.llm_base_url, headers=headers, json=payload, timeout=120)
            res.raise_for_status()
            content = res.json()["choices"][0]["message"]["content"]
            
            # 清理可能的 markdown 代码块标记
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"DeepSeek 网络调用失败: {e}") from e
        except Exception as e:
            raise RuntimeError(f"解析 JSON 结果失败: {e}\n原内容: {content if 'content' in locals() else '未获取到'}") from e
        
    def _verify_results(self, data: dict, scenario: str, target_metrics: list[str] | None = None) -> tuple[bool, str]:
        """
        Agent的多场景审计模块（防幻觉计算节点）。
        """
        if not isinstance(data, dict):
            return False, "大模型未返回期望的 JSON 字典结构"

        if target_metrics:
            missing_requested = [metric for metric in target_metrics if metric not in data or data.get(metric) in (None, "null", "")]
            if missing_requested:
                return False, f"未返回这些请求指标: {', '.join(missing_requested)}"

        if scenario == "financial":
            # 我们之前写的财报校验逻辑
            def _clean_num(val):
                if val in (None, "null", "", "API_ERROR", "PARSE_ERROR"): return None
                match = re.search(r"[-+]?\d*\.\d+|\d+", str(val).replace(",", "").replace("，", ""))
                return float(match.group()) if match else None
                
            a, l, e = _clean_num(data.get("资产总计")), _clean_num(data.get("负债合计")), _clean_num(data.get("所有者权益合计"))
            if a is not None and l is not None and e is not None and abs(a - (l + e)) > 0.05:
                return False, f"资产总计({a}) 不等于 负债合计({l}) + 所有者权益合计({e})"
                
            missing = [k for k, v in data.items() if v in (None, "null", "")]
            if missing: return False, f"有缺失的指标没有被找到或解析错误: {', '.join(missing)}"
                
        elif scenario in ("low_quality_ocr", "coreference_cross_page", "industry_spec"):
            # 通用的兜底校验：不能存在缺失的字段
            missing = [k for k, v in data.items() if v in (None, "null", "")]
            if missing:
                return False, f"发现这些字段为空或无法理解: {', '.join(missing)}。请你在严重模糊的图片文字残片中，或者跨页连接处联系上下文重新推测其含义。"
                
        return True, "校验通过"
