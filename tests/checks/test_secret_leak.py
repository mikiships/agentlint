from __future__ import annotations

from agentlint.checks import secret_leak
from agentlint.parser import parse_unified_diff

from ._utils import make_diff, parse_diff_text


class DummyConfig:
    def __init__(self, allowed=None):
        self.secret_allowed_patterns = allowed or []


def test_secret_leak_detects_aws_key() -> None:
    diff = parse_diff_text(make_diff("src/a.py", added=["AWS_KEY=AKIA1234567890ABCDEF"]))
    findings = secret_leak.run(diff)
    assert len(findings) == 1
    assert findings[0].severity == "error"


def test_secret_leak_detects_github_token() -> None:
    token = "ghp_" + "a" * 36
    diff = parse_diff_text(make_diff("src/a.py", added=[f"TOKEN='{token}'"]))
    findings = secret_leak.run(diff)
    assert findings and findings[0].check_id == "secret_leak"


def test_secret_leak_detects_credential_assignment() -> None:
    diff = parse_diff_text(make_diff("src/a.py", added=["password = 'supersecret123' "]))
    assert len(secret_leak.run(diff)) == 1


def test_secret_leak_detects_private_key() -> None:
    diff = parse_diff_text(
        make_diff("keys/id_rsa", added=["-----BEGIN RSA PRIVATE KEY-----", "abc", "-----END RSA PRIVATE KEY-----"])
    )
    findings = secret_leak.run(diff)
    assert len(findings) == 1


def test_secret_leak_detects_connection_string() -> None:
    diff = parse_diff_text(make_diff("src/db.py", added=["url='postgres://user:pass@localhost:5432/db' "]))
    assert len(secret_leak.run(diff)) == 1


def test_secret_leak_respects_allowlist() -> None:
    diff = parse_diff_text(make_diff("src/a.py", added=["password = 'supersecret123'"]))
    findings = secret_leak.run(diff, config=DummyConfig(allowed=["supersecret123"]))
    assert findings == []


def test_secret_leak_ignores_binary_files() -> None:
    text = """diff --git a/image.png b/image.png
Binary files a/image.png and b/image.png differ
"""
    diff = parse_unified_diff(text)
    assert secret_leak.run(diff) == []
