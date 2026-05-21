# 智能进化·Agent 能力评测赛道提交说明

## 1. 项目定位

本项目提交一个基于 MinerU + DeepSeek 的 Data Agent，主攻财务报表高密度数字抽取和防幻觉校验，同时提供跨页指代消解、低质量 OCR 修复和行业规范审查等扩展场景。

系统通过 FastAPI 暴露统一评测接口，支持文档 URL 提交、后台异步处理、任务状态轮询、结构化结果输出和健康检查。

## 2. 赛题要求对应关系

| 赛题要求 | 本项目实现 |
| --- | --- |
| 使用 MinerU 工具链 | `data_agent/mineru_client.py` 调用 MinerU SaaS 精准解析 API，`data_agent/agent.py` 兼容 `full_zip_url` 与 `markdown_url` |
| 数据理解与结构化处理 | MinerU 将 PDF/HTML 等解析为 Markdown，Agent 输出 JSON 指标结果 |
| 复杂任务规划与自动执行 | API 任务异步提交，内部执行 MinerU 解析、结果下载、上下文打包、规则抽取、LLM 提取、审计校验 |
| 系统稳定性 | `task_db.json` 持久化任务状态，`task_db_lock` 保护并发写入，支持过期任务清理 |
| API 评测接入 | `/v1/agent/process`、`/v1/agent/task_status/{job_id}`、`/health` |
| 可验证日志与结果 | `EXECUTION_LOGS.md`、`TESTING.md`、本地测试脚本和真实 PDF 联调脚本 |

## 3. 运行方式
建议python3.12
### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置密钥

复制 `.env.example` 为 `.env`，填写：

```bash
MINERU_API_TOKEN=你的 MinerU Token
DEEPSEEK_API_KEY=你的 DeepSeek API Key
```

### 启动服务

```bash
python -m data_agent.main
```

服务默认监听：

```text
http://127.0.0.1:8080
```

## 4. API 调用

### 提交任务

```bash
curl -X POST http://127.0.0.1:8080/v1/agent/process \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "财报核心指标抽取",
    "scenario": "financial",
    "file_url": "https://notice.10jqka.com.cn/api/pdf/e8639a5eb576c085.pdf",
    "page_ranges": "114-130",
    "target_metrics": ["营业收入", "资产总计", "负债合计", "所有者权益合计"]
  }'
```

### 查询任务

```bash
curl http://127.0.0.1:8080/v1/agent/task_status/{job_id}
```

### 健康检查

```bash
curl http://127.0.0.1:8080/health
```

## 5. 验证命令

提交前建议按以下顺序执行：

```bash
python tests/test_local_finance.py
python tests/test_agent_unit.py
python tests/test_stability.py
python scripts/run_real_pdf_test.py
```

其中前三项不依赖真实外部密钥，`scripts/run_real_pdf_test.py` 需要 MinerU 与 DeepSeek 密钥。

当前本地已验证：

```text
local smoke test passed
agent unit validation passed
stability validation passed | parallel_jobs=8 | removed_expired=1 | task_count=8
real pdf validation passed | page_ranges=114-130 | 营业收入=101450670 | 资产总计=150634906 | 负债合计=104512400 | 所有者权益合计=46122506
```

## 6. 文件清单

| 文件 | 说明 |
| --- | --- |
| `data_agent/main.py` | FastAPI 服务入口、异步任务和状态查询 |
| `data_agent/agent.py` | 多场景 Agent、上下文打包、财务规则抽取、LLM 调用和审计校验 |
| `data_agent/mineru_client.py` | MinerU SaaS 任务提交与轮询 |
| `data_agent/env_setup.py` | `.env` 自动加载 |
| `README.md` | 项目说明、启动方式和 API 示例 |
| `TECHNICAL_REPORT.md` | 技术报告 |
| `TESTING.md` | 测试矩阵与稳定性验证 |
| `EXECUTION_LOGS.md` | 运行日志与测试摘要 |
| `SUBMISSION_PACKAGE.md` | 提交材料清单 |
| `scripts/run_real_pdf_test.py` | 真实 PDF 联调脚本 |
| `tests/test_local_finance.py` | 本地烟测 |
| `tests/test_agent_unit.py` | Agent Markdown 兼容与财务校验单元测试 |
| `tests/test_stability.py` | 并发稳定性测试 |

