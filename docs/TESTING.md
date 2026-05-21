# 测试矩阵与稳定性验证

本文件用于补齐赛题交付所需的测试覆盖说明，重点覆盖数据理解、复杂任务规划、稳定性与异常恢复。

## 测试矩阵

| 编号 | 场景 | 目标 | 方法 | 验收标准 |
| --- | --- | --- | --- | --- |
| T1 | 本地烟测 | 验证 API、任务落盘、状态流转 | `python tests/test_local_finance.py` | 返回 `local smoke test passed`，任务状态为 `success` |
| T1.5 | Agent 单元验证 | 验证 Markdown 下载兼容与财务校验 | `python tests/test_agent_unit.py` | 返回 `agent unit validation passed` |
| T2 | 真实 PDF 联调 | 验证 MinerU + DeepSeek 的真实链路 | `python scripts/run_real_pdf_test.py` | 能输出 `structured_result`，且财务字段完整 |
| T3 | 并发稳定性 | 验证多任务并发执行与锁保护 | `python tests/test_stability.py` | 8 个并发任务全部成功，无任务状态错乱 |
| T4 | 过期任务清理 | 验证持久化任务表清理逻辑 | `python tests/test_stability.py` | 过期任务被清理，`cleanup_task_db()` 返回大于 0 |
| T5 | 健康检查 | 验证探活接口 | `GET /health` | 返回 `status=healthy` 且包含 `task_count` |
| T6 | 失败路径 | 验证缺少环境变量和外部依赖失败时的可解释性 | 取消配置 `MINERU_API_TOKEN` 或 `DEEPSEEK_API_KEY` 后运行 | 返回明确错误信息，不静默吞错 |

## 稳定性验证

### 1. 持久化稳定性
- 任务状态写入本地 `task_db.json`，重启后可恢复查询。
- `startup_cleanup()` 会在启动时清理过期终态任务，避免垃圾记录长期堆积。

### 2. 并发稳定性
- `task_db_lock` 保护任务写入与更新，避免并发请求造成 JSON 文件损坏。
- `tests/test_stability.py` 会并发启动多个任务，验证不会出现状态覆盖、丢写或结果串号。

### 3. 外部依赖稳定性
- MinerU 下载结果时采用重试和长读超时，降低大 ZIP 下载失败率。
- DeepSeek 请求使用明确超时，避免长时间挂起。

### 4. 结果可靠性
- 财报场景会先进行直接抽取，再进行财务平衡校验。
- 如果缺少 `所有者权益合计`，会按资产负债表恒等式补齐，避免“部分字段成功、整体结果不可用”的假阳性。

## 推荐执行顺序

1. `python tests/test_local_finance.py`
2. `python tests/test_agent_unit.py`
3. `python tests/test_stability.py`
4. `python scripts/run_real_pdf_test.py`
5. 启动 `python -m data_agent.main` 后调用 `/health` 和 `/v1/agent/task_status/{job_id}` 做在线检查
