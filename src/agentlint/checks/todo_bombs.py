"""Detect suspicious influx of TODO/FIXME-style placeholders."""

from __future__ import annotations

import re

from agentlint.models import CheckResult, Diff

from ._common import iter_added_lines

_TODO_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX|PLACEHOLDER)\b", re.IGNORECASE)


def run(diff: Diff, task_description: str | None = None) -> list[CheckResult]:
    del task_description

    matches: list[tuple[str, int | None]] = []
    for file_diff, line_no, content in iter_added_lines(diff):
        if _TODO_RE.search(content):
            matches.append((file_diff.path, line_no))

    count = len(matches)
    if count == 0:
        return []

    first_path, first_line = matches[0]
    severity = "error" if count > 3 else "warning"
    return [
        CheckResult(
            check_id="todo_bombs",
            severity=severity,
            file_path=first_path,
            line=first_line,
            message=f"Added {count} TODO/FIXME/HACK markers",
        )
    ]
