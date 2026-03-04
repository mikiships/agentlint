from __future__ import annotations

import json

import pytest

from agentlint.formatters import render_markdown
from agentlint.models import CheckResult
from agentlint.report import render_json


def _result(
    check_id: str,
    severity: str,
    *,
    file_path: str | None = "src/a.py",
    line: int | None = 1,
    message: str = "issue",
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        severity=severity,  # type: ignore[arg-type]
        message=message,
        file_path=file_path,
        line=line,
    )


@pytest.mark.parametrize(
    ("findings", "expected_summary"),
    [
        pytest.param([], {"total": 0, "by_severity": {"error": 0, "warning": 0, "info": 0}}, id="empty"),
        pytest.param(
            [_result("secret_leak", "error")],
            {"total": 1, "by_severity": {"error": 1, "warning": 0, "info": 0}},
            id="single-error",
        ),
        pytest.param(
            [_result("todo_bombs", "warning")],
            {"total": 1, "by_severity": {"error": 0, "warning": 1, "info": 0}},
            id="single-warning",
        ),
        pytest.param(
            [_result("note", "info")],
            {"total": 1, "by_severity": {"error": 0, "warning": 0, "info": 1}},
            id="single-info",
        ),
        pytest.param(
            [_result("secret_leak", "error"), _result("todo_bombs", "warning")],
            {"total": 2, "by_severity": {"error": 1, "warning": 1, "info": 0}},
            id="error-warning",
        ),
        pytest.param(
            [
                _result("secret_leak", "error"),
                _result("todo_bombs", "warning"),
                _result("scope_drift", "warning"),
            ],
            {"total": 3, "by_severity": {"error": 1, "warning": 2, "info": 0}},
            id="error-two-warning",
        ),
        pytest.param(
            [_result("note", "info"), _result("scope_drift", "warning"), _result("secret_leak", "error")],
            {"total": 3, "by_severity": {"error": 1, "warning": 1, "info": 1}},
            id="all-severities",
        ),
        pytest.param(
            [_result("scope_drift", "warning"), _result("scope_drift", "warning"), _result("scope_drift", "warning")],
            {"total": 3, "by_severity": {"error": 0, "warning": 3, "info": 0}},
            id="same-check-repeat",
        ),
    ],
)
def test_json_summary_contract_matrix(
    findings: list[CheckResult], expected_summary: dict[str, object]
) -> None:
    payload = json.loads(
        render_json(findings, tool_version="0.2.0", timestamp="2026-03-04T00:00:00Z")
    )
    assert payload["summary"] == expected_summary


@pytest.mark.parametrize(
    "finding",
    [
        pytest.param(
            _result("secret_leak", "error", file_path="src/security.py", line=12, message="secret"),
            id="error-with-location",
        ),
        pytest.param(
            _result("todo_bombs", "warning", file_path="src/app.py", line=44, message="todo spike"),
            id="warning-with-location",
        ),
        pytest.param(
            _result("note", "info", file_path="docs/readme.md", line=2, message="note"),
            id="info-with-location",
        ),
        pytest.param(
            _result("scope_drift", "warning", file_path=None, line=None, message="off task"),
            id="no-location",
        ),
        pytest.param(
            _result("dependency_injection", "warning", file_path="requirements.txt", line=8, message="new dep"),
            id="requirements-path",
        ),
        pytest.param(
            _result("permission_escalation", "error", file_path="scripts/run.sh", line=1, message="sudo use"),
            id="shell-path",
        ),
    ],
)
def test_json_finding_object_contract(finding: CheckResult) -> None:
    payload = json.loads(
        render_json([finding], tool_version="0.2.0", timestamp="2026-03-04T00:00:00Z")
    )
    row = payload["findings"][0]
    assert row == {
        "severity": finding.severity,
        "check": finding.check_id,
        "file": finding.file_path,
        "line": finding.line,
        "message": finding.message,
    }


@pytest.mark.parametrize(
    ("findings", "expected_rows"),
    [
        pytest.param([], ["| `-` | `-` | 0 |"], id="empty"),
        pytest.param(
            [_result("secret_leak", "error")],
            ["| `secret_leak` | `error` | 1 |"],
            id="single-error-row",
        ),
        pytest.param(
            [_result("todo_bombs", "warning"), _result("todo_bombs", "warning")],
            ["| `todo_bombs` | `warning` | 2 |"],
            id="warning-aggregation",
        ),
        pytest.param(
            [_result("note", "info")],
            ["| `note` | `info` | 1 |"],
            id="single-info-row",
        ),
        pytest.param(
            [_result("scope_drift", "warning"), _result("secret_leak", "error")],
            ["| `secret_leak` | `error` | 1 |", "| `scope_drift` | `warning` | 1 |"],
            id="multi-severity-rows",
        ),
        pytest.param(
            [
                _result("scope_drift", "warning"),
                _result("scope_drift", "warning"),
                _result("note", "info"),
            ],
            ["| `scope_drift` | `warning` | 2 |", "| `note` | `info` | 1 |"],
            id="multiple-checks",
        ),
    ],
)
def test_markdown_summary_table_matrix(findings: list[CheckResult], expected_rows: list[str]) -> None:
    text = render_markdown(findings)
    assert "| Check | Severity | Count |" in text
    for row in expected_rows:
        assert row in text


@pytest.mark.parametrize(
    ("file_path", "line"),
    [
        pytest.param("src/a.py", 1, id="python-file"),
        pytest.param("docs/readme.md", 2, id="docs-file"),
        pytest.param("requirements.txt", 3, id="requirements-file"),
        pytest.param("scripts/run.sh", 4, id="shell-file"),
        pytest.param("pkg/module.py", None, id="line-missing"),
        pytest.param(None, None, id="unknown-file"),
    ],
)
def test_markdown_file_grouping_matrix(file_path: str | None, line: int | None) -> None:
    finding = _result("scope_drift", "warning", file_path=file_path, line=line, message="issue")
    text = render_markdown([finding])
    expected_path = file_path or "<unknown>"
    assert f"<details><summary><code>{expected_path}</code> (1 findings)</summary>" in text
    assert f"`warning` `scope_drift` `{expected_path}" in text
