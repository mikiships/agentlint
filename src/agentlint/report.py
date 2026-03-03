"""Result formatting and reporting utilities."""

from __future__ import annotations

import json
from collections import defaultdict
from io import StringIO

from rich.console import Console
from rich.table import Table

from .engine import summarize_findings
from .models import CheckResult


def summarize(findings: list[CheckResult]) -> dict[str, int]:
    return summarize_findings(findings)


def summarize_by_file(findings: list[CheckResult]) -> dict[str, dict[str, int]]:
    per_file: dict[str, dict[str, int]] = defaultdict(lambda: {"error": 0, "warning": 0, "info": 0})
    for finding in findings:
        file_key = finding.file_path or "<unknown>"
        per_file[file_key][finding.severity] += 1

    return dict(sorted(per_file.items(), key=lambda item: item[0]))


def _table_for_findings(findings: list[CheckResult], quiet: bool) -> Table:
    table = Table(show_header=not quiet)
    if not quiet:
        table.title = "agentlint findings"

    table.add_column("severity")
    table.add_column("check")
    table.add_column("file")
    table.add_column("line", justify="right")
    table.add_column("message")

    for finding in findings:
        table.add_row(
            finding.severity,
            finding.check_id,
            finding.file_path or "",
            str(finding.line or ""),
            finding.message,
        )
    return table


def _table_for_files(per_file: dict[str, dict[str, int]], quiet: bool) -> Table:
    table = Table(show_header=not quiet)
    if not quiet:
        table.title = "per-file summary"

    table.add_column("file")
    table.add_column("errors", justify="right")
    table.add_column("warnings", justify="right")
    table.add_column("info", justify="right")

    for file_path, counts in per_file.items():
        table.add_row(
            file_path,
            str(counts["error"]),
            str(counts["warning"]),
            str(counts["info"]),
        )
    return table


def render_table(findings: list[CheckResult], quiet: bool = False) -> str:
    summary = summarize(findings)
    per_file = summarize_by_file(findings)

    if quiet:
        lines = [f"errors={summary['error']} warnings={summary['warning']} info={summary['info']}"]
        for finding in findings:
            location = finding.file_path or ""
            if finding.line:
                location = f"{location}:{finding.line}"
            lines.append(f"{finding.severity}\t{finding.check_id}\t{location}\t{finding.message}")
        if per_file:
            lines.append("files")
            for path, counts in per_file.items():
                lines.append(
                    f"{path}\terrors={counts['error']}\twarnings={counts['warning']}\tinfo={counts['info']}"
                )
        return "\n".join(lines)

    output = StringIO()
    console = Console(file=output, force_terminal=False, color_system=None, width=120)
    console.print(f"errors={summary['error']} warnings={summary['warning']} info={summary['info']}")
    console.print(_table_for_findings(findings, quiet=False))
    console.print(_table_for_files(per_file, quiet=False))
    return output.getvalue().rstrip()


def render_json(findings: list[CheckResult]) -> str:
    summary = summarize(findings)
    per_file = summarize_by_file(findings)
    payload = {
        "summary": summary,
        "files": per_file,
        "results": [finding.to_dict() for finding in findings],
    }
    return json.dumps(payload, sort_keys=True, indent=2)


def _gha_escape(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def render_github(findings: list[CheckResult]) -> str:
    lines: list[str] = []
    for finding in findings:
        level = "notice"
        if finding.severity == "error":
            level = "error"
        elif finding.severity == "warning":
            level = "warning"

        fields = []
        if finding.file_path:
            fields.append(f"file={_gha_escape(finding.file_path)}")
        if finding.line is not None:
            fields.append(f"line={finding.line}")

        field_text = ",".join(fields)
        message = _gha_escape(f"{finding.message} [{finding.check_id}]")
        if field_text:
            lines.append(f"::{level} {field_text}::{message}")
        else:
            lines.append(f"::{level}::{message}")

    summary = summarize(findings)
    lines.append(
        f"::notice::agentlint summary errors={summary['error']} warnings={summary['warning']} info={summary['info']}"
    )
    return "\n".join(lines)


def render(findings: list[CheckResult], output_format: str, quiet: bool = False) -> str:
    if output_format == "json":
        return render_json(findings)
    if output_format == "github":
        return render_github(findings)
    return render_table(findings, quiet=quiet)
