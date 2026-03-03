"""Detect likely credential and secret leaks in added lines."""

from __future__ import annotations

import re

from agentlint.models import CheckResult, Diff

from ._common import iter_added_lines

_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bghp_[A-Za-z0-9]{36}\b")),
    (
        "credential_assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|token|secret|password|passwd)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"
        ),
    ),
    (
        "private_key",
        re.compile(r"-----BEGIN (?:RSA|EC|DSA|OPENSSH|PGP) PRIVATE KEY-----"),
    ),
    (
        "connection_string",
        re.compile(r"(?i)(?:postgres|postgresql|mysql|mongodb|redis)://[^\s'\"]+"),
    ),
]


def _is_allowed(value: str, allowed_patterns: list[str]) -> bool:
    for pattern in allowed_patterns:
        if re.search(pattern, value):
            return True
    return False


def run(diff: Diff, task_description: str | None = None, config: object | None = None) -> list[CheckResult]:
    del task_description
    allowed_patterns = list(getattr(config, "secret_allowed_patterns", []))

    findings: list[CheckResult] = []
    for file_diff, line_no, content in iter_added_lines(diff):
        for secret_name, pattern in _SECRET_PATTERNS:
            match = pattern.search(content)
            if not match:
                continue
            matched_value = match.group(0)
            if _is_allowed(matched_value, allowed_patterns):
                continue
            findings.append(
                CheckResult(
                    check_id="secret_leak",
                    severity="error",
                    file_path=file_diff.path,
                    line=line_no,
                    message=f"Potential secret leak detected ({secret_name})",
                    hint=matched_value,
                )
            )

    return findings
