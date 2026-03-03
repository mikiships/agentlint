"""Configuration loading for agentlint."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import Severity

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

_VALID_SEVERITIES = {"error", "warning", "info"}


@dataclass(slots=True)
class RuntimeConfig:
    """Runtime configuration after file parsing/validation."""

    disabled_checks: set[str] = field(default_factory=set)
    severity_overrides: dict[str, Severity] = field(default_factory=dict)
    check_ignores: dict[str, list[str]] = field(default_factory=dict)
    secret_allowed_patterns: list[str] = field(default_factory=list)


class ConfigError(ValueError):
    """Raised for invalid config content."""


def discover_config_path(start_dir: Path | None = None, filename: str = ".agentlint.toml") -> Path | None:
    current = (start_dir or Path.cwd()).resolve()

    for directory in [current, *current.parents]:
        candidate = directory / filename
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _parse_inline_toml(raw_text: str) -> dict[str, Any]:
    """Minimal fallback parser for the limited config shape when tomllib is unavailable."""

    data: dict[str, Any] = {}
    section: str | None = None

    for raw_line in raw_text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            if section and section not in data:
                data[section] = {}
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        parsed_value: Any
        try:
            parsed_value = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            parsed_value = value.strip('"')

        if section:
            target = data.setdefault(section, {})
            if isinstance(target, dict):
                target[key] = parsed_value
        else:
            data[key] = parsed_value

    return data


def _load_toml(path: Path) -> dict[str, Any]:
    if tomllib is not None:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    return _parse_inline_toml(path.read_text(encoding="utf-8"))


def _as_str_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{field_name} must be a list of strings")
    return value


def build_runtime_config(data: dict[str, Any]) -> RuntimeConfig:
    disabled_checks = set(_as_str_list(data.get("disabled_checks", []), "disabled_checks"))

    severity_raw = data.get("severity", {})
    if not isinstance(severity_raw, dict):
        raise ConfigError("severity must be a table")

    severity_overrides: dict[str, Severity] = {}
    for check_id, severity in severity_raw.items():
        if not isinstance(check_id, str) or not isinstance(severity, str):
            raise ConfigError("severity values must be strings")
        severity_lower = severity.casefold()
        if severity_lower not in _VALID_SEVERITIES:
            raise ConfigError(f"invalid severity override for {check_id}: {severity}")
        severity_overrides[check_id] = severity_lower  # type: ignore[assignment]

    ignore_raw = data.get("ignore", {})
    if not isinstance(ignore_raw, dict):
        raise ConfigError("ignore must be a table")

    check_ignores: dict[str, list[str]] = {}
    for check_id, patterns in ignore_raw.items():
        if not isinstance(check_id, str):
            raise ConfigError("ignore keys must be strings")
        check_ignores[check_id] = _as_str_list(patterns, f"ignore.{check_id}")

    secrets_raw = data.get("secrets", {})
    if isinstance(secrets_raw, dict):
        allow_patterns_value = secrets_raw.get(
            "allowed_patterns",
            data.get("secrets.allowed_patterns", []),
        )
    else:
        allow_patterns_value = data.get("secrets.allowed_patterns", [])

    secret_allowed_patterns = _as_str_list(allow_patterns_value, "secrets.allowed_patterns")

    return RuntimeConfig(
        disabled_checks=disabled_checks,
        severity_overrides=severity_overrides,
        check_ignores=check_ignores,
        secret_allowed_patterns=secret_allowed_patterns,
    )


def load_runtime_config(
    *,
    config_path: Path | None = None,
    no_config: bool = False,
    start_dir: Path | None = None,
) -> RuntimeConfig:
    if no_config:
        return RuntimeConfig()

    target_path = config_path or discover_config_path(start_dir=start_dir)
    if target_path is None:
        return RuntimeConfig()

    data = _load_toml(target_path)
    return build_runtime_config(data)
