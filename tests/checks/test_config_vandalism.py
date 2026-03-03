from __future__ import annotations

from agentlint.checks import config_vandalism
from agentlint.parser import parse_unified_diff

from ._utils import make_diff, parse_diff_text


def test_config_vandalism_flags_github_workflow_change() -> None:
    diff = parse_diff_text(make_diff(".github/workflows/ci.yml", added=["name: ci"]))
    findings = config_vandalism.run(diff)
    assert len(findings) == 1


def test_config_vandalism_flags_terraform_file() -> None:
    diff = parse_diff_text(make_diff("infra/main.tf", added=["resource \"x\" \"y\" {}"]))
    assert len(config_vandalism.run(diff)) == 1


def test_config_vandalism_flags_lock_file() -> None:
    diff = parse_diff_text(make_diff("poetry.lock", added=["name = \"x\""]))
    assert len(config_vandalism.run(diff)) == 1


def test_config_vandalism_ignores_non_sensitive_file() -> None:
    diff = parse_diff_text(make_diff("src/app.py", added=["print('ok')"]))
    assert config_vandalism.run(diff) == []


def test_config_vandalism_allows_in_scope_task() -> None:
    diff = parse_diff_text(make_diff(".github/workflows/release.yml", added=["name: release"]))
    findings = config_vandalism.run(diff, task_description="update release workflow")
    assert findings == []


def test_config_vandalism_ignores_binary() -> None:
    text = """diff --git a/.github/workflows/ci.png b/.github/workflows/ci.png
Binary files a/.github/workflows/ci.png and b/.github/workflows/ci.png differ
"""
    diff = parse_unified_diff(text)
    assert config_vandalism.run(diff) == []
