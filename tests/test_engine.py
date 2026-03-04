from __future__ import annotations

import types

from agentlint.engine import (
    LintEngine,
    discover_check_modules,
    exit_code_for_findings,
    summarize_findings,
)
from agentlint.models import CheckResult, Diff


class DummyConfig:
    def __init__(self, disabled_checks=None, severity_overrides=None, check_ignores=None):
        self.disabled_checks = disabled_checks or []
        self.severity_overrides = severity_overrides or {}
        self.check_ignores = check_ignores or {}


def test_discover_check_modules_sorted() -> None:
    discovered = discover_check_modules("tests.fake_checks")
    assert discovered == sorted(discovered)
    assert "tests.fake_checks.error_check" in discovered


def test_engine_runs_checks_and_sorts_by_severity() -> None:
    engine = LintEngine(
        [
            "tests.fake_checks.info_check",
            "tests.fake_checks.warn_check",
            "tests.fake_checks.error_check",
        ]
    )
    findings = engine.run(Diff(files=[]))
    assert [f.severity for f in findings] == ["error", "warning", "info"]


def test_engine_respects_disabled_checks() -> None:
    engine = LintEngine(["tests.fake_checks.warn_check"])
    findings = engine.run(Diff(files=[]), config=DummyConfig(disabled_checks=["warn_check"]))
    assert findings == []


def test_engine_applies_severity_override() -> None:
    engine = LintEngine(["tests.fake_checks.warn_check"])
    findings = engine.run(
        Diff(files=[]),
        config=DummyConfig(severity_overrides={"warn_check": "error"}),
    )
    assert findings[0].severity == "error"


def test_engine_applies_ignore_patterns() -> None:
    engine = LintEngine(["tests.fake_checks.warn_check"])
    findings = engine.run(
        Diff(files=[]),
        config=DummyConfig(check_ignores={"warn_check": ["src/*.py"]}),
    )
    assert findings == []


def test_engine_skips_modules_without_run(monkeypatch) -> None:
    module_name = "tests.fake_checks.no_runner"
    mod = types.ModuleType(module_name)
    monkeypatch.setitem(__import__("sys").modules, module_name, mod)
    engine = LintEngine([module_name])
    assert engine.run(Diff(files=[])) == []


def test_summarize_findings() -> None:
    findings = [
        CheckResult("a", "m", "error"),
        CheckResult("b", "m", "warning"),
        CheckResult("c", "m", "info"),
        CheckResult("d", "m", "warning"),
    ]
    assert summarize_findings(findings) == {"error": 1, "warning": 2, "info": 1}


def test_exit_code_for_findings_warning_threshold() -> None:
    findings = [CheckResult("b", "m", "warning")]
    assert exit_code_for_findings(findings, fail_on="warning") == 1


def test_exit_code_for_findings_error_threshold() -> None:
    findings = [CheckResult("b", "m", "warning")]
    assert exit_code_for_findings(findings, fail_on="error") == 0


def test_exit_code_for_findings_error_always_wins() -> None:
    findings = [CheckResult("a", "m", "error")]
    assert exit_code_for_findings(findings, fail_on="error") == 1
