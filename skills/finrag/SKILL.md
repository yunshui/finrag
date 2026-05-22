# finrag Skill

Send local Markdown financial reports to the FinRAG API and save retrieved context.

## Usage

```bash
python3 {{skills_dir}}/finrag/finrag.py <input_md_file> [options]
```

## Options

| Option | Description |
|--------|-------------|
| `--query` | Override the query text |
| `--max_loops` | Override max_loops parameter |
| `--api_url` | Override API URL |
| `--client_id` | Override client_id header |
| `--retries` | Override retry count |
| `--timeout` | Override timeout (seconds) |

## Examples

```bash
# Basic usage
python3 {{skills_dir}}/finrag/finrag.py data/report.md

# Custom query
python3 {{skills_dir}}/finrag/finrag.py data/report.md --query "分析资产负债结构" --max_loops 5
```

## Output

- Context saved to `output/` directory
- Logs saved to `logs/` directory
