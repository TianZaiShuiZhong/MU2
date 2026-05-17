# 参赛要求对照检查表

| 参赛要求 | 对应材料 | 当前状态 |
| --- | --- | --- |
| 开放系统实现代码或关键模块代码，开源至 GitHub 并提交 repo 链接 | `main.py`、`agent.py`、`mineru_client.py`、测试脚本；待上传 GitHub 后填写 repo 链接 | 代码已准备，待创建/上传 GitHub 仓库 |
| 系统部署与运行说明文档 | `DEPLOYMENT_AND_API.md`、`README.md` | 已完成 |
| 系统架构说明 | `README.md`、`TECHNICAL_REPORT.md`、`DEPLOYMENT_AND_API.md` | 已完成 |
| 运行环境要求，包括操作系统、依赖库、硬件资源 | `DEPLOYMENT_AND_API.md` | 已完成 |
| 启动方式、测试方法及日志查看方式 | `DEPLOYMENT_AND_API.md`、`TESTING.md`、`EXECUTION_LOGS.md` | 已完成 |
| 互联网可访问服务接口信息或 API 接口说明 | `DEPLOYMENT_AND_API.md`、`api 文档.md` | 本地 API 已完成；如部署公网服务，补充公网地址即可 |
| 接口调用方式、参数说明、返回结果格式及认证方式 | `DEPLOYMENT_AND_API.md` | 已完成 |
| 完整技术报告 | `TECHNICAL_REPORT.md` | 已完成 |
| Data Agent 整体设计方案 | `TECHNICAL_REPORT.md` 第 2 节 | 已完成 |
| 任务执行机制 | `TECHNICAL_REPORT.md` 第 2.2 节 | 已完成 |
| 数据处理与工具调用能力 | `TECHNICAL_REPORT.md` 第 2.3 节 | 已完成 |
| 系统性能与稳定性说明 | `TECHNICAL_REPORT.md` 第 4 节 | 已完成 |
| 不少于 5 个典型任务执行示例 | `TECHNICAL_REPORT.md` 第 5 节 | 已完成，已有 5 个 |
| 系统适用场景与应用价值说明 | `TECHNICAL_REPORT.md` 第 6 节 | 已完成 |
| 系统运行日志与测试结果 | `EXECUTION_LOGS.md`、`TESTING.md` | 已完成 |
| 日志包含任务输入、执行步骤、调用工具信息、最终输出 | `EXECUTION_LOGS.md` | 已完成 |
| 其他加分材料 | `PPT_OUTLINE.md`；可进一步录制演示视频或制作正式 PPT | 已提供 PPT 提纲 |

## 待提交前填写项

- GitHub repo 链接：待填写。
- 如部署公网服务，服务地址：待填写。
- 队伍名称、成员信息：待填写。
- 如制作正式 PPT 或视频，可将文件链接补充到提交平台。

## 当前真实验证摘要

真实 PDF 联调命令：

```bash
python run_real_pdf_test.py
```

验证结果：

```text
营业收入=101450670
资产总计=150634906
负债合计=104512400
所有者权益合计=46122506
150634906 = 104512400 + 46122506
```
