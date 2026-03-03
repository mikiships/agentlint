"""Detect files that appear unrelated to the requested task."""

from __future__ import annotations

from agentlint.models import CheckResult, Diff

from ._common import extract_keywords, has_keyword_match, iter_changed_files


def run(diff: Diff, task_description: str | None = None) -> list[CheckResult]:
    keywords = extract_keywords(task_description)
    if not keywords:
        return []

    findings: list[CheckResult] = []
    for file_diff in iter_changed_files(diff):
        path_match = has_keyword_match(file_diff.path, keywords)
        content_match = any(has_keyword_match(content, keywords) for _, content in file_diff.added_content())
        if path_match or content_match:
            continue

        findings.append(
            CheckResult(
                check_id="scope_drift",
                severity="warning",
                file_path=file_diff.path,
                line=None,
                message="Changed file appears out of scope for the provided task description",
            )
        )

    return findings
