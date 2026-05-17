# 参赛提交内容清单

本文件将赛题要求映射到本项目当前可提交的材料，方便打包与提交。

## 1. 代码提交

- GitHub 仓库：当前项目仓库
- 主要代码：
  - [main.py](main.py)
  - [agent.py](agent.py)
  - [mineru_client.py](mineru_client.py)
  - [test_local_finance.py](test_local_finance.py)
  - [test_agent_unit.py](test_agent_unit.py)
  - [test_stability.py](test_stability.py)
  - [run_real_pdf_test.py](run_real_pdf_test.py)

## 2. 系统部署与运行说明

- 主说明文档：[README.md](README.md)
- 完整部署/API 文档：[DEPLOYMENT_AND_API.md](DEPLOYMENT_AND_API.md)
- MinerU 使用说明：[使用 MinerU.md](使用%20MinerU.md)
- API 说明：[api 文档.md](api%20文档.md)
- 需要提交时可直接引用 README 中的启动、接口与测试章节。

## 3. 技术报告

- 技术报告文件：[TECHNICAL_REPORT.md](TECHNICAL_REPORT.md)
- 覆盖内容：设计方案、任务执行机制、工具调用能力、性能与稳定性、典型任务示例、适用场景与应用价值。
- 最终提交说明：[FINAL_SUBMISSION.md](FINAL_SUBMISSION.md)，用于评审快速了解赛题要求与本项目实现的对应关系。
- 参赛要求对照检查：[SUBMISSION_REQUIREMENTS_CHECKLIST.md](SUBMISSION_REQUIREMENTS_CHECKLIST.md)

## 4. 测试矩阵与稳定性验证

- 测试矩阵文件：[TESTING.md](TESTING.md)
- 运行日志与测试结果：[EXECUTION_LOGS.md](EXECUTION_LOGS.md)
- 建议提交前至少完成：
  - 本地烟测
  - Agent 单元验证
  - 真实 PDF 联调
  - 并发稳定性验证
  - 健康检查验证

## 5. 其他材料

可选加分项：
- 演示 PPT 提纲：[PPT_OUTLINE.md](PPT_OUTLINE.md)
- 技术方案文档
- 演示视频
- 典型任务截图

## 6. 建议的打包顺序

1. 仓库代码
2. README 与 API 文档
3. 技术报告
4. 测试矩阵与日志
5. 演示类附件

## 7. 提交前核对项

- 代码可运行
- 依赖可安装
- 环境变量已说明
- API 入口可访问
- 测试脚本已通过
- 真实样本结果可复现
- `.env`、`task_db.json`、`venv/` 等本地文件不会被提交
- README、技术报告、测试矩阵、运行日志和最终提交说明均已包含
