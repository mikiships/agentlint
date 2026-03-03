"""Shared utilities for built-in checks."""

from __future__ import annotations

import re
from collections.abc import Iterable

from agentlint.models import Diff, FileDiff

_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
}


def iter_changed_files(diff: Diff) -> Iterable[FileDiff]:
    for file_diff in diff.files:
        if file_diff.is_binary:
            continue
        yield file_diff


def iter_added_lines(diff: Diff):
    for file_diff in iter_changed_files(diff):
        for line_no, content in file_diff.added_content():
            yield file_diff, line_no, content


def iter_deleted_lines(diff: Diff):
    for file_diff in iter_changed_files(diff):
        for line_no, content in file_diff.deleted_content():
            yield file_diff, line_no, content


def extract_keywords(task_description: str | None) -> set[str]:
    if not task_description:
        return set()
    words = re.findall(r"[a-zA-Z0-9_./-]+", task_description.casefold())
    return {word for word in words if len(word) >= 3 and word not in _STOPWORDS}


def has_keyword_match(text: str, keywords: set[str]) -> bool:
    if not text or not keywords:
        return False
    haystack = text.casefold()
    return any(word in haystack for word in keywords)


def is_test_path(path: str) -> bool:
    normalized = path.casefold()
    return (
        "/test" in normalized
        or normalized.startswith("test")
        or "/spec" in normalized
        or normalized.endswith("_test.py")
        or normalized.endswith(".spec.ts")
        or normalized.endswith(".spec.js")
    )
