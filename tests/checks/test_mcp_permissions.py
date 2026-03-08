"""Tests for the mcp_permissions check."""

from __future__ import annotations

import json

from agentlint.checks import mcp_permissions

from ._utils import make_diff, parse_diff_text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mcp_diff(path: str, config: dict) -> object:
    """Build a diff that adds a .mcp.json file with the given config dict."""
    raw = json.dumps(config, indent=2)
    lines = raw.splitlines()
    return parse_diff_text(make_diff(path, added=lines))


def _line_diff(path: str, lines: list[str]) -> object:
    return parse_diff_text(make_diff(path, added=lines))


# ---------------------------------------------------------------------------
# File-path detection
# ---------------------------------------------------------------------------

class TestMcpConfigFilePaths:
    def test_dot_mcp_json(self):
        diff = _mcp_diff(".mcp.json", {"mcpServers": {"safe": {"command": "npx"}}})
        # clean config — no findings expected
        assert mcp_permissions.run(diff) == []

    def test_nested_mcp_json(self):
        # A .mcp.json in a subdirectory should still be matched
        diff = _mcp_diff("project/.mcp.json", {"mcpServers": {}})
        assert mcp_permissions.run(diff) == []

    def test_unrelated_json_file_ignored_for_structural_check(self):
        # package.json should not trigger structural JSON parsing
        diff = _line_diff("package.json", ['"name": "my-app"'])
        assert mcp_permissions.run(diff) == []


# ---------------------------------------------------------------------------
# autoApprove: true (boolean)
# ---------------------------------------------------------------------------

class TestAutoApproveTrue:
    def test_detects_auto_approve_true_in_mcp_json(self):
        config = {"mcpServers": {"my-server": {"command": "npx", "autoApprove": True}}}
        diff = _mcp_diff(".mcp.json", config)
        findings = mcp_permissions.run(diff)
        assert any(f.check_id == "mcp_permissions" for f in findings)
        assert any("autoApprove" in f.message for f in findings)

    def test_auto_approve_true_severity_is_error(self):
        config = {"mcpServers": {"srv": {"autoApprove": True}}}
        diff = _mcp_diff(".mcp.json", config)
        findings = mcp_permissions.run(diff)
        assert all(f.severity == "error" for f in findings)

    def test_detects_auto_approve_true_inline_in_any_file(self):
        # Even in a non-config file, an inline pattern should be caught
        diff = _line_diff("scripts/setup.py", ['"autoApprove": true'])
        findings = mcp_permissions.run(diff)
        assert len(findings) >= 1
        assert findings[0].check_id == "mcp_permissions"


# ---------------------------------------------------------------------------
# autoApprove: ["*"] (wildcard)
# ---------------------------------------------------------------------------

class TestAutoApproveWildcard:
    def test_detects_wildcard_in_mcp_json(self):
        config = {"mcpServers": {"srv": {"command": "npx", "autoApprove": ["*"]}}}
        diff = _mcp_diff(".mcp.json", config)
        findings = mcp_permissions.run(diff)
        assert any("wildcard" in f.message.lower() or "*" in f.message for f in findings)

    def test_explicit_tool_list_is_allowed(self):
        config = {"mcpServers": {"srv": {"command": "npx", "autoApprove": ["read_file", "list_dir"]}}}
        diff = _mcp_diff(".mcp.json", config)
        findings = mcp_permissions.run(diff)
        assert findings == []

    def test_empty_auto_approve_list_is_allowed(self):
        config = {"mcpServers": {"srv": {"command": "npx", "autoApprove": []}}}
        diff = _mcp_diff(".mcp.json", config)
        findings = mcp_permissions.run(diff)
        assert findings == []

    def test_wildcard_mixed_with_other_tools_flagged(self):
        config = {"mcpServers": {"srv": {"autoApprove": ["read_file", "*"]}}}
        diff = _mcp_diff(".mcp.json", config)
        findings = mcp_permissions.run(diff)
        # "*" in list is still dangerous
        assert len(findings) >= 1


# ---------------------------------------------------------------------------
# trustLevel: "all"
# ---------------------------------------------------------------------------

class TestTrustLevel:
    def test_detects_trust_all_inline(self):
        diff = _line_diff(".mcp.json", ['"trustLevel": "all"'])
        findings = mcp_permissions.run(diff)
        assert len(findings) >= 1
        assert any("trust" in f.message.lower() for f in findings)

    def test_trust_user_not_flagged(self):
        diff = _line_diff(".mcp.json", ['"trustLevel": "user"'])
        findings = mcp_permissions.run(diff)
        assert findings == []


# ---------------------------------------------------------------------------
# Filesystem root access
# ---------------------------------------------------------------------------

class TestFilesystemRoot:
    def test_detects_root_path_slash(self):
        diff = _line_diff(".mcp.json", ['"roots": ["/"]'])
        findings = mcp_permissions.run(diff)
        assert len(findings) >= 1

    def test_specific_path_not_flagged(self):
        diff = _line_diff(".mcp.json", ['"roots": ["/home/user/project"]'])
        findings = mcp_permissions.run(diff)
        assert findings == []


# ---------------------------------------------------------------------------
# Clean configs — no false positives
# ---------------------------------------------------------------------------

class TestCleanConfigs:
    def test_no_auto_approve_key_is_clean(self):
        config = {"mcpServers": {"srv": {"command": "npx", "args": ["@tool/server"]}}}
        diff = _mcp_diff(".mcp.json", config)
        assert mcp_permissions.run(diff) == []

    def test_multiple_servers_all_clean(self):
        config = {
            "mcpServers": {
                "server1": {"command": "npx", "autoApprove": ["read_file"]},
                "server2": {"command": "python", "args": ["-m", "tool"]},
            }
        }
        diff = _mcp_diff(".mcp.json", config)
        assert mcp_permissions.run(diff) == []

    def test_empty_servers_dict_is_clean(self):
        config = {"mcpServers": {}}
        diff = _mcp_diff(".mcp.json", config)
        assert mcp_permissions.run(diff) == []

    def test_no_mcp_config_key_is_clean(self):
        # config without mcpServers key at all
        config = {"version": "1.0"}
        diff = _mcp_diff(".mcp.json", config)
        assert mcp_permissions.run(diff) == []

    def test_non_mcp_file_with_unrelated_true_value_not_flagged(self):
        diff = _line_diff("config.py", ['SOME_FLAG = True'])
        assert mcp_permissions.run(diff) == []


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_deleted_lines_not_flagged(self):
        raw = json.dumps({"mcpServers": {"srv": {"autoApprove": True}}}, indent=2)
        lines = raw.splitlines()
        diff = parse_diff_text(make_diff(".mcp.json", deleted=lines))
        # Deleted lines should not trigger findings (we only care about additions)
        assert mcp_permissions.run(diff) == []

    def test_multiple_servers_one_dangerous(self):
        config = {
            "mcpServers": {
                "safe": {"command": "npx", "autoApprove": ["read_file"]},
                "dangerous": {"command": "npx", "autoApprove": True},
            }
        }
        diff = _mcp_diff(".mcp.json", config)
        findings = mcp_permissions.run(diff)
        assert len(findings) >= 1
        assert any("dangerous" in f.message for f in findings)

    def test_returns_list(self):
        diff = parse_diff_text(make_diff("main.py", added=["x = 1"]))
        result = mcp_permissions.run(diff)
        assert isinstance(result, list)

    def test_check_id_consistent(self):
        config = {"mcpServers": {"srv": {"autoApprove": True}}}
        diff = _mcp_diff(".mcp.json", config)
        findings = mcp_permissions.run(diff)
        for f in findings:
            assert f.check_id == "mcp_permissions"
