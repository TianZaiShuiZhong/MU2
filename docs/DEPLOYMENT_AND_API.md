# 系统部署、运行与 API 说明

## 1. 运行环境要求

### 操作系统

- 推荐：Linux、Windows 或 macOS 均可运行。
- 当前验证环境：Windows + Python 虚拟环境。

### Python 与依赖

- Python：3.10 及以上。
- 依赖库：见 `requirements.txt`。

安装命令：

```bash
pip install -r requirements.txt
```

### 硬件资源

本项目核心解析能力依赖 MinerU SaaS 与 DeepSeek API，本地服务主要负责 API 编排、任务状态管理和结果校验，因此本地硬件要求较低：

- CPU：2 核及以上。
- 内存：建议 4 GB 及以上。
- 磁盘：建议预留 1 GB 以上，用于日志、任务状态和临时文件。
- GPU：非必需。

### 外部服务

需要准备以下密钥并写入 `.env`：

```bash
MINERU_API_TOKEN=your_mineru_api_token_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

可选：

```bash
MINERU_API_BASE_URL=https://mineru.net/api/v4/extract/task
```

## 2. 启动方式

### 本地启动

```bash
python -m data_agent.main
```

或：

```bash
uvicorn data_agent.main:app --host 0.0.0.0 --port 8080
```

默认服务地址：

```text
http://127.0.0.1:8080
```

FastAPI 调试文档：

```text
http://127.0.0.1:8080/docs
```

## 3. API 接口说明

### 3.1 健康检查

```http
GET /health
```

返回示例：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "status": "healthy",
    "task_count": 0
  }
}
```

### 3.2 提交处理任务

```http
POST /v1/agent/process
```

请求体：

```json
{
  "task_name": "财报核心指标抽取",
  "scenario": "financial",
  "file_url": "https://notice.10jqka.com.cn/api/pdf/e8639a5eb576c085.pdf",
  "page_ranges": "114-130",
  "target_metrics": ["营业收入", "资产总计", "负债合计", "所有者权益合计"]
}
```

参数说明：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `task_name` | string | 是 | 任务名称 |
| `file_url` | string | 是 | 待解析文件 URL |
| `target_metrics` | array | 是 | 需要抽取的字段列表 |
| `scenario` | string | 否 | 场景，默认 `financial` |
| `is_html` | boolean | 否 | 是否按 HTML 文件处理 |
| `page_ranges` | string | 否 | MinerU 页码范围，如 `114-130` |

支持场景：

| 场景 | 说明 |
| --- | --- |
| `financial` | 财报核心指标抽取与防幻觉校验 |
| `coreference_cross_page` | 跨页合并与指代消解 |
| `low_quality_ocr` | 低质量 OCR 文本修复 |
| `industry_spec` | 行业规范和合规条款判定 |

返回示例：

```json
{
  "code": 0,
  "msg": "ok",
  "job_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### 3.3 查询任务状态

```http
GET /v1/agent/task_status/{job_id}
```

成功返回示例：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "status": "success",
    "created_at": "2026-05-17T00:00:00+00:00",
    "updated_at": "2026-05-17T00:05:00+00:00",
    "result": {
      "营业收入": 101450670,
      "资产总计": 150634906,
      "负债合计": 104512400,
      "所有者权益合计": 46122506
    }
  }
}
```

失败返回示例：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "status": "failed",
    "error_msg": "达到最大重试次数，未能产出通过校验的结果"
  }
}
```

## 4. 认证方式

本项目对组委会暴露的本地 API 默认不启用额外认证，便于评测系统直接调用。

外部服务认证通过服务端环境变量完成：

- `MINERU_API_TOKEN`：用于调用 MinerU SaaS。
- `DEEPSEEK_API_KEY`：用于调用 DeepSeek。

`.env` 已被 `.gitignore` 忽略，不应提交到公开仓库。

## 5. 测试方法

### 本地烟测

```bash
python tests/test_local_finance.py
```

期望输出：

```text
local smoke test passed
```

### Agent 单元验证

```bash
python tests/test_agent_unit.py
```

期望输出：

```text
agent unit validation passed
```

### 并发稳定性验证

```bash
python tests/test_stability.py
```

期望输出：

```text
stability validation passed | parallel_jobs=8 | removed_expired=1 | task_count=8
```

### 真实 PDF 联调

```bash
python scripts/run_real_pdf_test.py
```

期望结果：

```text
structured_result={
  "营业收入": 101450670,
  "资产总计": 150634906,
  "负债合计": 104512400,
  "所有者权益合计": 46122506
}
```

## 6. 日志与结果查看

### 控制台日志

服务运行时会输出关键步骤：

- MinerU 任务提交。
- MinerU 任务轮询。
- ZIP 或 Markdown 下载。
- Agent 抽取。
- 校验结果。
- 失败原因。

### 任务状态文件

任务状态会写入：

```text
task_db.json
```

该文件包含任务状态、创建时间、更新时间、最终结果或错误信息。它属于运行时文件，已被 `.gitignore` 忽略。

### 结果记录文档

测试结果和真实联调摘要见：

- `EXECUTION_LOGS.md`
- `TESTING.md`
- `TECHNICAL_REPORT.md`

## 7. 复现流程

1. 克隆 GitHub 仓库。
2. 安装依赖：`pip install -r requirements.txt`。
3. 创建 `.env` 并填写 MinerU 与 DeepSeek 密钥。
4. 启动服务：`python -m data_agent.main`。
5. 调用 `/health` 确认服务正常。
6. 调用 `/v1/agent/process` 提交任务。
7. 调用 `/v1/agent/task_status/{job_id}` 查询结果。
8. 运行 `python scripts/run_real_pdf_test.py` 复现实测结果。
