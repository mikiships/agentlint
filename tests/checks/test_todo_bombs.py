from __future__ import annotations

from agentlint.checks import todo_bombs
from agentlint.parser import parse_unified_diff

from ._utils import make_diff, parse_diff_text


def test_todo_bombs_warns_on_one_marker() -> None:
    diff = parse_diff_text(make_diff("src/a.py", added=["# TODO: later"]))
    findings = todo_bombs.run(diff)
    assert len(findings) == 1
    assert findings[0].severity == "warning"


def test_todo_bombs_warns_on_three_markers() -> None:
    diff = parse_diff_text(make_diff("src/a.py", added=["# TODO", "# FIXME", "# HACK"]))
    findings = todo_bombs.run(diff)
    assert findings[0].severity == "warning"


def test_todo_bombs_errors_on_four_markers() -> None:
    diff = parse_diff_text(
        make_diff("src/a.py", added=["# TODO", "# FIXME", "# HACK", "# XXX"])
    )
    findings = todo_bombs.run(diff)
    assert findings[0].severity == "error"


def test_todo_bombs_is_case_insensitive() -> None:
    diff = parse_diff_text(make_diff("src/a.py", added=["# placeholder to fill"]))
    findings = todo_bombs.run(diff)
    assert len(findings) == 1


def test_todo_bombs_ignores_clean_diff() -> None:
    diff = parse_diff_text(make_diff("src/a.py", added=["print('ok')"]))
    assert todo_bombs.run(diff) == []


def test_todo_bombs_ignores_binary() -> None:
    text = """diff --git a/a.png b/a.png
Binary files a/a.png and b/a.png differ
"""
    diff = parse_unified_diff(text)
    assert todo_bombs.run(diff) == []
