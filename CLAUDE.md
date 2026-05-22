# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**finrag** is a Financial Report Retrieval-Augmented Generation (RAG) service. It accepts financial report files (e.g., Markdown) via HTTP POST and returns relevant retrieved context chunks based on a natural language query.

## API

The service exposes a single endpoint:

- **POST** `http://123.192.49.73:8000/fin-rag`

### Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `file` | form-data (file) | Financial report file (e.g., `.md`) |
| `query` | form-data (string) | Natural language query in Chinese (e.g., "使用财务报表生成现金流") |
| `max_loops` | form-data (int) | Maximum retrieval loops |

Headers must include `client_id` (e.g., `bf-mkd`).

### Response Structure

The JSON response contains:
- `context` — concatenated retrieved text chunks
- `tokens` — token count used
- `expanded_keywords` — list of finance-related keywords expanded from the query
- `stats` — retrieval statistics (total_chunks, keywords_used, total_retrieved, merged_unique, selected, max_tokens, loops_used, validation_enabled)
- `chunks` — array of retrieved chunks, each with `text`, `score`, and `metadata` (line number, heading, has_table, child_label)

## Repository Structure

```
finrag/
├── data/                          # Empty directory, likely for input data
├── example-curl-input2.json       # Example curl command for API requests
└── example-curl-output2.json      # Example API response output
```

## Notes

- The domain is primarily Traditional Chinese financial reports (e.g., MTR Corporation annual reports under HKFRS)
- The RAG system processes tabular financial data with line-number-based chunk metadata
- No source code is present in this repository — only API examples
