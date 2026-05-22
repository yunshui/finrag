# BACKEND.md — 后端/API 文档

## 1. 概述

finrag 本身是一个客户端工具，不实现服务端逻辑。本文档描述它所依赖的远端 FinRAG API 的规范，以及客户端与之交互的方式。

## 2. API 端点

### 2.1 基本信息

| 属性 | 值 |
|------|----|
| URL | `http://123.192.49.73:8000/fin-rag` |
| 方法 | `POST` |
| Content-Type | `multipart/form-data` |
| 认证 | 无（依赖 `client_id` 请求头标识） |

### 2.2 请求格式

#### Headers

| Header | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `client_id` | string | 是 | 客户端标识，用于区分调用方 | `bf-mkd` |

#### Form Data

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `file` | file | 是 | 财务报表文件（Markdown 格式） | `example-mtr.md` |
| `query` | string | 是 | 中文自然语言查询文本 | `使用财务报表生成现金流` |
| `max_loops` | int | 是 | 最大检索循环次数 | `8` |

### 2.3 客户端发送方式

```python
import requests

with open("example-mtr.md", "rb") as f:
    resp = requests.post(
        "http://123.192.49.73:8000/fin-rag",
        headers={"client_id": "bf-mkd"},
        files={"file": ("example-mtr.md", f, "text/markdown")},
        data={"query": "使用财务报表生成现金流", "max_loops": 8},
        timeout=60,
    )
    resp.raise_for_status()
    result = resp.json()
```

## 3. 响应格式

### 3.1 顶层结构

```json
{
    "context": "string",
    "tokens": 7878,
    "expanded_keywords": ["string", ...],
    "stats": { ... },
    "chunks": [ { ... }, ... ]
}
```

### 3.2 字段详细说明

#### `context`（string）

拼接后的检索文本内容。每个检索片段以 `[来源: 行 N]` 或 `[来源: 行 N, 章节: ...]` 标记开头，片段之间用 `\n\n---\n\n` 分隔。

标记模式：
- `[来源: 行 248]` — 仅行号
- `[来源: 行 294, 章节: \n\n9 業務分類資料(續)\n\n]` — 行号 + 章节标题

#### `tokens`（number）

本次请求消耗的 token 数量。示例值：`7878`。

#### `expanded_keywords`（array[string]）

从用户查询中自动扩展的财务领域关键词列表。示例值：

```json
[
    "綜合損益表",
    "財務狀況表",
    "現金流量表",
    "營業收入",
    "營業成本",
    "淨利潤",
    "資產",
    "負債",
    "淨資產",
    "現金流",
    "經營活動",
    "投資活動",
    "融資活動",
    "利息支出"
]
```

#### `stats`（object）

检索统计信息：

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `total_chunks` | int | 文档总 chunk 数 | 70 |
| `keywords_used` | int | 使用的关键词数量 | 14 |
| `total_retrieved` | int | 检索到的总片段数 | 140 |
| `merged_unique` | int | 去重后的唯一片段数 | 43 |
| `selected` | int | 最终选择的片段数 | 5 |
| `max_tokens` | int | 最大 token 限制 | 12000 |
| `loops_used` | int | 实际使用的检索循环次数 | 1 |
| `validation_enabled` | bool | 是否启用了检索验证 | true |

#### `chunks`（array[object]）

检索到的文本片段数组，按相关性排序。

每个 chunk 对象包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | string | 文本内容（CSV 格式的财务表格或文本描述） |
| `score` | number | 相关性得分（浮点数，越高越相关） |
| `metadata.line` | int | 原始文档中的起始行号 |
| `metadata.heading` | string | 所在章节标题 |
| `metadata.has_table` | bool | 是否包含表格 |
| `metadata.child_label` | string | 子标签（CSV 列名路径） |

### 3.3 完整响应示例

参见 `data/example-curl-output2.json`。

## 4. 错误响应

### 4.1 HTTP 状态码

| 状态码 | 含义 | 客户端处理 |
|--------|------|-----------|
| 200 | 成功 | 解析 JSON 响应 |
| 400 | 请求参数错误 | 重试（可能参数不匹配） |
| 404 | 端点不存在 | 重试（可能 URL 配置错误） |
| 500 | 服务器内部错误 | 重试 |
| 503 | 服务不可用 | 重试 |

### 4.2 客户端重试策略

客户端对所有 `requests.RequestException`（包括 HTTP 错误、网络错误、超时等）执行重试：

- 最大重试次数由 `retries` 配置控制（默认 3）
- 退避策略：线性退避，等待 `1 × attempt` 秒
- 重试耗尽后记录 ERROR 日志并退出

## 5. 数据领域说明

### 5.1 财务文档类型

FinRAG 主要处理以下类型的财务文档：

- 年度财务报表（Annual Reports）
- 中期财务报表（Interim Reports）
- 按照 HKFRS（香港财务报告准则）编制

### 5.2 典型输入文件结构

输入 Markdown 文件包含：
- CSV 格式的财务表格（以逗号分隔，数值可能用双引号包裹）
- 章节标题（Markdown `#` 标题语法）
- 文本描述段落
- 行号标记（在原始文档中的位置）

### 5.3 典型输出内容

输出 `context` 包含：
- 与查询相关的财务表格片段
- 相关文本描述段落
- 每个片段的来源行号标记
- 片段之间的分隔符 `---`

### 5.4 示例：现金流相关查询

查询：`使用财务报表生成现金流`

返回的 context 包含：
- 业务分类资料（收入和支出分类表）
- 财务衍生工具资产及负债表
- 融资活动产生的负债对账表
- 租赁现金流出总额表

提取的行号：248, 294, 890, 1162, 1181

## 6. 客户端交互协议

### 6.1 请求生命周期

```
1. 客户端读取本地 MD 文件
2. 构建 multipart/form-data POST 请求
3. 发送请求并等待响应（timeout 控制最长等待时间）
4. 收到 200 响应后解析 JSON
5. 提取 context 字段并保存到本地文件
6. 记录请求统计信息到日志
```

### 6.2 超时处理

- 默认超时 60 秒
- 超时触发 `requests.exceptions.Timeout`，计入重试
- 每次重试的超时独立计算（非累计）

### 6.3 大文件处理

- 文件以流式方式上传（`requests` 默认行为）
- 客户端不限制文件大小，实际限制取决于服务端配置
- 财务报表通常不超过 10MB

## 7. 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-05-22 | 初始版本 |
