from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> dict[str, object]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_action_yaml_is_valid_and_has_required_contract_inputs() -> None:
    action = _load_yaml(ROOT / "action.yml")
    inputs = action["inputs"]
    assert isinstance(inputs, dict)

    assert inputs["fail-on-error"]["default"] == "true"
    assert inputs["fail-on-warning"]["default"] == "false"
    assert inputs["format"]["default"] == "text"
    assert inputs["comment"]["default"] == "true"
    assert inputs["python-version"]["default"] == "3.12"

    outputs = action["outputs"]
    assert isinstance(outputs, dict)
    assert "exit-code" in outputs
    assert "report" in outputs


def test_reusable_workflow_yaml_is_valid_and_runs_on_pull_request() -> None:
    workflow = _load_yaml(ROOT / ".github/workflows/agentlint-ci.yml")
    event_block = workflow.get("on", workflow.get(True))
    assert isinstance(event_block, dict)
    assert "pull_request" in event_block
    assert "workflow_call" in event_block

    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    assert "lint-pr-diff" in jobs
