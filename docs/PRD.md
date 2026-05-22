# PRD — 产品需求文档（Product Requirements Document）

## 1. 产品概述

**finrag** 是一个财务报表检索增强生成（Retrieval-Augmented Generation, RAG）命令行客户端工具。用户将本地财务报表 Markdown 文件（如港铁公司年报等 HKFRS 格式文件）通过 HTTP POST 发送至远端 FinRAG API 服务，工具自动从响应中提取检索到的上下文内容，并保存为本地 Markdown 文件。

## 2. 背景与动机

### 2.1 业务场景

财务分析师和研究人员需要从大量财务报表（年报、中期报告等）中快速检索与特定财务问题相关的上下文。FinRAG 后端服务通过关键词扩展、语义检索和多轮循环机制，从财务报表中抽取最相关的文本片段。

当前用户只能通过 curl 命令与 API 交互，存在以下痛点：
- curl 命令冗长且难以管理配置
- 无法自动提取和保存响应中的核心内容（`context` 字段）
- 没有重试机制，网络不稳定时需要手动重跑
- 没有日志记录，无法追踪查询历史和排查问题
- 文件名冲突时可能覆盖已有输出

### 2.2 目标用户

- 财务分析师
- 金融数据研究人员
- 需要批量处理财务报表的自动化流程

## 3. 产品目标

| 目标 | 描述 |
|------|------|
| 简化交互 | 将多参数 curl 命令封装为单文件 + 可选参数的 CLI 命令 |
| 自动提取 | 自动从 API 响应中提取 `context` 字段并保存 |
| 容错可靠 | 内置可配置的重试机制，网络抖动自动恢复 |
| 可追溯 | 每次请求的详细日志（输入、参数、耗时、结果）记录到文件 |
| 安全输出 | 文件名冲突时自动生成唯一文件名，不覆盖已有文件 |

## 4. 功能需求

### 4.1 配置文件管理

- **FR-001**：系统从 `conf/setting.json` 加载默认配置
- **FR-002**：配置项包括：`api_url`、`client_id`、`query`、`max_loops`、`retries`、`timeout`
- **FR-003**：命令行参数可覆盖任意配置项

### 4.2 命令行接口

- **FR-010**：支持必填位置参数 `input_file`（输入的 Markdown 文件路径）
- **FR-011**：支持可选参数：`--query`、`--max_loops`、`--api_url`、`--client_id`、`--retries`、`--timeout`
- **FR-012**：支持 `--help` 查看使用说明
- **FR-013**：输入文件不存在时输出错误信息并退出（退出码 1）

### 4.3 API 请求

- **FR-020**：发送 HTTP POST 请求到配置的 `api_url`
- **FR-021**：请求使用 `multipart/form-data` 编码，包含 `file`、`query`、`max_loops` 三个字段
- **FR-022**：请求头包含 `client_id`
- **FR-023**：文件以 `text/markdown` MIME 类型上传
- **FR-024**：请求失败时按配置的 `retries` 次数重试，重试间隔为 `1s × attempt_number`（线性退避）
- **FR-025**：请求超时时间可配置（默认 60 秒）
- **FR-026**：所有重试均失败后输出错误信息并退出（退出码 1）

### 4.4 响应处理

- **FR-030**：从 JSON 响应中提取 `context` 字段内容
- **FR-031**：从 `context` 中使用正则 `来源:\s*行\s*(\d+)` 提取所有行号
- **FR-032**：记录 `tokens`、`chunks` 数量、`stats` 统计信息

### 4.5 输出管理

- **FR-040**：将 `context` 内容写入 `output/` 目录下的文件
- **FR-041**：输出文件名与输入文件同名（扩展名 `.md`）
- **FR-042**：若输出文件已存在，自动追加 `_` + 5 位随机小写字母数字后缀
- **FR-043**：`output/` 目录不存在时自动创建

### 4.6 日志记录

- **FR-050**：日志同时输出到控制台（stdout）和日志文件
- **FR-051**：日志文件路径为 `logs/finrag-YYYY-MM-DD.log`（按天轮转）
- **FR-052**：日志格式：`[YYYY-MM-DD HH:MM:SS] LEVEL 消息`
- **FR-053**：记录请求开始信息：输入文件名、query、max_loops、url
- **FR-054**：记录请求结果：成功/失败、耗时、输出文件路径
- **FR-055**：记录提取的行号列表
- **FR-056**：记录 tokens、chunks 数量和 stats 统计
- **FR-057**：重试时记录每次失败的 attempt 编号、耗时和错误信息
- **FR-058**：`logs/` 目录不存在时自动创建

## 5. 非功能需求

| 编号 | 需求 |
|------|------|
| NFR-001 | 单文件实现，不引入超过一个外部依赖 |
| NFR-002 | 仅依赖 Python 标准库 + `requests` |
| NFR-003 | Python 3.7+ 兼容 |
| NFR-004 | 启动时间 < 1 秒（不含网络请求） |
| NFR-005 | 日志文件使用 UTF-8 编码 |
| NFR-006 | 输出文件使用 UTF-8 编码 |
| NFR-007 | 无状态设计，不持久化会话数据 |

## 6. 外部 API 规范

### 6.1 端点

```
POST http://123.192.49.73:8000/fin-rag
```

### 6.2 请求

| 参数 | 类型 | 位置 | 说明 |
|------|------|------|------|
| `file` | file | form-data | 财务报表 Markdown 文件 |
| `query` | string | form-data | 中文自然语言查询 |
| `max_loops` | int | form-data | 最大检索循环次数 |
| `client_id` | string | header | 客户端标识（如 `bf-mkd`） |

### 6.3 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `context` | string | 拼接后的检索文本，含 `[来源: 行 N]` 标记 |
| `tokens` | number | 消耗的 token 数量 |
| `expanded_keywords` | array[string] | 扩展的财务关键词列表 |
| `stats` | object | 检索统计（total_chunks, keywords_used, total_retrieved, merged_unique, selected, max_tokens, loops_used, validation_enabled） |
| `chunks` | array[object] | 检索到的文本片段数组 |

每个 chunk 对象：

| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | string | 文本内容 |
| `score` | number | 相关性得分 |
| `metadata` | object | 元数据（line, heading, has_table, child_label） |

## 7. 示例

### 7.1 输入（curl 等价命令）

```bash
curl --location --request POST 'http://123.192.49.73:8000/fin-rag' \
--header 'client_id: bf-mkd' \
--form 'file=@/C:/Users/gyyz-YangYunShui/Desktop/example-mtr.md' \
--form 'query=使用财务报表生成现金流' \
--form 'max_loops=8'
```

### 7.2 等价 finrag 命令

```bash
python finrag.py example-mtr.md
```

### 7.3 输出示例（日志）

```
[2026-05-22 14:00:00] INFO  输入文件: example-mtr.md | query: 使用财务报表生成现金流 | max_loops: 8 | url: http://123.192.49.73:8000/fin-rag
[2026-05-22 14:00:01] INFO  请求成功 | 耗时: 1.23s | 输出文件: output/example-mtr.md
[2026-05-22 14:00:01] INFO  提取行号: 248, 294, 890, 1162, 1181
[2026-05-22 14:00:01] INFO  tokens: 7878 | chunks: 5 | stats: {"total_chunks":70,"keywords_used":14,"total_retrieved":140,"merged_unique":43,"selected":5,"max_tokens":12000,"loops_used":1,"validation_enabled":true}
```

## 8. 术语表

| 术语 | 说明 |
|------|------|
| RAG | Retrieval-Augmented Generation，检索增强生成 |
| HKFRS | Hong Kong Financial Reporting Standards，香港财务报告准则 |
| chunk | 从原始文档中按行号分割的文本片段 |
| context | API 返回的拼接后的检索文本 |
| max_loops | RAG 检索的最大循环次数 |
| expanded_keywords | 从用户查询中自动扩展的财务领域关键词 |

## 9. 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-05-22 | 初始版本 |
