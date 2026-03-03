from __future__ import annotations

from agentlint.parser import parse_unified_diff


def make_diff(
    path: str,
    *,
    added: list[str] | None = None,
    deleted: list[str] | None = None,
    header: str | None = None,
) -> str:
    added = added or []
    deleted = deleted or []
    old_count = max(1, len(deleted))
    new_count = max(1, len(added))
    hunk_lines = [f"-{line}" for line in deleted] + [f"+{line}" for line in added]
    body = "\n".join(hunk_lines) if hunk_lines else " line"

    extra = f"{header}\n" if header else ""
    return (
        f"diff --git a/{path} b/{path}\n"
        f"{extra}"
        f"--- a/{path}\n"
        f"+++ b/{path}\n"
        f"@@ -1,{old_count} +1,{new_count} @@\n"
        f"{body}\n"
    )


def parse_diff_text(text: str):
    return parse_unified_diff(text)
