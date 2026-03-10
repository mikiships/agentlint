"""Unit tests for context_formatters.py."""

from __future__ import annotations

import json

import pytest

from agentlint.context_formatters import format_context_report
from agentlint.context_models import ContextFinding, ContextReport


def make_report(findings=None, score=80):
    return ContextReport(
        file_path="AGENTS.md",
        freshness_score=score,
        findings=findings or [],
    )


def make_finding(check_id="CTX001", severity="warning", message="test msg", line=None):
    return ContextFinding(check_id=check_id, severity=severity, message=message, line_number=line)


# ---------------------------------------------------------------------------
# Text formatter
# ---------------------------------------------------------------------------

class TestTextFormatter:
    def test_contains_file_name(self):
        report = make_report()
        out = format_context_report(report, "text")
        assert "AGENTS.md" in out

    def test_contains_freshness_score(self):
        report = make_report(score=72)
        out = format_context_report(report, "text")
        assert "72/100" in out

    def test_finding_appears_in_output(self):
        f = make_finding(check_id="CTX001", severity="warning", message="path does not exist", line=14)
        report = make_report(findings=[f], score=95)
        out = format_context_report(report, "text")
        assert "CTX001" in out
        assert "WARNING" in out
        assert "14" in out
        assert "path does not exist" in out

    def test_no_findings_message(self):
        report = make_report(findings=[], score=100)
        out = format_context_report(report, "text")
        assert "No issues found" in out

    def test_error_count_in_summary(self):
        f = make_finding(severity="error")
        report = make_report(findings=[f], score=85)
        out = format_context_report(report, "text")
        assert "error" in out.lower()

    def test_deterministic_output(self):
        findings = [
            make_finding("CTX001", "warning", "msg1"),
            make_finding("CTX002", "error", "msg2"),
        ]
        report = make_report(findings=findings, score=80)
        out1 = format_context_report(report, "text")
        out2 = format_context_report(report, "text")
        assert out1 == out2


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------

class TestJsonFormatter:
    def test_valid_json(self):
        report = make_report()
        out = format_context_report(report, "json")
        data = json.loads(out)  # must not raise
        assert isinstance(data, dict)

    def test_json_keys(self):
        report = make_report()
        data = json.loads(format_context_report(report, "json"))
        assert "file" in data
        assert "freshness_score" in data
        assert "findings" in data

    def test_json_finding_structure(self):
        f = make_finding("CTX003", "error", "bloat message", line=None)
        report = make_report(findings=[f], score=70)
        data = json.loads(format_context_report(report, "json"))
        assert len(data["findings"]) == 1
        finding = data["findings"][0]
        assert finding["check_id"] == "CTX003"
        assert finding["severity"] == "error"
        assert finding["message"] == "bloat message"

    def test_json_deterministic(self):
        f = make_finding("CTX001", "warning", "x")
        report = make_report(findings=[f], score=95)
        out1 = format_context_report(report, "json")
        out2 = format_context_report(report, "json")
        assert out1 == out2


# ---------------------------------------------------------------------------
# Markdown formatter
# ---------------------------------------------------------------------------

class TestMarkdownFormatter:
    def test_contains_file_name(self):
        report = make_report()
        out = format_context_report(report, "markdown")
        assert "AGENTS.md" in out

    def test_contains_freshness_score(self):
        report = make_report(score=55)
        out = format_context_report(report, "markdown")
        assert "55/100" in out

    def test_table_headers_present(self):
        f = make_finding()
        report = make_report(findings=[f])
        out = format_context_report(report, "markdown")
        assert "| Check |" in out
        assert "| Severity |" in out

    def test_finding_in_table_row(self):
        f = make_finding("CTX004", "info", "stale todo here", line=5)
        report = make_report(findings=[f])
        out = format_context_report(report, "markdown")
        assert "CTX004" in out
        assert "info" in out
        assert "stale todo here" in out

    def test_no_findings_shows_no_issues(self):
        report = make_report(findings=[])
        out = format_context_report(report, "markdown")
        assert "No issues found" in out
