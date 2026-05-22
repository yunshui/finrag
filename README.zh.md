# finrag

财务报表检索增强生成（RAG）命令行客户端。将本地 Markdown 文件发送至 FinRAG API，提取并保存检索到的上下文内容。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 基本用法
python finrag.py data/report.md

# 自定义查询参数
python finrag.py data/report.md --query "其他查询" --max_loops 5
```

## 项目结构

```
finrag/
├── conf/
│   └── setting.json          # 默认配置文件
├── logs/                     # 日志目录（运行时自动创建）
├── output/                   # 输出目录（运行时自动创建）
├── data/                     # 示例数据
├── finrag.py                 # 主程序
├── requirements.txt          # Python 依赖
├── README.md                 # English documentation
└── README.zh.md              # 中文文档
```

## 配置文件

编辑 `conf/setting.json`：

```json
{
  "api_url": "http://123.192.49.73:8000/fin-rag",
  "client_id": "bf-mkd",
  "query": "使用财务报表生成现金流",
  "max_loops": 8,
  "retries": 3,
  "timeout": 60
}
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `api_url` | API 地址 | `http://123.192.49.73:8000/fin-rag` |
| `client_id` | 客户端标识 | `bf-mkd` |
| `query` | 自然语言查询（中文） | `使用财务报表生成现金流` |
| `max_loops` | 最大检索循环次数 | `8` |
| `retries` | 请求重试次数 | `3` |
| `timeout` | 请求超时（秒） | `60` |

## 命令行参数

```
python finrag.py <input_md_file> [options]
```

| 参数 | 说明 |
|------|------|
| `input_file` | 输入的 Markdown 文件路径（必需） |
| `--query` | 覆盖配置文件中的查询文本 |
| `--max_loops` | 覆盖配置文件中的 max_loops 值 |
| `--api_url` | 覆盖 API 地址 |
| `--client_id` | 覆盖客户端标识 |
| `--retries` | 覆盖重试次数 |
| `--timeout` | 覆盖超时时间（秒） |

## 响应结构

API 返回的 JSON 响应字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `context` | string | 拼接后的检索文本内容 |
| `tokens` | number | 消耗的 token 数量 |
| `expanded_keywords` | array | 从查询中扩展的财务关键词列表 |
| `stats` | object | 检索统计信息 |
| `chunks` | array | 检索到的文本片段，每个包含 `text`、`score` 和 `metadata` |

## 日志

日志按天写入 `logs/finrag-YYYY-MM-DD.log`，同时输出到控制台：

```
[2026-05-22 14:00:00] INFO  输入文件: report.md | query: xxx | max_loops: 8
[2026-05-22 14:00:01] INFO  请求成功 | 耗时: 1.23s | 输出文件: output/report.md
[2026-05-22 14:00:01] INFO  提取行号: 248, 294, 890, 1162, 1181
[2026-05-22 14:00:01] INFO  tokens: 7878 | chunks: 5
```

## 输出

检索到的 `context` 内容保存到 `output/` 目录，文件名与输入文件相同。若文件名已存在，自动追加 `_` + 5 位随机字符以避免覆盖：

```
output/
├── report.md
└── report_a3k9x.md    # 文件名冲突时自动生成
```

## 许可证

MIT
