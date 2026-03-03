"""Core data models for parsed diffs and lint findings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["error", "warning", "info"]
SEVERITY_ORDER: dict[Severity, int] = {"error": 0, "warning": 1, "info": 2}


@dataclass(slots=True, frozen=True)
class CheckResult:
    """A single issue emitted by a check module."""

    check_id: str
    message: str
    severity: Severity
    file_path: str | None = None
    line: int | None = None
    hint: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "check_id": self.check_id,
            "severity": self.severity,
            "message": self.message,
            "file": self.file_path,
            "line": self.line,
            "hint": self.hint,
        }


@dataclass(slots=True, frozen=True)
class DiffLine:
    """A single line within a diff hunk."""

    prefix: Literal["+", "-", " "]
    content: str
    old_lineno: int | None
    new_lineno: int | None

    @property
    def is_addition(self) -> bool:
        return self.prefix == "+"

    @property
    def is_deletion(self) -> bool:
        return self.prefix == "-"


@dataclass(slots=True)
class Hunk:
    """A parsed hunk from unified diff format."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    header: str = ""
    lines: list[DiffLine] = field(default_factory=list)


@dataclass(slots=True)
class FileDiff:
    """A changed file in a unified diff."""

    old_path: str | None = None
    new_path: str | None = None
    path: str = ""
    is_new: bool = False
    is_deleted: bool = False
    is_rename: bool = False
    is_binary: bool = False
    hunks: list[Hunk] = field(default_factory=list)
    added_lines: int = 0
    deleted_lines: int = 0

    def all_lines(self) -> list[DiffLine]:
        return [line for hunk in self.hunks for line in hunk.lines]

    def added_content(self) -> list[tuple[int | None, str]]:
        out: list[tuple[int | None, str]] = []
        for line in self.all_lines():
            if line.is_addition:
                out.append((line.new_lineno, line.content))
        return out

    def deleted_content(self) -> list[tuple[int | None, str]]:
        out: list[tuple[int | None, str]] = []
        for line in self.all_lines():
            if line.is_deletion:
                out.append((line.old_lineno, line.content))
        return out


@dataclass(slots=True)
class Diff:
    """A parsed unified diff."""

    files: list[FileDiff] = field(default_factory=list)
    raw_text: str = ""

    @property
    def changed_paths(self) -> list[str]:
        return [file.path for file in self.files]
