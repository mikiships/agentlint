"""Detect potentially risky test deletions or off-task test changes."""

from __future__ import annotations

from agentlint.models import CheckResult, Diff

from ._common import extract_keywords, has_keyword_match, is_test_path, iter_changed_files


def run(diff: Diff, task_description: str | None = None) -> list[CheckResult]:
    keywords = extract_keywords(task_description)
    task_mentions_tests = bool(task_description and "test" in task_description.casefold())

    findings: list[CheckResult] = []
    for file_diff in iter_changed_files(diff):
        if not is_test_path(file_diff.path):
            continue

        if file_diff.deleted_lines > 0 and file_diff.added_lines == 0:
            findings.append(
                CheckResult(
                    check_id="test_regression",
                    severity="warning",
                    file_path=file_diff.path,
                    message="Test lines were deleted without corresponding additions",
                )
            )

        if keywords and not task_mentions_tests and not has_keyword_match(file_diff.path, keywords):
            findings.append(
                CheckResult(
                    check_id="test_regression",
                    severity="warning",
                    file_path=file_diff.path,
                    message="Test file changed outside the described task scope",
                )
            )

    return findings
