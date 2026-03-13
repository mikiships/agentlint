"""CLI entry points for agentlint."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click

from .config import ConfigError, load_runtime_config
from .context_checker import ContextChecker, _auto_detect_context_file
from .context_formatters import format_context_report
from .engine import LintEngine, exit_code_for_findings
from .parser import parse_unified_diff
from .report import render


def _load_diff_text_from_git(range_spec: str | None = None, staged: bool = False) -> str:
    cmd: list[str] = ["git", "diff"]
    if staged:
        cmd.append("--cached")
    elif range_spec:
        cmd.append(range_spec)
    else:
        cmd.append("HEAD~1..HEAD")

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise click.ClickException(proc.stderr.strip() or "failed to read git diff")
    return proc.stdout


@click.group()
def main() -> None:
    """Lint AI coding agent git diffs for common problems."""


@main.command("check")
@click.argument("range_spec", required=False)
@click.option("--staged", is_flag=True, help="Lint staged changes (git diff --cached).")
@click.option("--stdin", "use_stdin", is_flag=True, help="Read unified diff from stdin.")
@click.option("--task", "task_description", type=str, help="Task description for scope-aware checks.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "markdown"], case_sensitive=False),
    default="text",
    show_default=True,
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to an explicit .agentlint.toml file.",
)
@click.option(
    "--no-config",
    is_flag=True,
    help="Do not load .agentlint.toml from the current directory tree.",
)
@click.option(
    "--fail-on",
    type=click.Choice(["warning", "error"], case_sensitive=False),
    default="warning",
    show_default=True,
    help="Severity threshold that causes a non-zero exit code.",
)
@click.option(
    "--quiet",
    is_flag=True,
    help="Reduce output decoration for CI/log processing.",
)
def check_command(
    range_spec: str | None,
    staged: bool,
    use_stdin: bool,
    task_description: str | None,
    output_format: str,
    config_path: Path | None,
    no_config: bool,
    fail_on: str,
    quiet: bool,
) -> None:
    """Run checks against a git diff."""

    if use_stdin and (staged or range_spec):
        raise click.UsageError("--stdin cannot be combined with --staged or commit range")

    if use_stdin:
        diff_text = sys.stdin.read()
    else:
        diff_text = _load_diff_text_from_git(range_spec=range_spec, staged=staged)

    if no_config and config_path is not None:
        raise click.UsageError("--no-config cannot be combined with --config")

    try:
        runtime_config = load_runtime_config(config_path=config_path, no_config=no_config)
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    diff = parse_unified_diff(diff_text)
    findings = LintEngine().run(diff, task_description=task_description, config=runtime_config)
    click.echo(render(findings, output_format=output_format, quiet=quiet))
    raise SystemExit(exit_code_for_findings(findings, fail_on=fail_on))


@main.command("check-context")
@click.argument("file", required=False, type=click.Path(exists=False, path_type=Path))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "markdown"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Repository root for path resolution (default: cwd).",
)
@click.option(
    "--no-config",
    is_flag=True,
    help="Skip .agentlint.toml configuration.",
)
def check_context_command(
    file: Path | None,
    output_format: str,
    repo_root: Path | None,
    no_config: bool,
) -> None:
    """Validate an AGENTS.md / CLAUDE.md context file for staleness and bloat.

    FILE defaults to the first of AGENTS.md, CLAUDE.md, GEMINI.md, .cursorrules
    found in the current directory.
    """
    resolved_root = repo_root or Path.cwd()

    if file is None:
        file = _auto_detect_context_file(resolved_root)
        if file is None:
            raise click.ClickException(
                "No context file found. Pass a FILE argument or create AGENTS.md / CLAUDE.md."
            )
    else:
        if not file.is_absolute():
            file = resolved_root / file
        if not file.exists():
            raise click.ClickException(f"File not found: {file}")
        # If a directory was passed, auto-detect from it
        if file.is_dir():
            resolved_root = file
            file = _auto_detect_context_file(resolved_root)
            if file is None:
                raise click.ClickException(
                    f"No context file found in {resolved_root}. Create AGENTS.md / CLAUDE.md."
                )

    checker = ContextChecker(file_path=file, repo_root=resolved_root)
    report = checker.run()
    click.echo(format_context_report(report, output_format=output_format))
    if report.error_count > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
