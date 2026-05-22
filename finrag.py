#!/usr/bin/env python3
"""finrag — Financial Report RAG CLI client.

Sends local Markdown files to the FinRAG API and saves the retrieved context.

Usage:
    python finrag.py <input_md_file>
    python finrag.py data/example-mtr.md --query "其他查询" --max_loops 5
"""

import argparse
import json
import logging
import os
import random
import re
import string
import sys
import time
from pathlib import Path

import requests

# ── Paths ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "conf" / "setting.json"
LOGS_DIR = PROJECT_ROOT / "logs"
OUTPUT_DIR = PROJECT_ROOT / "output"


# ── Config ─────────────────────────────────────────────────────────────
def load_config():
    """Load default config from conf/setting.json."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_args():
    """Parse CLI arguments, overriding config values where provided."""
    parser = argparse.ArgumentParser(
        description="Send a Markdown file to the FinRAG API and save retrieved context."
    )
    parser.add_argument("input_file", help="Path to the input Markdown file")
    parser.add_argument("--query", default=None, help="Override the query text")
    parser.add_argument(
        "--max_loops", type=int, default=None, help="Override max_loops parameter"
    )
    parser.add_argument("--api_url", default=None, help="Override API URL")
    parser.add_argument("--client_id", default=None, help="Override client_id header")
    parser.add_argument("--retries", type=int, default=None, help="Override retry count")
    parser.add_argument("--timeout", type=int, default=None, help="Override timeout (seconds)")
    return parser.parse_args()


def build_config(args):
    """Merge config file with CLI overrides."""
    cfg = load_config()
    if args.query is not None:
        cfg["query"] = args.query
    if args.max_loops is not None:
        cfg["max_loops"] = args.max_loops
    if args.api_url is not None:
        cfg["api_url"] = args.api_url
    if args.client_id is not None:
        cfg["client_id"] = args.client_id
    if args.retries is not None:
        cfg["retries"] = args.retries
    if args.timeout is not None:
        cfg["timeout"] = args.timeout
    return cfg


# ── Logger ─────────────────────────────────────────────────────────────
def setup_logger():
    """Set up logger that writes to both console and daily log file."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"finrag-{time.strftime('%Y-%m-%d')}.log"

    logger = logging.getLogger("finrag")
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("[%(asctime)s] %(levelname)-5s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger


# ── Request ────────────────────────────────────────────────────────────
def send_request(cfg, input_path, logger):
    """POST the file to the API with retry logic. Returns (response_json, elapsed)."""
    input_path = Path(input_path)
    if not input_path.is_file():
        logger.error(f"输入文件不存在: {input_path}")
        sys.exit(1)

    url = cfg["api_url"]
    headers = {"client_id": cfg["client_id"]}
    retries = cfg.get("retries", 3)
    timeout = cfg.get("timeout", 60)

    with open(input_path, "rb") as f:
        files = {"file": (input_path.name, f, "text/markdown")}
        data = {
            "query": cfg["query"],
            "max_loops": cfg["max_loops"],
        }

        logger.info(
            f"输入文件: {input_path.name} | query: {cfg['query']} | max_loops: {cfg['max_loops']} | url: {url}"
        )

        last_err = None
        for attempt in range(1, retries + 1):
            start = time.monotonic()
            try:
                resp = requests.post(
                    url, headers=headers, files=files, data=data, timeout=timeout
                )
                elapsed = time.monotonic() - start
                resp.raise_for_status()
                return resp.json(), elapsed
            except requests.RequestException as e:
                elapsed = time.monotonic() - start
                last_err = e
                logger.warning(
                    f"请求失败 (attempt {attempt}/{retries}) | 耗时: {elapsed:.2f}s | 错误: {e}"
                )
                if attempt < retries:
                    time.sleep(1 * attempt)

        logger.error(f"请求最终失败 | 最后错误: {last_err}")
        sys.exit(1)


# ── Output ─────────────────────────────────────────────────────────────
def resolve_output_path(input_name):
    """Return a non-conflicting output path. Appends _XXXXX if file exists."""
    stem = Path(input_name).stem
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{stem}.md"
    if not out_path.exists():
        return out_path
    suffix = "_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    out_path = OUTPUT_DIR / f"{stem}{suffix}.md"
    return out_path


def extract_line_numbers(context):
    """Extract line numbers from [来源: 行 N] patterns in context."""
    return sorted(set(int(n) for n in re.findall(r"来源:\s*行\s*(\d+)", context)))


def save_output(cfg, result, input_name, logger, elapsed):
    """Save context to output file and log summary."""
    context = result.get("context", "")
    tokens = result.get("tokens", 0)
    chunks = result.get("chunks", [])
    stats = result.get("stats", {})

    out_path = resolve_output_path(input_name)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(context)

    line_numbers = extract_line_numbers(context)
    rel_path = out_path.relative_to(PROJECT_ROOT)

    logger.info(
        f"请求成功 | 耗时: {elapsed:.2f}s | 输出文件: {rel_path}"
    )
    if line_numbers:
        logger.info(f"提取行号: {', '.join(str(n) for n in line_numbers)}")
    logger.info(
        f"tokens: {tokens} | chunks: {len(chunks)} | "
        f"stats: {json.dumps(stats, ensure_ascii=False)}"
    )

    return out_path


# ── Main ───────────────────────────────────────────────────────────────
def main():
    args = parse_args()
    cfg = build_config(args)
    logger = setup_logger()

    input_path = Path(args.input_file)
    input_name = input_path.name

    result, elapsed = send_request(cfg, input_path, logger)
    out_path = save_output(cfg, result, input_name, logger, elapsed)

    print(f"\nDone → {out_path}")


if __name__ == "__main__":
    main()
