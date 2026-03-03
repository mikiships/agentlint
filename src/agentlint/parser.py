"""Unified diff parser used by agentlint checks."""

from __future__ import annotations

import re

from .models import Diff, DiffLine, FileDiff, Hunk

_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def _strip_git_prefix(path: str) -> str:
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path


def _parse_hunk_header(line: str) -> tuple[int, int, int, int, str] | None:
    match = _HUNK_RE.match(line)
    if not match:
        return None
    old_start = int(match.group(1))
    old_count = int(match.group(2) or 1)
    new_start = int(match.group(3))
    new_count = int(match.group(4) or 1)
    heading = match.group(5).strip()
    return old_start, old_count, new_start, new_count, heading


def parse_unified_diff(text: str) -> Diff:
    """Parse unified diff text into structured file/hunk/line objects."""

    lines = text.splitlines()
    parsed = Diff(raw_text=text)

    current_file: FileDiff | None = None
    current_hunk: Hunk | None = None
    old_lineno = 0
    new_lineno = 0

    def flush_file() -> None:
        nonlocal current_file, current_hunk
        if current_file is None:
            return
        if not current_file.path:
            current_file.path = current_file.new_path or current_file.old_path or ""
        parsed.files.append(current_file)
        current_file = None
        current_hunk = None

    for line in lines:
        if line.startswith("diff --git "):
            flush_file()
            parts = line.split()
            old_path = _strip_git_prefix(parts[2]) if len(parts) > 2 else None
            new_path = _strip_git_prefix(parts[3]) if len(parts) > 3 else None
            current_file = FileDiff(old_path=old_path, new_path=new_path, path=new_path or old_path or "")
            continue

        if current_file is None:
            if line.startswith("--- "):
                current_file = FileDiff(old_path=_strip_git_prefix(line[4:].strip()))
            else:
                continue

        if line.startswith("new file mode "):
            current_file.is_new = True
            continue
        if line.startswith("deleted file mode "):
            current_file.is_deleted = True
            continue
        if line.startswith("rename from "):
            current_file.is_rename = True
            current_file.old_path = line[len("rename from ") :].strip()
            if not current_file.path:
                current_file.path = current_file.old_path
            continue
        if line.startswith("rename to "):
            current_file.is_rename = True
            current_file.new_path = line[len("rename to ") :].strip()
            current_file.path = current_file.new_path
            continue
        if line.startswith("Binary files ") and line.endswith(" differ"):
            current_file.is_binary = True
            continue
        if line == "GIT binary patch":
            current_file.is_binary = True
            continue

        if line.startswith("--- "):
            path = line[4:].strip()
            if path != "/dev/null":
                current_file.old_path = _strip_git_prefix(path)
            continue

        if line.startswith("+++ "):
            path = line[4:].strip()
            if path != "/dev/null":
                current_file.new_path = _strip_git_prefix(path)
                current_file.path = current_file.new_path
            continue

        hunk_meta = _parse_hunk_header(line)
        if hunk_meta is not None:
            old_start, old_count, new_start, new_count, heading = hunk_meta
            current_hunk = Hunk(
                old_start=old_start,
                old_count=old_count,
                new_start=new_start,
                new_count=new_count,
                header=heading,
            )
            current_file.hunks.append(current_hunk)
            old_lineno = old_start
            new_lineno = new_start
            continue

        if current_hunk is None:
            continue

        if line.startswith("\\ No newline at end of file"):
            continue

        if not line:
            prefix = " "
            content = ""
        else:
            prefix = line[0]
            content = line[1:]

        if prefix == "+":
            current_hunk.lines.append(
                DiffLine(prefix="+", content=content, old_lineno=None, new_lineno=new_lineno)
            )
            current_file.added_lines += 1
            new_lineno += 1
        elif prefix == "-":
            current_hunk.lines.append(
                DiffLine(prefix="-", content=content, old_lineno=old_lineno, new_lineno=None)
            )
            current_file.deleted_lines += 1
            old_lineno += 1
        elif prefix == " ":
            current_hunk.lines.append(
                DiffLine(
                    prefix=" ",
                    content=content,
                    old_lineno=old_lineno,
                    new_lineno=new_lineno,
                )
            )
            old_lineno += 1
            new_lineno += 1
        else:
            # Unknown line type in hunk; preserve as context.
            current_hunk.lines.append(
                DiffLine(
                    prefix=" ",
                    content=line,
                    old_lineno=old_lineno,
                    new_lineno=new_lineno,
                )
            )
            old_lineno += 1
            new_lineno += 1

    flush_file()
    return parsed
