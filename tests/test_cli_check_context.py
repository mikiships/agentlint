"""Integration tests for the check-context CLI command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from agentlint.cli import main


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def agents_md(tmp_path: Path) -> Path:
    p = tmp_path / "AGENTS.md"
    p.write_text("# Instructions\n\nRun pytest to test.\n")
    return p


# ---------------------------------------------------------------------------
# Basic
# ---------------------------------------------------------------------------

def test_basic_text_output(runner: CliRunner, agents_md: Path) -> None:
    result = runner.invoke(
        main,
        ["check-context", str(agents_md), "--repo-root", str(agents_md.parent)],
    )
    assert result.exit_code in (0, 1)
    assert "agentlint context check" in result.output
    assert "Freshness score" in result.output


def test_no_file_auto_detects(runner: CliRunner, tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("Hello world.")
    result = runner.invoke(main, ["check-context", "--repo-root", str(tmp_path)])
    assert "agentlint context check" in result.output


def test_no_file_and_no_context_file_errors(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(main, ["check-context", "--repo-root", str(tmp_path)])
    assert result.exit_code != 0
    assert "No context file found" in result.output


def test_file_not_found_errors(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(
        main,
        ["check-context", str(tmp_path / "nonexistent.md"), "--repo-root", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "Error" in result.output


# ---------------------------------------------------------------------------
# --format json
# ---------------------------------------------------------------------------

def test_json_output_valid_json(runner: CliRunner, agents_md: Path) -> None:
    result = runner.invoke(
        main,
        ["check-context", str(agents_md), "--repo-root", str(agents_md.parent), "--format", "json"],
    )
    data = json.loads(result.output)
    assert "file" in data
    assert "freshness_score" in data
    assert "findings" in data
    assert isinstance(data["findings"], list)


def test_json_output_freshness_in_range(runner: CliRunner, agents_md: Path) -> None:
    result = runner.invoke(
        main,
        ["check-context", str(agents_md), "--repo-root", str(agents_md.parent), "--format", "json"],
    )
    data = json.loads(result.output)
    assert 0 <= data["freshness_score"] <= 100


# ---------------------------------------------------------------------------
# --format markdown
# ---------------------------------------------------------------------------

def test_markdown_output_contains_table(runner: CliRunner, agents_md: Path) -> None:
    result = runner.invoke(
        main,
        ["check-context", str(agents_md), "--repo-root", str(agents_md.parent), "--format", "markdown"],
    )
    assert "agentlint context check" in result.output
    assert "Freshness score" in result.output


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------

def test_exit_1_on_errors(runner: CliRunner, tmp_path: Path) -> None:
    p = tmp_path / "AGENTS.md"
    p.write_text("x" * 16_000)  # triggers CTX003 error
    result = runner.invoke(
        main, ["check-context", str(p), "--repo-root", str(tmp_path)]
    )
    assert result.exit_code == 1


def test_exit_0_when_only_warnings(runner: CliRunner, tmp_path: Path) -> None:
    p = tmp_path / "AGENTS.md"
    # 9k chars → warning only
    p.write_text("x" * 9_000)
    result = runner.invoke(
        main, ["check-context", str(p), "--repo-root", str(tmp_path)]
    )
    assert result.exit_code == 0
