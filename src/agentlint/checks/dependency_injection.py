"""Detect unexpected dependency additions."""

from __future__ import annotations

import re

from agentlint.models import CheckResult, Diff

from ._common import extract_keywords, has_keyword_match, iter_added_lines

_DEP_FILES = (
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "package.json",
    "cargo.toml",
)

_DEP_LINE_PATTERNS = [
    re.compile(r"^[A-Za-z0-9_.\-]+\s*(?:==|>=|<=|~=|>|<).+"),
    re.compile(r'^\s*"[A-Za-z0-9_.\-/]+"\s*:\s*"[^"]+"\s*,?$'),
    re.compile(r"^[A-Za-z0-9_.\-]+\s*=\s*\{?.+"),
]

_ALLOWED_KEYWORDS = {"dependency", "dependencies", "upgrade", "bump", "package", "library"}


def _is_dependency_file(path: str) -> bool:
    lowered = path.casefold()
    if lowered.endswith(tuple(_DEP_FILES)):
        return True
    return lowered.endswith(".lock")


def _is_dependency_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return False
    if stripped.startswith("[") and stripped.endswith("]"):
        return False
    return any(pattern.match(stripped) for pattern in _DEP_LINE_PATTERNS)


def run(diff: Diff, task_description: str | None = None) -> list[CheckResult]:
    keywords = extract_keywords(task_description)
    task_allows_dependency_change = bool(keywords & _ALLOWED_KEYWORDS)

    found_by_file: dict[str, int] = {}
    first_line: dict[str, int | None] = {}
    for file_diff, line_no, content in iter_added_lines(diff):
        if not _is_dependency_file(file_diff.path):
            continue
        if not _is_dependency_line(content):
            continue

        found_by_file[file_diff.path] = found_by_file.get(file_diff.path, 0) + 1
        first_line.setdefault(file_diff.path, line_no)

    findings: list[CheckResult] = []
    for path, count in found_by_file.items():
        if task_allows_dependency_change and has_keyword_match(path, keywords):
            continue
        if task_allows_dependency_change:
            continue

        findings.append(
            CheckResult(
                check_id="dependency_injection",
                severity="warning",
                file_path=path,
                line=first_line.get(path),
                message=f"Added {count} dependency declaration(s) without task approval",
            )
        )

    return findings
