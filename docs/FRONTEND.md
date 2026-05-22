# FRONTEND.md — 前端/交互界面文档

## 1. 概述

finrag 当前无图形用户界面（GUI），纯命令行（CLI）工具。本文档定义 CLI 交互规范和未来 GUI 扩展的接口要求。

## 2. 命令行界面

### 2.1 基本用法

```bash
python finrag.py <input_md_file> [options]
```

### 2.2 参数详情

#### 位置参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `input_file` | string | 是 | 输入的 Markdown 文件路径（相对于或绝对于当前工作目录） |

#### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--query` | string | 配置文件中 `query` 值 | 覆盖查询文本 |
| `--max_loops` | int | 配置文件中 `max_loops` 值 | 覆盖最大检索循环次数 |
| `--api_url` | string | 配置文件中 `api_url` 值 | 覆盖 API 地址 |
| `--client_id` | string | 配置文件中 `client_id` 值 | 覆盖客户端标识 |
| `--retries` | int | 配置文件中 `retries` 值 | 覆盖重试次数 |
| `--timeout` | int | 配置文件中 `timeout` 值 | 覆盖超时时间（秒） |
| `-h`, `--help` | — | — | 显示帮助信息并退出 |

### 2.3 Help 输出

```
usage: finrag.py [-h] [--query QUERY] [--max_loops MAX_LOOPS]
                 [--api_url API_URL] [--client_id CLIENT_ID]
                 [--retries RETRIES] [--timeout TIMEOUT]
                 input_file

Send a Markdown file to the FinRAG API and save retrieved context.

positional arguments:
  input_file            Path to the input Markdown file

options:
  -h, --help            show this help message and exit
  --query QUERY         Override the query text
  --max_loops MAX_LOOPS
                        Override max_loops parameter
  --api_url API_URL     Override API URL
  --client_id CLIENT_ID
                        Override client_id header
  --retries RETRIES     Override retry count
  --timeout TIMEOUT     Override timeout (seconds)
```

### 2.4 使用示例

```bash
# 使用默认配置
python finrag.py data/report.md

# 自定义查询
python finrag.py data/report.md --query "分析资产负债结构" --max_loops 5

# 指定不同 API 地址
python finrag.py data/report.md --api_url http://localhost:8000/fin-rag

# 增加重试次数和超时
python finrag.py data/report.md --retries 5 --timeout 120

# 查看所有可用参数
python finrag.py --help
```

### 2.5 控制台输出

#### 正常流程

```
[2026-05-22 14:00:00] INFO  输入文件: report.md | query: 使用财务报表生成现金流 | max_loops: 8 | url: http://123.192.49.73:8000/fin-rag
[2026-05-22 14:00:01] INFO  请求成功 | 耗时: 1.23s | 输出文件: output/report.md
[2026-05-22 14:00:01] INFO  提取行号: 248, 294, 890, 1162, 1181
[2026-05-22 14:00:01] INFO  tokens: 7878 | chunks: 5 | stats: {"total_chunks":70,"keywords_used":14,"total_retrieved":140,"merged_unique":43,"selected":5,"max_tokens":12000,"loops_used":1,"validation_enabled":true}

Done → /Users/yunshuiyang/Workspace/finrag/output/report.md
```

#### 重试场景

```
[2026-05-22 14:00:00] INFO  输入文件: report.md | query: 使用财务报表生成现金流 | max_loops: 8 | url: http://123.192.49.73:8000/fin-rag
[2026-05-22 14:01:01] WARNING 请求失败 (attempt 1/3) | 耗时: 60.01s | 错误: Connection timed out
[2026-05-22 14:02:02] WARNING 请求失败 (attempt 2/3) | 耗时: 60.00s | 错误: Connection timed out
[2026-05-22 14:03:03] WARNING 请求失败 (attempt 3/3) | 耗时: 60.02s | 错误: Connection timed out
[2026-05-22 14:03:03] ERROR 请求最终失败 | 最后错误: Connection timed out
```

#### 错误场景

```
[2026-05-22 14:00:00] ERROR 输入文件不存在: /path/to/nonexistent.md
```

## 3. 输出文件

### 3.1 文件格式

输出文件为纯文本 Markdown 文件，内容为 API 返回的 `context` 字段原始值，不做任何格式转换或美化。

### 3.2 内容结构

`context` 由多个检索片段拼接而成，每个片段以 `[来源: 行 N]` 或 `[来源: 行 N, 章节: ...]` 标记开头，片段之间用 `---` 分隔。

```
[来源: 行 248]
百萬港元,香港 客運服務,香港 物業租賃 及管理業務,...
（表格数据...）

---

[来源: 行 294, 章节: \n\n9 業務分類資料(續)\n\n]
\n\n9 業務分類資料(續)\n\n
百萬港元,香港 客運服務,...
（表格数据和文本...）

---

[来源: 行 890]
,名義金額,公允價值,...
（表格数据...）
```

### 3.3 文件命名规则

| 场景 | 输出文件名 |
|------|-----------|
| 首次运行 | `output/<输入文件名stem>.md` |
| 文件已存在 | `output/<输入文件名stem>_<随机5字符>.md` |

随机字符集：`[a-z0-9]`，长度 5，理论上 60,466,176 种组合。

## 4. 日志文件

### 4.1 文件位置

```
logs/finrag-YYYY-MM-DD.log
```

### 4.2 格式

每条日志一行：

```
[YYYY-MM-DD HH:MM:SS] LEVEL 消息
```

| 字段 | 格式 |
|------|------|
| 时间 | `YYYY-MM-DD HH:MM:SS`（24 小时制） |
| 级别 | `INFO`、`WARNING`、`ERROR`（左对齐，占 5 字符） |
| 消息 | 结构化文本，` | ` 分隔各字段 |

### 4.3 日志内容

每次成功请求的完整日志包含四条记录：

| 序号 | 级别 | 内容 |
|------|------|------|
| 1 | INFO | 请求开始：输入文件名、query、max_loops、url |
| 2 | INFO | 请求成功：耗时、输出文件路径 |
| 3 | INFO | 提取的行号列表（如有） |
| 4 | INFO | 统计信息：tokens、chunks 数量、stats JSON |

## 5. 未来 GUI 扩展考虑

如果未来需要构建图形界面，建议遵循以下原则：

### 5.1 可复用的核心逻辑

当前 `finrag.py` 中的函数设计为纯函数（无全局状态），可直接被 GUI 框架调用：

| 函数 | GUI 用途 |
|------|---------|
| `load_config()` / `build_config()` | 配置管理界面 |
| `send_request()` | 执行请求（需异步包装） |
| `extract_line_numbers()` | 行号可视化 |
| `resolve_output_path()` | 输出路径管理 |

### 5.2 GUI 功能建议

- 文件选择器（替代命令行参数）
- 查询输入框（带历史记录）
- 实时日志/进度显示
- 输出内容预览和导出
- 配置管理界面

### 5.3 框架建议

| 框架 | 适用场景 |
|------|---------|
| `tkinter` | 轻量级，Python 内置 |
| `PyQt`/`PySide` | 功能丰富，跨平台 |
| `gradio` | 快速原型，Web 界面 |
| `streamlit` | 快速数据应用，Web 界面 |

## 6. 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-05-22 | 初始版本 |
