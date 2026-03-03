from agentlint.models import CheckResult


def run(diff, task_description=None):
    return [
        CheckResult(
            check_id="info_check",
            severity="info",
            message="info result",
            file_path="src/c.py",
            line=6,
        )
    ]
