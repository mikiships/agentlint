from __future__ import annotations

from agentlint.checks import dependency_injection

from ._utils import make_diff, parse_diff_text


def test_dependency_injection_flags_requirements_addition() -> None:
    diff = parse_diff_text(make_diff("requirements.txt", added=["requests==2.32.0"]))
    findings = dependency_injection.run(diff)
    assert len(findings) == 1


def test_dependency_injection_flags_package_json_addition() -> None:
    diff = parse_diff_text(make_diff("package.json", added=['"left-pad": "1.3.0"']))
    findings = dependency_injection.run(diff)
    assert len(findings) == 1


def test_dependency_injection_flags_pyproject_dependency() -> None:
    diff = parse_diff_text(make_diff("pyproject.toml", added=['fastapi = "^0.111"']))
    findings = dependency_injection.run(diff)
    assert len(findings) == 1


def test_dependency_injection_allows_dependency_task() -> None:
    diff = parse_diff_text(make_diff("requirements.txt", added=["rich>=13.0"]))
    findings = dependency_injection.run(diff, task_description="dependency upgrade")
    assert findings == []


def test_dependency_injection_ignores_non_dependency_lines() -> None:
    diff = parse_diff_text(make_diff("requirements.txt", added=["# comment only"]))
    assert dependency_injection.run(diff) == []


def test_dependency_injection_ignores_source_files() -> None:
    diff = parse_diff_text(make_diff("src/app.py", added=["import x"]))
    assert dependency_injection.run(diff) == []
