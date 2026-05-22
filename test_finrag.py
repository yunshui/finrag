#!/usr/bin/env python3
"""Tests for finrag.py — all use mocks, no real network calls."""

import json
import os
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import requests

# Import the module under test
import finrag


# ── Fixtures ───────────────────────────────────────────────────────────

MOCK_RESPONSE_JSON = {
    "context": "[来源: 行 248]\nHello world\n\n---\n\n[来源: 行 890]\nFoo bar",
    "tokens": 7878,
    "expanded_keywords": ["资产", "负债"],
    "stats": {
        "total_chunks": 70,
        "keywords_used": 2,
        "total_retrieved": 140,
        "merged_unique": 43,
        "selected": 2,
        "max_tokens": 12000,
        "loops_used": 1,
        "validation_enabled": True,
    },
    "chunks": [
        {"text": "Hello world", "score": 11.6, "metadata": {"line": 248}},
        {"text": "Foo bar", "score": 22.3, "metadata": {"line": 890}},
    ],
}

MOCK_CONFIG = {
    "api_url": "http://mock:8000/fin-rag",
    "client_id": "test-client",
    "query": "测试查询",
    "max_loops": 5,
    "retries": 1,
    "timeout": 10,
}


# ── extract_line_numbers ──────────────────────────────────────────────

class TestExtractLineNumbers(unittest.TestCase):
    def test_no_markers(self):
        self.assertEqual(finrag.extract_line_numbers("no markers here"), [])

    def test_single_marker(self):
        result = finrag.extract_line_numbers("[来源: 行 248]\nsome text")
        self.assertEqual(result, [248])

    def test_multiple_markers(self):
        ctx = "[来源: 行 100]\na\n\n---\n\n[来源: 行 200]\nb\n\n---\n\n[来源: 行 300]\nc"
        self.assertEqual(finrag.extract_line_numbers(ctx), [100, 200, 300])

    def test_duplicates_removed(self):
        ctx = "[来源: 行 100]\na\n[来源: 行 100]\nb"
        self.assertEqual(finrag.extract_line_numbers(ctx), [100])

    def test_sorted_output(self):
        ctx = "[来源: 行 300]\na\n[来源: 行 100]\nb\n[来源: 行 200]\nc"
        self.assertEqual(finrag.extract_line_numbers(ctx), [100, 200, 300])

    def test_whitespace_variants(self):
        ctx = "[来源:行42]\na\n[来源:  行  99]\nb"
        self.assertEqual(finrag.extract_line_numbers(ctx), [42, 99])

    def test_marker_with_chapter(self):
        ctx = "[来源: 行 294, 章节: \\n\\n9 業務分類資料(續)\\n\\n]\ntext"
        self.assertEqual(finrag.extract_line_numbers(ctx), [294])


# ── build_config ──────────────────────────────────────────────────────

class TestBuildConfig(unittest.TestCase):
    def setUp(self):
        self.args = MagicMock()
        self.args.query = None
        self.args.max_loops = None
        self.args.api_url = None
        self.args.client_id = None
        self.args.retries = None
        self.args.timeout = None

    @patch("finrag.load_config")
    def test_no_overrides(self, mock_load):
        mock_load.return_value = MOCK_CONFIG.copy()
        cfg = finrag.build_config(self.args)
        self.assertEqual(cfg["query"], "测试查询")
        self.assertEqual(cfg["max_loops"], 5)

    @patch("finrag.load_config")
    def test_query_override(self, mock_load):
        mock_load.return_value = MOCK_CONFIG.copy()
        self.args.query = "自定义查询"
        cfg = finrag.build_config(self.args)
        self.assertEqual(cfg["query"], "自定义查询")

    @patch("finrag.load_config")
    def test_max_loops_override(self, mock_load):
        mock_load.return_value = MOCK_CONFIG.copy()
        self.args.max_loops = 3
        cfg = finrag.build_config(self.args)
        self.assertEqual(cfg["max_loops"], 3)

    @patch("finrag.load_config")
    def test_multiple_overrides(self, mock_load):
        mock_load.return_value = MOCK_CONFIG.copy()
        self.args.query = "新查询"
        self.args.max_loops = 2
        self.args.retries = 5
        self.args.timeout = 30
        cfg = finrag.build_config(self.args)
        self.assertEqual(cfg["query"], "新查询")
        self.assertEqual(cfg["max_loops"], 2)
        self.assertEqual(cfg["retries"], 5)
        self.assertEqual(cfg["timeout"], 30)


# ── resolve_output_path ───────────────────────────────────────────────

class TestResolveOutputPath(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.output_dir = Path(self.tmpdir) / "output"

    def test_first_run(self):
        with patch.object(finrag, "OUTPUT_DIR", self.output_dir):
            path = finrag.resolve_output_path("report.md")
        self.assertEqual(path.name, "report.md")
        self.assertFalse(path.exists())

    def test_conflict_generates_suffix(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        existing = self.output_dir / "report.md"
        existing.touch()

        with patch.object(finrag, "OUTPUT_DIR", self.output_dir):
            path = finrag.resolve_output_path("report.md")
        self.assertNotEqual(path.name, "report.md")
        self.assertTrue(path.name.startswith("report_"))
        self.assertEqual(len(path.stem.split("_")[1]), 5)
        self.assertFalse(path.exists())


# ── send_request (mocked) ─────────────────────────────────────────────

class TestSendRequest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.input_file = Path(self.tmpdir) / "test.md"
        self.input_file.write_text("# Test\nHello world\n")
        self.logger = MagicMock()

    def test_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_RESPONSE_JSON
        mock_resp.raise_for_status.return_value = None

        with patch("finrag.requests.post", return_value=mock_resp) as mock_post:
            result, elapsed = finrag.send_request(MOCK_CONFIG, self.input_file, self.logger)

        self.assertEqual(result, MOCK_RESPONSE_JSON)
        self.assertIsInstance(elapsed, float)
        mock_post.assert_called_once()

    def test_file_not_found(self):
        missing = Path("/nonexistent/file.md")
        with patch("sys.exit", side_effect=SystemExit(1)):
            with self.assertRaises(SystemExit):
                finrag.send_request(MOCK_CONFIG, missing, self.logger)

    def test_retry_on_failure(self):
        """First attempt fails, second succeeds."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_RESPONSE_JSON
        mock_resp.raise_for_status.return_value = None

        cfg = {**MOCK_CONFIG, "retries": 3}
        with patch("finrag.requests.post", side_effect=[
            requests.RequestException("Connection refused"),
            mock_resp,
        ]) as mock_post:
            with patch("finrag.time.sleep"):
                result, elapsed = finrag.send_request(cfg, self.input_file, self.logger)

        self.assertEqual(result, MOCK_RESPONSE_JSON)
        self.assertEqual(mock_post.call_count, 2)

    def test_retry_exhausted(self):
        """All retries fail → sys.exit(1)."""
        cfg = {**MOCK_CONFIG, "retries": 2}
        with patch("finrag.requests.post", side_effect=requests.RequestException("Connection refused")):
            with patch("finrag.time.sleep"):
                with patch("sys.exit", side_effect=SystemExit(1)):
                    with self.assertRaises(SystemExit):
                        finrag.send_request(cfg, self.input_file, self.logger)


# ── save_output ───────────────────────────────────────────────────────

class TestSaveOutput(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.output_dir = Path(self.tmpdir) / "output"
        self.project_root = Path(self.tmpdir)
        self.logger = MagicMock()

    def test_saves_context(self):
        with patch.object(finrag, "OUTPUT_DIR", self.output_dir), \
             patch.object(finrag, "PROJECT_ROOT", self.project_root):
            out_path = finrag.save_output(
                MOCK_CONFIG, MOCK_RESPONSE_JSON, "report.md", self.logger, 1.23
            )

        self.assertTrue(out_path.exists())
        content = out_path.read_text(encoding="utf-8")
        self.assertIn("[来源: 行 248]", content)
        self.assertIn("Hello world", content)

    def test_logger_called(self):
        with patch.object(finrag, "OUTPUT_DIR", self.output_dir), \
             patch.object(finrag, "PROJECT_ROOT", self.project_root):
            finrag.save_output(
                MOCK_CONFIG, MOCK_RESPONSE_JSON, "report.md", self.logger, 1.23
            )

        # Verify logger.info was called
        self.assertTrue(self.logger.info.called)
        calls = [str(c) for c in self.logger.info.call_args_list]
        # Should contain tokens info
        self.assertTrue(any("tokens: 7878" in c for c in calls))


# ── main (full integration with mocks) ────────────────────────────────

class TestMain(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.input_file = Path(self.tmpdir) / "test.md"
        self.input_file.write_text("# Test\nContent\n")
        self.output_dir = Path(self.tmpdir) / "output"
        self.logs_dir = Path(self.tmpdir) / "logs"
        self.config_path = Path(self.tmpdir) / "conf" / "setting.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(MOCK_CONFIG))

    @patch("sys.argv", ["finrag.py", "test.md"])
    def test_main_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_RESPONSE_JSON
        mock_resp.raise_for_status.return_value = None

        with patch("finrag.PROJECT_ROOT", Path(self.tmpdir)), \
             patch("finrag.CONFIG_PATH", self.config_path), \
             patch("finrag.OUTPUT_DIR", self.output_dir), \
             patch("finrag.LOGS_DIR", self.logs_dir), \
             patch("finrag.requests.post", return_value=mock_resp), \
             patch("sys.argv", ["finrag.py", str(self.input_file)]):
            finrag.main()

        # Verify output file was created
        out_file = self.output_dir / "test.md"
        self.assertTrue(out_file.exists())
        self.assertIn("[来源: 行 248]", out_file.read_text())


# ── Run ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main()
