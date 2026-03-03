from __future__ import annotations

from agentlint.checks import scope_drift
from agentlint.parser import parse_unified_diff

from ._utils import make_diff, parse_diff_text


def test_scope_drift_skips_without_task() -> None:
    diff = parse_diff_text(make_diff("src/app.py", added=["print('x')"]))
    assert scope_drift.run(diff, task_description=None) == []


def test_scope_drift_accepts_keyword_in_path() -> None:
    diff = parse_diff_text(make_diff("src/parser.py", added=["print('x')"]))
    assert scope_drift.run(diff, task_description="update parser") == []


def test_scope_drift_accepts_keyword_in_content() -> None:
    diff = parse_diff_text(make_diff("src/app.py", added=["# parser fix"]))
    assert scope_drift.run(diff, task_description="parser fix") == []


def test_scope_drift_flags_unrelated_file() -> None:
    diff = parse_diff_text(make_diff("infra/main.tf", added=["resource x"]))
    findings = scope_drift.run(diff, task_description="update parser")
    assert len(findings) == 1
    assert findings[0].severity == "warning"


def test_scope_drift_ignores_binary_files() -> None:
    text = """diff --git a/image.png b/image.png
Binary files a/image.png and b/image.png differ
"""
    diff = parse_unified_diff(text)
    assert scope_drift.run(diff, task_description="parser") == []


def test_scope_drift_handles_empty_diff() -> None:
    diff = parse_diff_text("")
    assert scope_drift.run(diff, task_description="anything") == []
