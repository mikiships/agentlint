from __future__ import annotations

from agentlint.checks import test_regression
from agentlint.parser import parse_unified_diff

from ._utils import make_diff, parse_diff_text


def test_regression_warns_on_test_deletion_without_addition() -> None:
    diff = parse_diff_text(make_diff("tests/test_api.py", deleted=["assert x"]))
    findings = test_regression.run(diff)
    assert len(findings) == 1
    assert "deleted" in findings[0].message.casefold()


def test_regression_no_warning_when_tests_replaced() -> None:
    diff = parse_diff_text(make_diff("tests/test_api.py", deleted=["assert x"], added=["assert y"]))
    findings = test_regression.run(diff)
    assert findings == []


def test_regression_warns_on_off_task_test_change() -> None:
    diff = parse_diff_text(make_diff("tests/test_parser.py", added=["assert True"]))
    findings = test_regression.run(diff, task_description="update docs")
    assert len(findings) == 1
    assert "outside" in findings[0].message.casefold()


def test_regression_allows_test_changes_when_task_mentions_tests() -> None:
    diff = parse_diff_text(make_diff("tests/test_parser.py", added=["assert True"]))
    assert test_regression.run(diff, task_description="add tests for parser") == []


def test_regression_ignores_non_test_files() -> None:
    diff = parse_diff_text(make_diff("src/app.py", deleted=["x"], added=["y"]))
    assert test_regression.run(diff) == []


def test_regression_ignores_binary_diff() -> None:
    text = """diff --git a/tests/snapshot.png b/tests/snapshot.png
Binary files a/tests/snapshot.png and b/tests/snapshot.png differ
"""
    diff = parse_unified_diff(text)
    assert test_regression.run(diff) == []
