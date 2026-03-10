"""Formatters for ContextReport — text, JSON, and Markdown."""

from __future__ import annotations

import json

from .context_models import CONTEXT_SEVERITY_ORDER, ContextReport

_SEVERITY_ICON = {
    "error": "❌",
    "warning": "⚠️ ",
    "info": "ℹ️ ",
}


def _severity_label(s: str) -> str:
    return s.upper().ljust(7)


def format_context_report(report: ContextReport, output_format: str = "text") -> str:
    """Dispatch to the appropriate formatter."""
    fmt = output_format.lower()
    if fmt == "json":
        return _format_json(report)
    if fmt == "markdown":
        return _format_markdown(report)
    return _format_text(report)


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

def _format_text(report: ContextReport) -> str:
    lines: list[str] = [
        f"agentlint context check: {report.file_path}",
        "─" * 45,
    ]

    sorted_findings = sorted(
        report.findings,
        key=lambda f: (CONTEXT_SEVERITY_ORDER[f.severity], f.line_number or 0),
    )

    for f in sorted_findings:
        line_col = f"line {f.line_number}" if f.line_number else "—"
        icon = _SEVERITY_ICON.get(f.severity, " ")
        lines.append(
            f"{f.check_id} {_severity_label(f.severity)} {line_col:<10}  {icon} {f.message}"
        )

    if not sorted_findings:
        lines.append("No issues found.")

    lines.append("")
    lines.append(f"Freshness score: {report.freshness_score}/100")
    total = len(report.findings)
    parts = []
    if report.error_count:
        parts.append(f"{report.error_count} error{'s' if report.error_count > 1 else ''}")
    if report.warning_count:
        parts.append(f"{report.warning_count} warning{'s' if report.warning_count > 1 else ''}")
    if report.info_count:
        parts.append(f"{report.info_count} info")
    summary = ", ".join(parts) if parts else "no issues"
    lines.append(f"{total} finding{'s' if total != 1 else ''} ({summary})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def _format_json(report: ContextReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def _format_markdown(report: ContextReport) -> str:
    lines: list[str] = [
        f"## agentlint context check: `{report.file_path}`",
        "",
    ]

    sorted_findings = sorted(
        report.findings,
        key=lambda f: (CONTEXT_SEVERITY_ORDER[f.severity], f.line_number or 0),
    )

    if sorted_findings:
        lines += [
            "| Check | Severity | Line | Message |",
            "| --- | --- | --- | --- |",
        ]
        for f in sorted_findings:
            line_col = str(f.line_number) if f.line_number else "—"
            lines.append(f"| `{f.check_id}` | `{f.severity}` | {line_col} | {f.message} |")
    else:
        lines.append("No issues found.")

    lines += [
        "",
        f"> **Freshness score: {report.freshness_score}/100**",
    ]
    return "\n".join(lines)
