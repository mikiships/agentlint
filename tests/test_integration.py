from __future__ import annotations

import json

from click.testing import CliRunner

from agentlint import cli


def test_integration_empty_diff_clean_exit() -> None:
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--stdin", "--format", "json"], input="")
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["summary"] == {"error": 0, "warning": 0, "info": 0}


def test_integration_binary_diff_no_findings() -> None:
    diff = """diff --git a/a.png b/a.png
Binary files a/a.png and b/a.png differ
"""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--stdin", "--format", "json"], input=diff)
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["results"] == []


def test_integration_rename_diff_parsed() -> None:
    diff = """diff --git a/old.py b/new.py
similarity index 100%
rename from old.py
rename to new.py
"""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--stdin", "--format", "json"], input=diff)
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["summary"]["error"] == 0


def test_integration_json_schema_keys() -> None:
    diff = """diff --git a/requirements.txt b/requirements.txt
--- a/requirements.txt
+++ b/requirements.txt
@@ -1 +1,2 @@
 requests==2.0.0
+flask==3.0.0
"""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--stdin", "--format", "json"], input=diff)
    payload = json.loads(result.output)
    assert set(payload.keys()) == {"files", "results", "summary"}
    assert all({"check_id", "severity", "message", "file", "line", "hint"} <= set(item) for item in payload["results"])


def test_integration_fail_on_error_threshold() -> None:
    diff = """diff --git a/requirements.txt b/requirements.txt
--- a/requirements.txt
+++ b/requirements.txt
@@ -1 +1,2 @@
 requests==2.0.0
+flask==3.0.0
"""
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["check", "--stdin", "--fail-on", "error", "--format", "json"],
        input=diff,
    )
    assert result.exit_code == 0


def test_integration_mega_diff_runs() -> None:
    added = "\n".join(f"+line_{idx}" for idx in range(200))
    diff = (
        "diff --git a/src/big.py b/src/big.py\n"
        "--- a/src/big.py\n"
        "+++ b/src/big.py\n"
        "@@ -1,1 +1,200 @@\n"
        "-line_old\n"
        f"{added}\n"
    )
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--stdin", "--quiet"], input=diff)
    assert result.exit_code in (0, 1, 2)
    assert "errors=" in result.output
