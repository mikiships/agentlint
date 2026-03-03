from __future__ import annotations

from agentlint.checks import dead_code
from agentlint.parser import parse_unified_diff

from ._utils import make_diff, parse_diff_text


def test_dead_code_flags_five_comment_lines() -> None:
    diff = parse_diff_text(
        make_diff("src/app.py", added=["# one", "# two", "# three", "# four", "# five"])
    )
    findings = dead_code.run(diff)
    assert len(findings) == 1


def test_dead_code_ignores_four_comment_lines() -> None:
    diff = parse_diff_text(make_diff("src/app.py", added=["# one", "# two", "# three", "# four"]))
    assert dead_code.run(diff) == []


def test_dead_code_resets_on_non_comment() -> None:
    diff = parse_diff_text(
        make_diff(
            "src/app.py",
            added=["# one", "# two", "# three", "print('x')", "# four", "# five", "# six"],
        )
    )
    assert dead_code.run(diff) == []


def test_dead_code_flags_multiple_blocks() -> None:
    diff = parse_diff_text(
        make_diff(
            "src/app.py",
            added=[
                "# a",
                "# b",
                "# c",
                "# d",
                "# e",
                "print('x')",
                "# f",
                "# g",
                "# h",
                "# i",
                "# j",
            ],
        )
    )
    findings = dead_code.run(diff)
    assert len(findings) == 2


def test_dead_code_ignores_regular_additions() -> None:
    diff = parse_diff_text(make_diff("src/app.py", added=["x = 1", "y = 2"]))
    assert dead_code.run(diff) == []


def test_dead_code_ignores_binary() -> None:
    text = """diff --git a/src/a.png b/src/a.png
Binary files a/src/a.png and b/src/a.png differ
"""
    diff = parse_unified_diff(text)
    assert dead_code.run(diff) == []
