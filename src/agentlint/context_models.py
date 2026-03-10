"""Data models for the check-context command."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ContextSeverity = Literal["error", "warning", "info"]
CONTEXT_SEVERITY_ORDER: dict[ContextSeverity, int] = {"error": 0, "warning": 1, "info": 2}
CONTEXT_SEVERITY_DEDUCT: dict[ContextSeverity, int] = {"error": 15, "warning": 5, "info": 2}


@dataclass(slots=True, frozen=True)
class ContextFinding:
    """A single issue found in a context file."""

    check_id: str
    severity: ContextSeverity
    message: str
    line_number: int | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "check_id": self.check_id,
            "severity": self.severity,
            "message": self.message,
            "line_number": self.line_number,
        }


@dataclass(slots=True)
class ContextReport:
    """Aggregated result of running check-context on a file."""

    file_path: str
    freshness_score: int
    findings: list[ContextFinding] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "info")

    def to_dict(self) -> dict[str, object]:
        return {
            "file": self.file_path,
            "freshness_score": self.freshness_score,
            "findings": [f.to_dict() for f in self.findings],
        }
