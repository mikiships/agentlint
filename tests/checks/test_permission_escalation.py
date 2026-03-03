from __future__ import annotations

from agentlint.checks import permission_escalation

from ._utils import make_diff, parse_diff_text


def test_permission_escalation_detects_sudo() -> None:
    diff = parse_diff_text(make_diff("scripts/deploy.sh", added=["sudo rm -rf /tmp/data"]))
    findings = permission_escalation.run(diff)
    assert len(findings) == 1
    assert findings[0].severity == "error"


def test_permission_escalation_detects_chmod() -> None:
    diff = parse_diff_text(make_diff("scripts/deploy.sh", added=["chmod 777 ./run.sh"]))
    assert len(permission_escalation.run(diff)) == 1


def test_permission_escalation_detects_subprocess_shell_true() -> None:
    diff = parse_diff_text(
        make_diff("src/app.py", added=["subprocess.run(cmd, shell=True, check=False)"])
    )
    assert len(permission_escalation.run(diff)) == 1


def test_permission_escalation_detects_os_system() -> None:
    diff = parse_diff_text(make_diff("src/app.py", added=["os.system('rm -rf /')"]))
    assert len(permission_escalation.run(diff)) == 1


def test_permission_escalation_detects_eval() -> None:
    diff = parse_diff_text(make_diff("src/app.py", added=["eval(user_input)"]))
    assert len(permission_escalation.run(diff)) == 1


def test_permission_escalation_ignores_safe_line() -> None:
    diff = parse_diff_text(make_diff("src/app.py", added=["print('safe')"]))
    assert permission_escalation.run(diff) == []
