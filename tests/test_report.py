from __future__ import annotations

import json

from agentlint.models import CheckResult
from agentlint.report import (
    REPORT_SCHEMA_VERSION,
    render,
    render_json,
    render_text,
    summarize,
    summarize_by_file,
)


def _sample_findings() -> list[CheckResult]:
    return [
        CheckResult("secret_leak", "secret found", "error", file_path="src/a.py", line=10),
        CheckResult("todo_bombs", "todo", "warning", file_path="src/a.py", line=22),
        CheckResult("scope_drift", "scope", "warning", file_path="docs/readme.md", line=1),
        CheckResult("note", "info note", "info", file_path="docs/readme.md", line=2),
    ]


def test_summarize_counts() -> None:
    assert summarize(_sample_findings()) == {"error": 1, "warning": 2, "info": 1}


def test_summarize_by_file() -> None:
    by_file = summarize_by_file(_sample_findings())
    assert by_file["src/a.py"] == {"error": 1, "warning": 1, "info": 0}
    assert by_file["docs/readme.md"] == {"error": 0, "warning": 1, "info": 1}


def test_render_json_includes_file_summary() -> None:
    text = render_json(
        _sample_findings(),
        tool_version="0.2.0",
        timestamp="2026-03-04T00:00:00Z",
    )
    payload = json.loads(text)
    assert payload["version"] == REPORT_SCHEMA_VERSION
    assert payload["metadata"] == {
        "version": "0.2.0",
        "timestamp": "2026-03-04T00:00:00Z",
    }
    assert payload["summary"] == {
        "total": 4,
        "by_severity": {"error": 1, "warning": 2, "info": 1},
    }
    assert payload["findings"][0] == {
        "severity": "error",
        "check": "secret_leak",
        "file": "src/a.py",
        "line": 10,
        "message": "secret found",
    }


def test_render_table_has_summary_and_file_section() -> None:
    text = render_text(_sample_findings())
    assert "errors=1 warnings=2 info=1" in text
    assert "per-file summary" in text


def test_render_table_quiet_mode() -> None:
    text = render_text(_sample_findings(), quiet=True)
    assert text.splitlines()[0] == "errors=1 warnings=2 info=1"
    assert "\t" in text


def test_render_dispatch() -> None:
    assert "summary" in render(_sample_findings(), output_format="json")
    assert "errors=1" in render(_sample_findings(), output_format="text")
    assert "# agentlint Report" in render(_sample_findings(), output_format="markdown")
