"""Detect long commented-out added code blocks."""

from __future__ import annotations

from agentlint.models import CheckResult, Diff

from ._common import iter_changed_files

_COMMENT_PREFIXES = ("#", "//", "/*", "*", "--")


def _is_comment_line(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    return stripped.startswith(_COMMENT_PREFIXES)


def run(diff: Diff, task_description: str | None = None) -> list[CheckResult]:
    del task_description

    findings: list[CheckResult] = []
    for file_diff in iter_changed_files(diff):
        block_size = 0
        block_start_line: int | None = None

        for line_no, content in file_diff.added_content():
            if _is_comment_line(content):
                if block_size == 0:
                    block_start_line = line_no
                block_size += 1
            else:
                if block_size >= 5:
                    findings.append(
                        CheckResult(
                            check_id="dead_code",
                            severity="warning",
                            file_path=file_diff.path,
                            line=block_start_line,
                            message="Added a large commented-out block that looks like dead code",
                        )
                    )
                block_size = 0
                block_start_line = None

        if block_size >= 5:
            findings.append(
                CheckResult(
                    check_id="dead_code",
                    severity="warning",
                    file_path=file_diff.path,
                    line=block_start_line,
                    message="Added a large commented-out block that looks like dead code",
                )
            )

    return findings
