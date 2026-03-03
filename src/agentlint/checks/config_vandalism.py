"""Detect risky CI/config/infra edits outside task scope."""

from __future__ import annotations

from agentlint.models import CheckResult, Diff

from ._common import extract_keywords, has_keyword_match, iter_changed_files

_SENSITIVE_MARKERS = [
    ".github/workflows/",
    ".gitlab-ci.yml",
    ".circleci/",
    "jenkinsfile",
    "terraform/",
    "/k8s/",
    "/helm/",
    "docker-compose",
    "poetry.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "cargo.lock",
]


def _is_sensitive(path: str) -> bool:
    lowered = path.casefold()
    if lowered.endswith(".tf"):
        return True
    return any(marker in lowered for marker in _SENSITIVE_MARKERS)


def run(diff: Diff, task_description: str | None = None) -> list[CheckResult]:
    keywords = extract_keywords(task_description)

    findings: list[CheckResult] = []
    for file_diff in iter_changed_files(diff):
        if not _is_sensitive(file_diff.path):
            continue

        if keywords and has_keyword_match(file_diff.path, keywords):
            continue

        findings.append(
            CheckResult(
                check_id="config_vandalism",
                severity="warning",
                file_path=file_diff.path,
                message="Sensitive CI/config/infrastructure file changed outside task scope",
            )
        )

    return findings
