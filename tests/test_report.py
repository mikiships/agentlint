from __future__ import annotations

import json

from agentlint.models import CheckResult
from agentlint.report import (
    render,
    render_github,
    render_json,
    render_table,
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
    text = render_json(_sample_findings())
    payload = json.loads(text)
    assert payload["summary"]["error"] == 1
    assert "src/a.py" in payload["files"]


def test_render_github_annotations() -> None:
    text = render_github(_sample_findings())
    assert "::error file=src/a.py,line=10::" in text
    assert "::warning file=src/a.py,line=22::" in text
    assert "::notice::agentlint summary" in text


def test_render_table_has_summary_and_file_section() -> None:
    text = render_table(_sample_findings())
    assert "errors=1 warnings=2 info=1" in text
    assert "per-file summary" in text


def test_render_table_quiet_mode() -> None:
    text = render_table(_sample_findings(), quiet=True)
    assert text.splitlines()[0] == "errors=1 warnings=2 info=1"
    assert "\t" in text


def test_render_dispatch() -> None:
    assert "summary" in render(_sample_findings(), output_format="json")
    assert "::notice::" in render(_sample_findings(), output_format="github")
    assert "errors=1" in render(_sample_findings(), output_format="table")
