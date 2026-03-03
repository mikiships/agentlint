"""Check discovery and execution engine."""

from __future__ import annotations

import fnmatch
import importlib
import pkgutil
from collections.abc import Iterable
from dataclasses import replace

from .models import SEVERITY_ORDER, CheckResult, Diff


def discover_check_modules(package: str = "agentlint.checks") -> list[str]:
    """Return import paths for check modules in deterministic order."""

    pkg = importlib.import_module(package)
    if not hasattr(pkg, "__path__"):
        return []

    modules: list[str] = []
    for module in pkgutil.iter_modules(pkg.__path__, f"{package}."):
        if module.name.rsplit(".", 1)[-1].startswith("_"):
            continue
        modules.append(module.name)
    modules.sort()
    return modules


class LintEngine:
    """Runs all checks against a parsed diff."""

    def __init__(self, checks: Iterable[str] | None = None) -> None:
        self.checks = list(checks) if checks is not None else discover_check_modules()

    @staticmethod
    def _matches_ignore(file_path: str | None, patterns: list[str]) -> bool:
        if not file_path:
            return False
        for pattern in patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    def run(self, diff: Diff, task_description: str | None = None, config: object | None = None) -> list[CheckResult]:
        disabled_checks = set(getattr(config, "disabled_checks", []))
        severity_overrides = dict(getattr(config, "severity_overrides", {}))
        check_ignores = dict(getattr(config, "check_ignores", {}))

        findings: list[CheckResult] = []
        for module_name in self.checks:
            check_id = module_name.rsplit(".", 1)[-1]
            if check_id in disabled_checks:
                continue

            module = importlib.import_module(module_name)
            run_fn = getattr(module, "run", None)
            if run_fn is None:
                continue

            try:
                results = run_fn(diff, task_description=task_description, config=config)
            except TypeError:
                results = run_fn(diff, task_description=task_description)
            if not results:
                continue

            for result in results:
                if check_id in severity_overrides:
                    result = replace(result, severity=severity_overrides[check_id])
                if self._matches_ignore(result.file_path, check_ignores.get(check_id, [])):
                    continue
                findings.append(result)

        findings.sort(
            key=lambda item: (
                SEVERITY_ORDER[item.severity],
                item.file_path or "",
                item.line or -1,
                item.check_id,
                item.message,
            )
        )
        return findings


def summarize_findings(findings: list[CheckResult]) -> dict[str, int]:
    counts = {"error": 0, "warning": 0, "info": 0}
    for finding in findings:
        counts[finding.severity] += 1
    return counts


def exit_code_for_findings(findings: list[CheckResult], fail_on: str = "warning") -> int:
    counts = summarize_findings(findings)
    if counts["error"] > 0:
        return 2
    if fail_on == "warning" and counts["warning"] > 0:
        return 1
    return 0
