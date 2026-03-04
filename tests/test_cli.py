from __future__ import annotations

from click.testing import CliRunner

from agentlint import cli
from agentlint.models import CheckResult

SIMPLE_DIFF = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1 +1 @@
-a
+b
"""


class FakeWarningEngine:
    def run(self, diff, task_description=None, config=None):
        return [
            CheckResult(
                check_id="warn_check",
                severity="warning",
                message="warning",
                file_path="a.py",
                line=1,
            )
        ]


class FakeErrorEngine:
    def run(self, diff, task_description=None, config=None):
        return [
            CheckResult(
                check_id="error_check",
                severity="error",
                message="error",
                file_path="a.py",
                line=1,
            )
        ]


class FakeCleanEngine:
    def run(self, diff, task_description=None, config=None):
        return []


def test_cli_json_from_stdin(monkeypatch) -> None:
    monkeypatch.setattr(cli, "LintEngine", lambda: FakeWarningEngine())
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--stdin", "--format", "json"], input=SIMPLE_DIFF)
    assert result.exit_code == 1
    assert '"check": "warn_check"' in result.output
    assert '"metadata"' in result.output


def test_cli_text_default_format(monkeypatch) -> None:
    monkeypatch.setattr(cli, "LintEngine", lambda: FakeWarningEngine())
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--stdin"], input=SIMPLE_DIFF)
    assert result.exit_code == 1
    assert "warn_check" in result.output


def test_cli_stdin_conflict() -> None:
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "HEAD~1..HEAD", "--stdin"], input=SIMPLE_DIFF)
    assert result.exit_code != 0
    assert "cannot be combined" in result.output


def test_cli_uses_git_diff_when_not_stdin(monkeypatch) -> None:
    called = {}

    def fake_loader(range_spec=None, staged=False):
        called["range_spec"] = range_spec
        called["staged"] = staged
        return SIMPLE_DIFF

    monkeypatch.setattr(cli, "_load_diff_text_from_git", fake_loader)
    monkeypatch.setattr(cli, "LintEngine", lambda: FakeCleanEngine())

    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "HEAD~2..HEAD"])
    assert result.exit_code == 0
    assert called == {"range_spec": "HEAD~2..HEAD", "staged": False}


def test_cli_staged_uses_cached(monkeypatch) -> None:
    called = {}

    def fake_loader(range_spec=None, staged=False):
        called["range_spec"] = range_spec
        called["staged"] = staged
        return SIMPLE_DIFF

    monkeypatch.setattr(cli, "_load_diff_text_from_git", fake_loader)
    monkeypatch.setattr(cli, "LintEngine", lambda: FakeCleanEngine())

    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--staged"])
    assert result.exit_code == 0
    assert called == {"range_spec": None, "staged": True}


def test_cli_warning_exit_code(monkeypatch) -> None:
    monkeypatch.setattr(cli, "LintEngine", lambda: FakeWarningEngine())
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--stdin"], input=SIMPLE_DIFF)
    assert result.exit_code == 1


def test_cli_fail_on_error_ignores_warning(monkeypatch) -> None:
    monkeypatch.setattr(cli, "LintEngine", lambda: FakeWarningEngine())
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--stdin", "--fail-on", "error"], input=SIMPLE_DIFF)
    assert result.exit_code == 0


def test_cli_error_exit_code(monkeypatch) -> None:
    monkeypatch.setattr(cli, "LintEngine", lambda: FakeErrorEngine())
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--stdin"], input=SIMPLE_DIFF)
    assert result.exit_code == 1


def test_cli_clean_exit_code(monkeypatch) -> None:
    monkeypatch.setattr(cli, "LintEngine", lambda: FakeCleanEngine())
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--stdin"], input=SIMPLE_DIFF)
    assert result.exit_code == 0


def test_cli_passes_task_to_engine(monkeypatch) -> None:
    called = {}

    class TaskEngine:
        def run(self, diff, task_description=None, config=None):
            called["task"] = task_description
            return []

    monkeypatch.setattr(cli, "LintEngine", lambda: TaskEngine())
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["check", "--stdin", "--task", "fix parser bug"],
        input=SIMPLE_DIFF,
    )
    assert result.exit_code == 0
    assert called["task"] == "fix parser bug"


def test_cli_json_has_summary(monkeypatch) -> None:
    monkeypatch.setattr(cli, "LintEngine", lambda: FakeCleanEngine())
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--stdin", "--format", "json"], input=SIMPLE_DIFF)
    assert result.exit_code == 0
    assert '"summary"' in result.output


def test_cli_markdown_output(monkeypatch) -> None:
    monkeypatch.setattr(cli, "LintEngine", lambda: FakeErrorEngine())
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--stdin", "--format", "markdown"], input=SIMPLE_DIFF)
    assert result.exit_code == 1
    assert "# agentlint Report" in result.output
    assert "<details>" in result.output


def test_cli_quiet_mode(monkeypatch) -> None:
    monkeypatch.setattr(cli, "LintEngine", lambda: FakeWarningEngine())
    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--stdin", "--quiet"], input=SIMPLE_DIFF)
    assert result.exit_code == 1
    assert "errors=0 warnings=1 info=0" in result.output


def test_cli_no_config_and_config_conflict(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "LintEngine", lambda: FakeCleanEngine())
    config_file = tmp_path / ".agentlint.toml"
    config_file.write_text("", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["check", "--stdin", "--no-config", "--config", str(config_file)],
        input=SIMPLE_DIFF,
    )
    assert result.exit_code != 0
    assert "cannot be combined" in result.output


def test_cli_passes_explicit_config(monkeypatch, tmp_path) -> None:
    called = {}

    class TaskEngine:
        def run(self, diff, task_description=None, config=None):
            called["config"] = config
            return []

    config_file = tmp_path / ".agentlint.toml"
    config_file.write_text("disabled_checks = [\"scope_drift\"]\n", encoding="utf-8")

    monkeypatch.setattr(cli, "LintEngine", lambda: TaskEngine())
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["check", "--stdin", "--config", str(config_file)],
        input=SIMPLE_DIFF,
    )
    assert result.exit_code == 0
    assert called["config"].disabled_checks == {"scope_drift"}
