# 使用 MinerU

## 快速配置模型源

MinerU默认使用`huggingface`作为模型源，若用户网络无法访问`huggingface`，可以通过环境变量便捷地切换模型源为`modelscope`：

```
export MINERU_MODEL_SOURCE=modelscope
```

有关模型源配置和自定义本地模型路径的更多信息，请参考文档中的[模型源说明](https://opendatalab.github.io/MinerU/zh/usage/model_source/)。

## 通过命令行快速使用

MinerU内置了命令行工具，用户可以通过命令行快速使用MinerU进行文档解析：

```
mineru -p <input_path> -o <output_path>
```

Tip

- `<input_path>`：本地 `PDF` / 图片 / `DOCX` / `PPTX` / `XLSX` 文件或目录
- `<output_path>`：输出目录
- 未传 `--api-url` 时，CLI 会自动拉起本地临时 `mineru-api`
- 传入 `--api-url` 时，CLI 会直连远端或已有本地 FastAPI 服务

更多关于输出文件的信息，请参考[输出文件说明](https://opendatalab.github.io/MinerU/zh/reference/output_files/)。

Note

命令行工具会在Linux和macOS系统自动尝试cuda/mps加速。Windows用户如需使用cuda加速， 请前往 [Pytorch官网](https://pytorch.org/get-started/locally/) 选择适合自己cuda版本的命令安装支持加速的`torch`和`torchvision`。

如果需要通过自定义参数调整解析选项，您也可以在文档中查看更详细的[命令行工具使用说明](https://opendatalab.github.io/MinerU/zh/usage/cli_tools/)。

## 通过api、webui、http-client/server进阶使用

- 通过fast api方式调用：

  ```
  mineru-api --host 0.0.0.0 --port 8000
  ```

  Tip

  在浏览器中访问 `http://127.0.0.1:8000/docs` 查看API文档。

  - 健康检查接口：`GET /health` 返回 `protocol_version`、`processing_window_size`、`max_concurrent_requests` 等服务信息
  - 异步任务提交接口：`POST /tasks`
  - 同步解析接口：`POST /file_parse`
  - 任务查询接口：`GET /tasks/{task_id}`、`GET /tasks/{task_id}/result`
  - API 输出目录由服务端固定控制，默认写入 `./output`
  - 上传文件当前支持 `PDF`、图片与 `DOCX`、`PPTX`、`XLSX`
  - `POST /tasks` 会立即返回 `task_id`；`POST /file_parse` 会在内部提交到同一个任务管理器，等待任务完成后同步返回最终结果。
  - 当任务处于排队状态时，任务提交结果和状态查询结果中可能会返回 `queued_ahead` 字段，用于表示前方排队任务数。
  - 任务为单进程、进程内状态实现，服务重启、`--reload` 热重载或多进程部署后不保证仍可查询历史任务状态。
  - 默认任务完成或失败后保留 24 小时，随后自动清理任务状态和输出目录；清理后访问任务状态或结果会返回 `404`。
  - 可通过环境变量 `MINERU_API_TASK_RETENTION_SECONDS` 和 `MINERU_API_TASK_CLEANUP_INTERVAL_SECONDS` 调整保留时长与清理轮询间隔。
  - 可通过 `--enable-vlm-preload true` 在服务启动阶段预热本地 VLM 模型，避免首次 VLM 或 hybrid 请求时再初始化。

  异步任务提交示例：

  ```
  curl -X POST http://127.0.0.1:8000/tasks \
    -F "files=@demo/pdfs/demo1.pdf" \
    -F "return_md=true"
  ```

  同步解析示例：

  ```
  curl -X POST http://127.0.0.1:8000/file_parse \
    -F "files=@demo/pdfs/demo1.pdf" \
    -F "return_md=true" \
    -F "response_format_zip=true" \
    -F "return_original_file=true"
  ```

  轮询任务状态与结果：

  ```
  curl http://127.0.0.1:8000/tasks/<task_id>
  curl http://127.0.0.1:8000/tasks/<task_id>/result
  curl http://127.0.0.1:8000/health
  ```

  http异步调用代码示例：[Python版本](https://github.com/opendatalab/MinerU/blob/master/demo/demo.py)

- 启动gradio webui 可视化前端：

  ```
  mineru-gradio --server-name 0.0.0.0 --server-port 7860
  ```

  Tip

  - 在浏览器中访问 `http://127.0.0.1:7860` 使用 Gradio WebUI。
  - 未传 `--api-url` 时，Gradio 会自动拉起可复用的本地 `mineru-api`；传入 `--api-url` 时则会复用已有本地或远端服务。
  - `--enable-vlm-preload true` 会让 Gradio 在 WebUI 启动阶段主动拉起本地 `mineru-api` 并等待 VLM 预加载完成；传入 `--api-url` 时会被忽略。
  - WebUI 当前支持上传 `PDF`、图片与 `DOCX`、`PPTX`、`XLSX` 文件。

- 通过 `mineru-router` 进行多服务 / 多 GPU 编排：

  ```
  mineru-router --host 0.0.0.0 --port 8002 --local-gpus auto
  ```

  Tip

  - `mineru-router` 对外暴露与 `mineru-api` 一致的 `/health`、`/tasks`、`/file_parse`、`/tasks/{task_id}`、`/tasks/{task_id}/result` 接口。
  - 可重复使用 `--upstream-url` 聚合多个已有 `mineru-api` 服务，也可通过 `--local-gpus` 自动拉起本地 worker。
  - `--enable-vlm-preload true` 仅作用于 router 托管的本地 worker，不会影响通过 `--upstream-url` 接入的远端服务。
  - 适用于多服务、多 GPU 和统一入口部署场景。

- 使用`http-client/server`方式调用：

  ```
  # 启动openai兼容服务器(需要安装vllm或lmdeploy环境)
  mineru-openai-server --port 30000
  ```

  Tip

  在另一个终端中通过http client连接openai server

  ```
  mineru -p <input_path> -o <output_path> -b hybrid-http-client -u http://127.0.0.1:30000
  ```

  `vlm-http-client` 是轻量远程 client，用法上不要求本地安装 `torch`。 `hybrid-http-client` 需要本地具备 `mineru[pipeline]` 及 `torch` 等 pipeline 依赖。

Note

所有`vllm/lmdeploy`官方支持的参数都可用通过命令行参数传递给 MinerU，包括以下命令:`mineru`、`mineru-openai-server`、`mineru-gradio`、`mineru-api`、`mineru-router`， 我们整理了一些`vllm/lmdeploy`使用中的常用参数和使用方法，可以在文档[命令行进阶参数](https://opendatalab.github.io/MinerU/zh/usage/advanced_cli_parameters/)中获取。

## 基于配置文件扩展 MinerU 功能

MinerU 现已实现开箱即用，但也支持通过配置文件扩展功能。您可通过编辑用户目录下的 `mineru.json` 文件，添加自定义配置。

Important

`mineru.json` 文件会在您使用内置模型下载命令 `mineru-models-download` 时自动生成，也可以通过将[配置模板文件](https://github.com/opendatalab/MinerU/blob/master/mineru.template.json)复制到用户目录下并重命名为 `mineru.json` 来创建。

以下是一些可用的配置选项：

- `latex-delimiter-config`：

  - 用于配置 LaTeX 公式的分隔符
  - 默认为`$`符号，可根据需要修改为其他符号或字符串。

- `llm-aided-config`：

  - 用于配置 LLM 辅助标题分级的相关参数，兼容所有支持`openai协议`的 LLM 模型

  - 默认使用`阿里云百炼`的`qwen3-next-80b-a3b-instruct`模型

  - 您需要自行配置 API 密钥并将`enable`设置为`true`来启用此功能

  - 如果您的api供应商不支持`enable_thinking`参数，请手动将该参数删除

    - 例如，在您的配置文件中，`llm-aided-config` 部分可能如下所示：

      ```
      "llm-aided-config": {
         "api_key": "your_api_key",
         "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
         "model": "qwen3-next-80b-a3b-instruct",
         "enable_thinking": false,
         "enable": false
      }
      ```

    - 要移除`enable_thinking`参数，只需删除包含`"enable_thinking": false`的那一行，结果如下:

      ```
      "llm-aided-config": {
         "api_key": "your_api_key",
         "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
         "model": "qwen3-next-80b-a3b-instruct",
         "enable": false
      }
      ```

- `models-dir`：

  - 用于指定本地模型存储目录，请为`pipeline`和`vlm`后端分别指定模型目录，
  - 指定目录后您可通过配置环境变量`export MINERU_MODEL_SOURCE=local`来使用本地模型。



# 模型源说明

MinerU使用 `HuggingFace` 和 `ModelScope` 作为模型仓库，用户可以根据需要切换模型源或使用本地模型。

- `HuggingFace` 是默认的模型源，在全球范围内提供了优异的加载速度和极高稳定性。
- `ModelScope` 是中国大陆地区用户的最佳选择，提供了无缝兼容的SDK模块，适用于无法访问`HuggingFace`的用户。

## 模型源的切换方法

### 通过环境变量切换

MinerU 通过 `MINERU_MODEL_SOURCE` 环境变量配置模型源，这适用于所有命令行工具和 API 调用。

```
export MINERU_MODEL_SOURCE=modelscope
mineru -p <input_path> -o <output_path>
```

或在代码中设置：

```
import os
os.environ["MINERU_MODEL_SOURCE"] = "modelscope"
```

Tip

MinerU 已不再提供用于切换模型源的命令行参数。通过环境变量设置的模型源会在当前终端会话中生效，直到终端关闭或环境变量被修改。

## 使用本地模型

### 1. 下载模型到本地



```
mineru-models-download --help
```

或使用交互式命令行工具选择模型下载：

```
mineru-models-download
```

Note

- 下载完成后，模型路径会在当前终端窗口输出，并自动写入用户目录下的 `mineru.json`。
- 您也可以通过将[配置模板文件](https://github.com/opendatalab/MinerU/blob/master/mineru.template.json)复制到用户目录下并重命名为 `mineru.json` 来创建配置文件。
- 模型下载到本地后，您可以自由移动模型文件夹到其他位置，同时需要在 `mineru.json` 中更新模型路径。
- 如您将模型文件夹部署到其他服务器上，请确保将 `mineru.json`文件一同移动到新设备的用户目录中并正确配置模型路径。
- 如您需要更新模型文件，可以再次运行 `mineru-models-download` 命令，模型更新暂不支持自定义路径，如您没有移动本地模型文件夹，模型文件会增量更新；如您移动了模型文件夹，模型文件会重新下载到默认位置并更新`mineru.json`。
- `mineru-models-download` 必须使用远端模型源执行真实下载；如果当前终端已设置 `MINERU_MODEL_SOURCE=local`，该命令会仅在本次执行中临时忽略该值，并改用您选择的 `huggingface` 或 `modelscope` 下载模型。

### 2. 使用本地模型进行解析

通过环境变量启用本地模型：

```
export MINERU_MODEL_SOURCE=local
mineru -p <input_path> -o <output_path>
```

# 命令行工具使用说明

## 查看帮助信息

要查看 MinerU 命令行工具的帮助信息，可以使用 `--help` 参数。以下是各个命令行工具的帮助信息示例：

```
mineru --help
Usage: mineru [OPTIONS]

Options:
  -v, --version                   显示版本并退出
  -p, --path PATH                 输入文件路径或目录（必填）
  -o, --output PATH               输出目录（必填）
  --api-url TEXT                  MinerU FastAPI 服务地址；不传时自动拉起本地临时 mineru-api
  -m, --method [auto|txt|ocr]     解析方法：auto（默认）、txt、ocr（仅用于 pipeline 与 hybrid* 后端）
  -b, --backend [pipeline|hybrid-auto-engine|hybrid-http-client|vlm-auto-engine|vlm-http-client]
                                  解析后端（默认为 hybrid-auto-engine）
  -l, --lang [ch|ch_server|ch_lite|en|korean|japan|chinese_cht|ta|te|ka|th|el|latin|arabic|east_slavic|cyrillic|devanagari]
                                  指定文档语言（可提升 OCR 准确率，仅用于 pipeline 与 hybrid* 后端）
  -u, --url TEXT                  当使用 http-client 时，传给服务端后端的 OpenAI 兼容地址
  -s, --start INTEGER             开始解析的页码（从 0 开始）
  -e, --end INTEGER               结束解析的页码（从 0 开始）
  -f, --formula BOOLEAN           是否启用公式解析（默认开启）
  -t, --table BOOLEAN             是否启用表格解析（默认开启）
  --help                          显示帮助信息
```

Tip

`mineru` 当前支持本地 `PDF`、图片与 `DOCX`、`PPTX`、`XLSX` 文件或目录输入。



```
mineru-api --help
Usage: mineru-api [OPTIONS]

Options:
  --host TEXT     服务器主机地址（默认：127.0.0.1）
  --port INTEGER  服务器端口（默认：8000）
  --reload        启用自动重载（开发模式）
  --enable-vlm-preload BOOLEAN
                  在 mineru-api 启动阶段预加载本地 VLM 模型
  --help          显示此帮助信息并退出
mineru-gradio --help
Usage: mineru-gradio [OPTIONS]

Options:
  --enable-example BOOLEAN        启用示例文件输入(需要将示例文件放置在当前
                                  执行命令目录下的 `example` 文件夹中)
  --enable-http-client BOOLEAN    在后端选项中启用 HTTP 客户端选项
  --enable-api BOOLEAN            启用 Gradio API 以提供应用程序服务
  --max-convert-pages INTEGER     设置从 PDF 转换为 Markdown 的最大页数
  --server-name TEXT              设置 Gradio 应用程序的服务器主机名
  --server-port INTEGER           设置 Gradio 应用程序的服务器端口
  --api-url TEXT                  MinerU FastAPI 服务地址；不传时自动拉起可复用的本地
                                  mineru-api
  --enable-vlm-preload BOOLEAN    在 Gradio 拉起本地 mineru-api 时预加载本地
                                  VLM 模型
  --latex-delimiters-type [a|b|all]
                                  设置在 Markdown 渲染中使用的 LaTeX 分隔符类型
                                  ('a' 表示 '$' 类型，'b' 表示 '()[]' 类型，
                                  'all' 表示两种类型都使用)
  --help                          显示此帮助信息并退出
mineru-router --help
Usage: mineru-router [OPTIONS]

Options:
  --host TEXT             路由服务主机地址（默认：127.0.0.1）
  --port INTEGER          路由服务端口（默认：8002）
  --reload                启用自动重载（开发模式）
  --upstream-url TEXT     现有 MinerU FastAPI 服务地址；可重复传入多个
  --local-gpus TEXT       本地 GPU worker 配置：auto、none 或 0,1,2 形式
  --worker-host TEXT      路由托管 worker 的监听地址（默认：127.0.0.1）
  --enable-vlm-preload BOOLEAN
                          在 router 托管的本地 mineru-api worker 中预加载本地
                          VLM 模型
  --help                  显示此帮助信息并退出
```

## 环境变量说明

Note

从当前版本开始，`mineru` 是基于 `mineru-api` 的编排客户端：

- 未传 `--api-url` 时，CLI 会自动拉起本地临时 `mineru-api`
- 传入 `--api-url` 时，CLI 会直连该 FastAPI 服务
- `--url` 不再表示 MinerU API 地址，而是服务端 `vlm/hybrid-http-client` 所需的 OpenAI 兼容地址

MinerU命令行工具的某些参数存在相同功能的环境变量配置，通常环境变量配置的优先级高于命令行参数，且在所有命令行工具中都生效。 以下是常用的环境变量及其说明：

- `MINERU_TOOLS_CONFIG_JSON`：

  - 用于指定配置文件路径
  - 默认为用户目录下的`mineru.json`，可通过环境变量指定其他配置文件路径。

- `MINERU_FORMULA_ENABLE`：

  - 用于启用公式解析
  - 默认为`true`，可通过环境变量设置为`false`来禁用公式解析。

- `MINERU_FORMULA_CH_SUPPORT`：

  - 用于启用中文公式解析优化（实验性功能）
  - 默认为`false`，可通过环境变量设置为`true`来启用中文公式解析优化。
  - 仅对`pipeline`后端生效。

- `MINERU_TABLE_ENABLE`：

  - 用于启用表格解析
  - 默认为`true`，可通过环境变量设置为`false`来禁用表格解析。

- `MINERU_TABLE_MERGE_ENABLE`：

  - 用于启用表格合并功能
  - 默认为`true`，可通过环境变量设置为`false`来禁用表格合并功能。

- `MINERU_PDF_RENDER_TIMEOUT`：

  - 用于设置将PDF渲染为图片的超时时间（秒）
  - 默认为`300`秒，可通过环境变量设置为其他值以调整渲染图片的超时时间。
  - 在 Linux、macOS 和 Windows 系统中生效。

- `MINERU_PDF_RENDER_THREADS`：

  - 用于设置将PDF渲染为图片时使用的渲染 worker 并发数
  - 默认为`4`，可通过环境变量设置为其他值以调整渲染 worker 并发数。
  - 在 Linux、macOS 和 Windows 系统中生效。

- `MINERU_PROCESSING_WINDOW_SIZE`：

  - 用于设置单次处理窗口大小，影响大文档处理时的内存占用和吞吐表现
  - 默认为`64`，可通过环境变量设置为其他正整数。

- `MINERU_API_MAX_CONCURRENT_REQUESTS`：

  - 用于设置 `mineru-api` 或 `mineru-router` 管理的 worker 最大并发请求数
  - 默认为`3`，需设置为正整数。

- `MINERU_API_ENABLE_FASTAPI_DOCS`：

  - 用于控制是否启用 FastAPI 自动生成的 `/docs`、`/openapi.json`、`/redoc`
  - 默认为`true`。

- `MINERU_API_OUTPUT_ROOT`：

  - 用于指定 `mineru-api` 输出目录根路径
  - 默认为当前工作目录下的 `./output`。

- `MINERU_LOCAL_API_STARTUP_TIMEOUT_SECONDS`：

  - 用于控制各命令行工具等待本地拉起的 `mineru-api` 进入健康状态的最长时间
  - 默认为 `300` 秒。
  - 适用于 `mineru` 的临时本地 API、`mineru-gradio` 的 preload 启动，以及 `mineru-router` 托管的本地 worker。

- `MINERU_API_TASK_RETENTION_SECONDS`：

  - 用于设置任务完成或失败后的保留时长（秒）
  - 默认为 `86400` 秒（24 小时）。

- `MINERU_API_TASK_CLEANUP_INTERVAL_SECONDS`：

  - 用于设置任务清理轮询间隔（秒）
  - 默认为 `300` 秒（5 分钟）。

- `MINERU_INTRA_OP_NUM_THREADS`：

  - 用于设置onnx模型的intra_op线程数，影响单个算子的计算速度
  - 默认为`-1`（自动选择），可通过环境变量设置为其他值以调整线程数。

- `MINERU_INTER_OP_NUM_THREADS`：

  - 用于设置onnx模型的inter_op线程数，影响多个算子的并行执行
  - 默认为`-1`（自动选择），可通过环境变量设置为其他值以调整线程数。

- `MINERU_HYBRID_BATCH_RATIO`：

  - 用于设置 hybrid-* 后端中 小模型处理的batch倍率

  - 在hybrid-http-client中较为常用，可以通过控制小模型的batch倍率来调整单个客户端的显存占用量

  - | 单个client端显存大小 | MINERU_HYBRID_BATCH_RATIO |
    | :------------------- | :------------------------ |
    | <= 6 GB              | 8                         |
    | <= 4 GB              | 4                         |
    | <= 3 GB              | 2                         |
    | <= 2 GB              | 1                         |

- `MINERU_HYBRID_FORCE_PIPELINE_ENABLE`：

  - 用于强制将 hybrid-* 后端中的 文本提取部分使用 小模型 进行处理
  - 默认为`false`，可通过环境变量设置为`true`来启用该功能，从而在某些极端情况下减少幻觉的发生。

- `MINERU_VL_MODEL_NAME`：

  - 用于指定 vlm/hybrid 后端使用的模型名称，这将允许您在同时存在多个模型的远程openai-server中指定 MinerU 运行所需的模型。

- `MINERU_VL_API_KEY`:

  - 用于指定 vlm/hybrid 后端使用的API Key，这将允许您在远程openai-server中进行身份验证。

# 命令行参数进阶

## 推理引擎参数透传

### 参数传递说明

Tip

- 所有vllm/lmdeploy官方支持的参数都可用通过命令行参数传递给 MinerU，包括以下命令:`mineru`、`mineru-openai-server`、`mineru-gradio`、`mineru-api`、`mineru-router`
- 命令行参数同时支持 `--foo value` 与 `--foo=value` 两种写法
- 如果您想了解更多有关`vllm`的参数使用方法，请参考 [vllm官方文档](https://docs.vllm.ai/en/latest/cli/serve.html)
- 如果您想了解更多有关`lmdeploy`的参数使用方法，请参考 [lmdeploy官方文档](https://lmdeploy.readthedocs.io/en/latest/llm/api_server.html)

## GPU 设备选择与配置

### CUDA_VISIBLE_DEVICES 基本用法

Tip

- 任何情况下，您都可以通过在命令行的开头添加`CUDA_VISIBLE_DEVICES` 环境变量来指定可见的 GPU 设备：

  ```
  CUDA_VISIBLE_DEVICES=1 mineru -p <input_path> -o <output_path>
  ```

- 这种指定方式对所有的命令行调用都有效，包括 `mineru`、`mineru-openai-server`、`mineru-gradio`、`mineru-api`和`mineru-router`，且对`pipeline`、`vlm`后端均适用。

### 常见设备配置示例

Tip

以下是一些常见的 `CUDA_VISIBLE_DEVICES` 设置示例：

```
CUDA_VISIBLE_DEVICES=1  # Only device 1 will be seen
CUDA_VISIBLE_DEVICES=0,1  # Devices 0 and 1 will be visible
CUDA_VISIBLE_DEVICES="0,1"  # Same as above, quotation marks are optional
CUDA_VISIBLE_DEVICES=0,2,3  # Devices 0, 2, 3 will be visible; device 1 is masked
CUDA_VISIBLE_DEVICES=""  # No GPU will be visible
```

## 实际应用场景

Tip

以下是一些可能的使用场景：

- 如果您有多张显卡，需要在卡0和卡1上启动两个`openai-server`服务，并分别监听不同的端口，可以使用以下命令：

  ```
  # 在终端1中
  CUDA_VISIBLE_DEVICES=0 mineru-openai-server --engine vllm --port 30000
  # 在终端2中
  CUDA_VISIBLE_DEVICES=1 mineru-openai-server --engine vllm --port 30001
  ```

- 如果您有多张显卡，需要在卡0和卡1上启动两个`fastapi`服务，并分别监听不同的端口，可以使用以下命令：

  ```
  # 在终端1中
  CUDA_VISIBLE_DEVICES=0 mineru-api --host 127.0.0.1 --port 8000
  # 在终端2中
  CUDA_VISIBLE_DEVICES=1 mineru-api --host 127.0.0.1 --port 8001
  ```

- 如果您有多张显卡，需要通过`router`在其中4张卡上启动`fastapi`服务并统一管理，可以使用以下命令：

  ```
  CUDA_VISIBLE_DEVICES=0,1,2,3 mineru-router --host 127.0.0.1 --port 8002
  ```