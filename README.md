# 智能进化·Data Agent (基于 MinerU 与 DeepSeek)

> **所属赛道**：智能进化·Agent 能力评测赛道  
> **核心依托**：MinerU SaaS 工具链 + DeepSeek 深度推理  
> **解决痛点**：财务报表情景下的高密度数字防幻觉、跨页信息合并与指代消解、OCR 低质量鲁棒去噪恢复。

---

## 💡 项目简介

随着大模型技术的发展，如何确保数据处理系统在真实业务场景中（尤其是财报、复杂工程图纸、低质量扫描件等）保持“零幻觉”及高可用性，成为最迫切的问题。

本项目开发并提交了一个**具备自动化、跨场景处理与防幻觉能力的复合数据智能体 (Universal Data Agent)**。<br/>
该系统创新性地将 **MinerU 强大的版面结构转化能力** 与 **大语言模型（DeepSeek）的认知规划能力** 结合，通过自主编排的多轮试错与逻辑审计机制（Reflection），彻底解决了文档理解中“幻觉严重、多页串联失效、噪声冗余”的工业落地痛点。符合赛方关于 **数据理解结构化、复杂任务规划和输出可靠性** 的核心考验。

---

## 🛠️ 系统架构与核心创新点

本项目的处理管线分为四大层：

1. **感知与预处理层（使用 MinerU）**
   - 彻底摒弃传统直接读取文本带来的错行、漏字问题。利用 MinerU 的精准解析，将复杂 PDF/Word/图片等转化为富含层级和表格标签的结构化 Markdown。
2. **多场景路由认知大脑（LLM 提示工程）**
   - Agent 收到清洗好的数据后，可以根据用户下发的 `scenario`，自适应切换认知角色：
     - `financial`：**金融审计专员**（严格禁用大模型产生单位进位、四舍五入等幻觉特性，做到数字原封不动）。
     - `coreference_cross_page`：**逻辑缝合推导专员**（专注连接由于物理分页断裂的指代词）。
     - `low_quality_ocr`：**强鲁棒去噪专员**（联系上下文推翻零碎的错误识别汉字）。
3. **防幻觉与审计机制层（Agent Reflection）**
   - 提取并非一步到位。Agent 中置入了**数学公式验证组件 (Math Verification)**。
   - 当在 `financial` 模式中，如果抽取的《资产总计》不等于《负债 + 所有者权益》，或者指标出现空缺 (null)，**Agent 会立刻抛出异常拒绝输出，转而携错误原因再度追问大模型要求它进行第二轮更为严谨的仔细反思排查。** 确保极强的一致性与可落地能力。
4. **服务部署层（FastAPI 异步架构）**
   - 直接原生提供生产级的高并发异步 API，不仅防止了处理巨型财报导致的链接超时阻塞，更是完美符合了赛题要求的“**支持通过 API 接口随时随地提交至组委会进行能力评测**”。
   - 任务状态会落盘到本地 `task_db.json`，并提供 `/health` 便于评测端探活。

---

## 🚀 快速开始与部署说明

### 1. 环境准备
项目基于 Python 3.10+ 开发，首先请激活虚拟环境并安装核心依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
确保 `mineru_client.py` 及 `agent.py` 文件中，或环境变量中配置好您申请的密钥：
- **MinerU API Token**: 用于拉起远端 VLM 解析。
- **DeepSeek API Key**: 系统的大脑执行与分析模块。
   - 可选配置 `MINERU_API_BASE_URL` 覆盖 MinerU 接口地址。

更方便的方式是直接在项目根目录放一个 `.env` 文件，程序启动时会自动加载，不需要每次在命令行里手动设置。可参考仓库里的 [.env.example](.env.example) 复制一份后填写自己的密钥。

### 3. 启动 API 服务
在终端中运行以下命令：
```bash
python main.py
# 或使用 uvicorn 守护: uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```
API 服务将默认开启在 `http://0.0.0.0:8080` （支持 `http://127.0.0.1:8080/docs` 可视化调试接口面板）。

---

## 📖 API 调用与测试说明（供给组委会/评测框架）

### 0. 测试矩阵与稳定性验证

完整测试矩阵和稳定性验证说明见 [TESTING.md](TESTING.md)。当前项目建议至少覆盖以下三类验证：
- 本地烟测：`python test_local_finance.py`
- 并发稳定性：`python test_stability.py`
- 真实 PDF 联调：`python run_real_pdf_test.py`

其中 `test_stability.py` 会同时覆盖并发任务、过期任务清理和 `/health` 探活，适合作为提交前的稳定性回归检查。

### 0.1 提交材料总览

赛题要求对应的提交材料汇总见 [SUBMISSION_PACKAGE.md](SUBMISSION_PACKAGE.md)，逐项对照检查见 [SUBMISSION_REQUIREMENTS_CHECKLIST.md](SUBMISSION_REQUIREMENTS_CHECKLIST.md)。其中完整部署/API 说明见 [DEPLOYMENT_AND_API.md](DEPLOYMENT_AND_API.md)，技术报告见 [TECHNICAL_REPORT.md](TECHNICAL_REPORT.md)，运行日志与测试结果见 [EXECUTION_LOGS.md](EXECUTION_LOGS.md)。
评审快速入口见 [FINAL_SUBMISSION.md](FINAL_SUBMISSION.md)，该文件集中说明赛题要求、项目实现、运行方式、API 调用和验证命令。

### 1. 提交解析任务 (异步提交)
向 `/v1/agent/process` 提交 JSON 请求。此时会立即返回一个 `job_id` 供下一步轮询。

**请求示例**：
```bash
curl -X POST http://127.0.0.1:8080/v1/agent/process \
  -H "Content-Type: application/json" \
  -d '{
      "task_name": "A股年度财报提取（防幻觉测试）",
      "scenario": "financial",
      "file_url": "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
      "page_ranges": "114-130",
      "target_metrics": ["营业收入", "资产总计", "负债合计", "所有者权益合计"]
  }'
```

**支持的 `scenario` 枚举：**
- `financial`: 财报强对齐防幻觉 (默认值)
- `coreference_cross_page`: 跨页合并与指代消解
- `low_quality_ocr`: 模糊去噪
- `industry_spec`: 标准规章判定

可选字段 `page_ranges` 会透传给 MinerU 标准解析 API，用于限制解析页码范围，例如 `"114-130"`。这适合年报等超过 200 页的大文档，也能降低联调成本和等待时间。

### 2. 轮询提取进度与防幻觉结果
Agent 处理多页文档以及自我反思校验往往需要数十秒到几分钟，通过刚获取的 `job_id` 定期 `GET` 拉取最终结果。

**查询示例**：
```bash
curl -X GET http://127.0.0.1:8080/v1/agent/task_status/{job_id}
```
**返回值特征**：
状态字段 (`status`) 从 `queued` 转化为 `parsing_document`，再到 `agent_processing`，最后完成为 `success`，并在 `result` 中获得无污染对齐的 JSON 抽取数据。
遇到无法自洽的数据断裂且超过重试次数时，为了严谨性将返回友好的 `error_msg`，以避免强行造假。

### 3. 健康检查

```bash
curl -X GET http://127.0.0.1:8080/health
```

该接口返回服务存活状态以及当前任务数量，适合评测平台做探活与基础连通性检查。

---

## 📋 文件目录结构

```text
📁 Project Root
 ├── main.py                // 接口定义、路由核心与 FastAPI 异步生命周期逻辑
 ├── agent.py               // 多场景切换大脑、防幻觉审计与 DeepSeek LLM 提取算法实现
 ├── mineru_client.py       // 极简包装的 MinerU SaaS 云直连工具包
 ├── requirements.txt       // 项目依赖项
 └── README.md              // 部署与产品使用文档
```

**致谢**：感谢 MinerU 开源社区与 OpenXLab 提供的基石版面解析支持体系，让 Data Agent 的底层“长了眼睛”。
