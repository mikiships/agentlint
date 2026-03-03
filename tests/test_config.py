from __future__ import annotations

from pathlib import Path

import pytest

from agentlint.config import (
    ConfigError,
    RuntimeConfig,
    build_runtime_config,
    discover_config_path,
    load_runtime_config,
)


def test_discover_config_walks_up_tree(tmp_path: Path) -> None:
    config = tmp_path / ".agentlint.toml"
    config.write_text("disabled_checks = []\n", encoding="utf-8")
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)

    found = discover_config_path(start_dir=nested)
    assert found == config


def test_load_runtime_config_returns_defaults_without_file(tmp_path: Path) -> None:
    loaded = load_runtime_config(start_dir=tmp_path)
    assert loaded == RuntimeConfig()


def test_load_runtime_config_from_explicit_path(tmp_path: Path) -> None:
    config = tmp_path / "custom.toml"
    config.write_text(
        """
disabled_checks = ["scope_drift"]

[severity]
todo_bombs = "error"

[ignore]
secret_leak = ["tests/*"]

[secrets]
allowed_patterns = ["dummy_token"]
""",
        encoding="utf-8",
    )

    loaded = load_runtime_config(config_path=config)
    assert loaded.disabled_checks == {"scope_drift"}
    assert loaded.severity_overrides == {"todo_bombs": "error"}
    assert loaded.check_ignores == {"secret_leak": ["tests/*"]}
    assert loaded.secret_allowed_patterns == ["dummy_token"]


def test_no_config_ignores_discovered_file(tmp_path: Path) -> None:
    (tmp_path / ".agentlint.toml").write_text("disabled_checks = [\"x\"]\n", encoding="utf-8")
    loaded = load_runtime_config(start_dir=tmp_path, no_config=True)
    assert loaded == RuntimeConfig()


def test_build_runtime_config_rejects_invalid_severity() -> None:
    with pytest.raises(ConfigError):
        build_runtime_config({"severity": {"scope_drift": "fatal"}})


def test_build_runtime_config_rejects_invalid_ignore_type() -> None:
    with pytest.raises(ConfigError):
        build_runtime_config({"ignore": {"scope_drift": "src/*"}})


def test_build_runtime_config_accepts_dotted_secrets_key() -> None:
    loaded = build_runtime_config({"secrets.allowed_patterns": ["^dummy$"]})
    assert loaded.secret_allowed_patterns == ["^dummy$"]


def test_fallback_inline_parser(monkeypatch, tmp_path: Path) -> None:
    config = tmp_path / ".agentlint.toml"
    config.write_text(
        """
disabled_checks = ["scope_drift"]
[severity]
secret_leak = "warning"
""",
        encoding="utf-8",
    )

    import agentlint.config as config_module

    monkeypatch.setattr(config_module, "tomllib", None)
    loaded = config_module.load_runtime_config(config_path=config)
    assert loaded.disabled_checks == {"scope_drift"}
    assert loaded.severity_overrides == {"secret_leak": "warning"}
