"""Detect dangerous MCP (Model Context Protocol) permission configurations in diffs.

Flags patterns that could allow agents to perform unauthorized actions,
including the auto-approve bypass pattern associated with CVE-2026-21852.
"""

from __future__ import annotations

import json
import re

from agentlint.models import CheckResult, Diff

from ._common import iter_added_lines

# Files likely to contain MCP configuration
_MCP_CONFIG_PATHS = re.compile(
    r"(?:^|/)(?:\.mcp\.json|claude(?:_desktop)?_config\.json|mcp(?:_config)?\.json)$",
    re.IGNORECASE,
)

# Patterns within diff lines that indicate dangerous permission settings
_DANGEROUS_LINE_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "auto_approve_wildcard",
        "MCP autoApprove set to wildcard '*' — grants all tools unrestricted approval",
        re.compile(r'"autoApprove"\s*:\s*\[\s*"\*"\s*\]'),
    ),
    (
        "auto_approve_true",
        "MCP autoApprove set to boolean true — bypasses per-tool approval prompts",
        re.compile(r'"autoApprove"\s*:\s*true'),
    ),
    (
        "trust_all",
        "MCP trust level set to 'all' — grants unrestricted trust to server",
        re.compile(r'"trust(?:Level)?"\s*:\s*"all"'),
    ),
    (
        "allow_dangerous_root",
        "MCP filesystem root grants access to system root '/' — overly broad path access",
        re.compile(r'"roots?"\s*:\s*\[\s*(?:"/"|\{"uri"\s*:\s*"file:///"\})\s*\]'),
    ),
]


def _is_mcp_config_file(path: str) -> bool:
    return bool(_MCP_CONFIG_PATHS.search(path))


def _validate_mcp_json_block(raw_json: str, file_path: str) -> list[CheckResult]:
    """Parse a complete JSON block and check for structural violations."""
    findings: list[CheckResult] = []
    try:
        config = json.loads(raw_json)
    except json.JSONDecodeError:
        return findings

    servers = {}
    if isinstance(config, dict):
        servers = config.get("mcpServers", config.get("servers", {}))

    if not isinstance(servers, dict):
        return findings

    for server_name, server_config in servers.items():
        if not isinstance(server_config, dict):
            continue

        auto_approve = server_config.get("autoApprove")

        # autoApprove: true (boolean)
        if auto_approve is True:
            findings.append(
                CheckResult(
                    check_id="mcp_permissions",
                    severity="error",
                    file_path=file_path,
                    line=None,
                    message=(
                        f"MCP server '{server_name}': autoApprove=true bypasses "
                        "per-tool approval prompts for all tools"
                    ),
                    hint="Set autoApprove to an explicit list of safe tool names, or remove it.",
                )
            )

        # autoApprove: ["*"] (wildcard list)
        elif isinstance(auto_approve, list) and "*" in auto_approve:
            findings.append(
                CheckResult(
                    check_id="mcp_permissions",
                    severity="error",
                    file_path=file_path,
                    line=None,
                    message=(
                        f"MCP server '{server_name}': autoApprove includes wildcard '*' — "
                        "all tools auto-approved without prompting"
                    ),
                    hint="Replace '*' with an explicit list of tools that are safe to auto-approve.",
                )
            )

    return findings


def run(diff: Diff, task_description: str | None = None, config: object | None = None) -> list[CheckResult]:
    del task_description, config

    findings: list[CheckResult] = []

    # Track accumulated lines per MCP config file for structural validation
    accumulated: dict[str, list[str]] = {}

    for file_diff, line_no, content in iter_added_lines(diff):
        path = file_diff.path or ""

        # 1. Collect MCP config file lines for JSON parsing
        if _is_mcp_config_file(path):
            accumulated.setdefault(path, []).append(content)

        # 2. Check for dangerous patterns in any file (MCP config or inline strings)
        for check_name, message, pattern in _DANGEROUS_LINE_PATTERNS:
            if pattern.search(content):
                findings.append(
                    CheckResult(
                        check_id="mcp_permissions",
                        severity="error",
                        file_path=file_diff.path,
                        line=line_no,
                        message=message,
                        hint=f"Pattern: {check_name}",
                    )
                )
                break  # one finding per line

    # 3. Try structural JSON validation on accumulated MCP config files
    for file_path, lines in accumulated.items():
        raw = "\n".join(lines)
        json_findings = _validate_mcp_json_block(raw, file_path)
        # Deduplicate: skip if same file + message already reported via line patterns
        existing_messages = {f.message for f in findings if f.file_path == file_path}
        for finding in json_findings:
            if finding.message not in existing_messages:
                findings.append(finding)

    return findings
