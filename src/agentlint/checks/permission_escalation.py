"""Detect potentially dangerous permission or command execution additions."""

from __future__ import annotations

import re

from agentlint.models import CheckResult, Diff

from ._common import iter_added_lines

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("sudo", re.compile(r"\bsudo\b")),
    ("chmod", re.compile(r"\bchmod\s+[0-7]{3,4}\b")),
    ("eval", re.compile(r"\beval\s*\(")),
    ("exec", re.compile(r"\bexec\s*\(")),
    ("subprocess_shell", re.compile(r"\bsubprocess\.(?:run|Popen|call)\([^\n]*shell\s*=\s*True")),
    ("os_system", re.compile(r"\bos\.system\s*\(")),
]


def run(diff: Diff, task_description: str | None = None) -> list[CheckResult]:
    del task_description

    findings: list[CheckResult] = []
    for file_diff, line_no, content in iter_added_lines(diff):
        for name, pattern in _PATTERNS:
            if pattern.search(content):
                findings.append(
                    CheckResult(
                        check_id="permission_escalation",
                        severity="error",
                        file_path=file_diff.path,
                        line=line_no,
                        message=f"Potential permission escalation pattern detected ({name})",
                    )
                )
                break

    return findings
