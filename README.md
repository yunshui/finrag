# finrag

A command-line client for the Financial Report Retrieval-Augmented Generation (RAG) service. Sends local Markdown files to the FinRAG API and saves the retrieved context.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Basic usage
python finrag.py data/report.md

# Override query parameters
python finrag.py data/report.md --query "其他查询" --max_loops 5
```

## Project Structure

```
finrag/
├── conf/
│   └── setting.json          # Default configuration
├── logs/                     # Log directory (created at runtime)
├── output/                   # Output directory (created at runtime)
├── data/                     # Sample data
├── finrag.py                 # Main program
├── requirements.txt          # Python dependencies
├── README.md                 # English documentation
└── README.zh.md              # Chinese documentation
```

## Configuration

Edit `conf/setting.json`:

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

| Parameter | Description | Default |
|-----------|-------------|---------|
| `api_url` | API endpoint URL | `http://123.192.49.73:8000/fin-rag` |
| `client_id` | Client identifier | `bf-mkd` |
| `query` | Natural language query (Chinese) | `使用财务报表生成现金流` |
| `max_loops` | Maximum retrieval loops | `8` |
| `retries` | Request retry count | `3` |
| `timeout` | Request timeout (seconds) | `60` |

## CLI Options

```
python finrag.py <input_md_file> [options]
```

| Option | Description |
|--------|-------------|
| `input_file` | Input Markdown file path (required) |
| `--query` | Override the query text |
| `--max_loops` | Override the max_loops value |
| `--api_url` | Override the API URL |
| `--client_id` | Override the client_id header |
| `--retries` | Override the retry count |
| `--timeout` | Override the timeout in seconds |

## Response Structure

The API returns a JSON response with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `context` | string | Concatenated retrieved text content |
| `tokens` | number | Token count consumed |
| `expanded_keywords` | array | List of finance-related keywords expanded from the query |
| `stats` | object | Retrieval statistics |
| `chunks` | array | Retrieved text chunks, each with `text`, `score`, and `metadata` |

## Logging

Logs are written daily to `logs/finrag-YYYY-MM-DD.log` and also printed to the console:

```
[2026-05-22 14:00:00] INFO  输入文件: report.md | query: xxx | max_loops: 8
[2026-05-22 14:00:01] INFO  请求成功 | 耗时: 1.23s | 输出文件: output/report.md
[2026-05-22 14:00:01] INFO  提取行号: 248, 294, 890, 1162, 1181
[2026-05-22 14:00:01] INFO  tokens: 7878 | chunks: 5
```

## Output

Retrieved `context` content is saved to the `output/` directory using the input filename. If a file with the same name already exists, a `_` + 5 random character suffix is appended to avoid overwriting:

```
output/
├── report.md
└── report_a3k9x.md    # Auto-generated on filename conflict
```

## License

MIT
