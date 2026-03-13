"""Core engine for the check-context command.

Validates AGENTS.md / CLAUDE.md / GEMINI.md context files for staleness,
bloat, and conflicts — without requiring a git diff.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .context_models import (
    CONTEXT_SEVERITY_DEDUCT,
    ContextFinding,
    ContextReport,
)

# Files to auto-detect, in priority order
CONTEXT_FILE_NAMES = ["AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursorrules"]

# Regexes
_PATH_RE = re.compile(r"(?:^|[\s`'\"])([./~][^\s`'\"<>{}|\\^[\]]*[a-zA-Z0-9_/.-])")
_NPM_SCRIPT_RE = re.compile(r"npm\s+run\s+([a-zA-Z0-9:_-]+)")
_TODO_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
_YEAR_RE = re.compile(r"\b(202[0-3])\b")
_TEST_CMD_RE = re.compile(r"(npm\s+run\s+[a-zA-Z0-9:_-]+|pytest(?:\s+[^\s]+)?|cargo\s+test)")


def _auto_detect_context_file(search_dir: Path) -> Path | None:
    """Return the first context file found in search_dir, or None."""
    for name in CONTEXT_FILE_NAMES:
        candidate = search_dir / name
        if candidate.exists():
            return candidate
    return None


class ContextChecker:
    """Runs all 6 context-file checks and returns a ContextReport."""

    def __init__(self, file_path: Path, repo_root: Path | None = None) -> None:
        self.file_path = file_path
        self.repo_root = repo_root or file_path.parent

    def run(self) -> ContextReport:
        content = self.file_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()

        findings: list[ContextFinding] = []
        findings.extend(self._check_path_rot(lines))
        findings.extend(self._check_script_rot(lines))
        findings.extend(self._check_bloat(content))
        findings.extend(self._check_stale_todos(lines))
        findings.extend(self._check_year_rot(lines))
        findings.extend(self._check_multi_file_conflict(content))

        score = 100
        for f in findings:
            score -= CONTEXT_SEVERITY_DEDUCT[f.severity]
        score = max(0, score)

        return ContextReport(
            file_path=self.file_path.name,
            freshness_score=score,
            findings=findings,
        )

    # ------------------------------------------------------------------
    # CTX001: path-rot
    # ------------------------------------------------------------------
    def _check_path_rot(self, lines: list[str]) -> list[ContextFinding]:
        findings: list[ContextFinding] = []
        seen: set[str] = set()
        for lineno, line in enumerate(lines, start=1):
            for match in _PATH_RE.finditer(line):
                raw = match.group(1).rstrip(".,;:)")
                if raw in seen:
                    continue
                seen.add(raw)
                # Skip bare file extensions (e.g. ".py", ".md") — not paths
                if re.fullmatch(r"\.[a-zA-Z0-9]+", raw):
                    continue
                # Skip CLI slash-commands (e.g. "/compact", "/review") — not filesystem paths
                if re.fullmatch(r"/[a-z][a-z_-]*", raw):
                    continue
                # Expand ~ to home
                expanded = Path(raw.replace("~", str(Path.home())))
                if not expanded.is_absolute():
                    expanded = self.repo_root / expanded
                if not expanded.exists():
                    findings.append(
                        ContextFinding(
                            check_id="CTX001",
                            severity="warning",
                            message=f"path-rot: {raw} does not exist",
                            line_number=lineno,
                        )
                    )
        return findings

    # ------------------------------------------------------------------
    # CTX002: script-rot
    # ------------------------------------------------------------------
    def _check_script_rot(self, lines: list[str]) -> list[ContextFinding]:
        package_json = self.repo_root / "package.json"
        if not package_json.exists():
            return []

        try:
            pkg = json.loads(package_json.read_text(encoding="utf-8"))
            known_scripts: set[str] = set((pkg.get("scripts") or {}).keys())
        except (json.JSONDecodeError, OSError):
            return []

        findings: list[ContextFinding] = []
        seen: set[str] = set()
        for lineno, line in enumerate(lines, start=1):
            for match in _NPM_SCRIPT_RE.finditer(line):
                script = match.group(1)
                if script in seen:
                    continue
                seen.add(script)
                if script not in known_scripts:
                    findings.append(
                        ContextFinding(
                            check_id="CTX002",
                            severity="warning",
                            message=f"script-rot: `npm run {script}` not found in package.json scripts",
                            line_number=lineno,
                        )
                    )
        return findings

    # ------------------------------------------------------------------
    # CTX003: bloat
    # ------------------------------------------------------------------
    def _check_bloat(self, content: str) -> list[ContextFinding]:
        char_count = len(content)
        if char_count > 15_000:
            k = char_count / 1000
            return [
                ContextFinding(
                    check_id="CTX003",
                    severity="error",
                    message=(
                        f"bloat: {k:.1f}k chars — adds ~20% token overhead per ETH Zurich ICSE 2026 study"
                    ),
                )
            ]
        if char_count > 8_000:
            k = char_count / 1000
            return [
                ContextFinding(
                    check_id="CTX003",
                    severity="warning",
                    message=(
                        f"bloat: {k:.1f}k chars — consider --minimal mode in agentmd to reduce size"
                    ),
                )
            ]
        return []

    # ------------------------------------------------------------------
    # CTX004: stale-todos
    # ------------------------------------------------------------------
    def _check_stale_todos(self, lines: list[str]) -> list[ContextFinding]:
        findings: list[ContextFinding] = []
        for lineno, line in enumerate(lines, start=1):
            match = _TODO_RE.search(line)
            if match:
                tag = match.group(1)
                findings.append(
                    ContextFinding(
                        check_id="CTX004",
                        severity="info",
                        message=f"stale-todos: Unresolved {tag} at line {lineno} may confuse agents",
                        line_number=lineno,
                    )
                )
        return findings

    # ------------------------------------------------------------------
    # CTX005: year-rot
    # ------------------------------------------------------------------
    def _check_year_rot(self, lines: list[str]) -> list[ContextFinding]:
        findings: list[ContextFinding] = []
        for lineno, line in enumerate(lines, start=1):
            for match in _YEAR_RE.finditer(line):
                year = match.group(1)
                findings.append(
                    ContextFinding(
                        check_id="CTX005",
                        severity="warning",
                        message=(
                            f"year-rot: Year reference {year} may be stale — "
                            "agents may interpret as outdated guidance"
                        ),
                        line_number=lineno,
                    )
                )
        return findings

    # ------------------------------------------------------------------
    # CTX006: multi-file-conflict
    # ------------------------------------------------------------------
    def _check_multi_file_conflict(self, _content: str) -> list[ContextFinding]:
        present = [
            self.repo_root / name
            for name in CONTEXT_FILE_NAMES
            if (self.repo_root / name).exists()
        ]
        if len(present) < 2:
            return [
                ContextFinding(
                    check_id="CTX006",
                    severity="info",
                    message="multi-file-conflict: only one context file found — no conflicts possible",
                )
            ]

        # Extract primary test commands from each file
        file_cmds: dict[str, set[str]] = {}
        for p in present:
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            cmds: set[str] = set()
            for match in _TEST_CMD_RE.finditer(text):
                cmds.add(match.group(1).strip())
            file_cmds[p.name] = cmds

        # Check for conflicting commands across files
        all_cmds: list[tuple[str, str]] = []
        for fname, cmds in file_cmds.items():
            for cmd in cmds:
                all_cmds.append((fname, cmd))

        if len(file_cmds) < 2:
            return []

        names = list(file_cmds.keys())
        findings: list[ContextFinding] = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a_name, b_name = names[i], names[j]
                a_cmds = file_cmds.get(a_name, set())
                b_cmds = file_cmds.get(b_name, set())
                # Conflict: both have commands but they differ
                if a_cmds and b_cmds and a_cmds != b_cmds:
                    a_sample = next(iter(a_cmds))
                    b_sample = next(iter(b_cmds))
                    findings.append(
                        ContextFinding(
                            check_id="CTX006",
                            severity="warning",
                            message=(
                                f"multi-file-conflict: {a_name} says `{a_sample}` but "
                                f"{b_name} says `{b_sample}` — agents may pick either"
                            ),
                        )
                    )
        return findings
