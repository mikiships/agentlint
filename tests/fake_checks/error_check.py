from agentlint.models import CheckResult


def run(diff, task_description=None):
    return [
        CheckResult(
            check_id="error_check",
            severity="error",
            message="error result",
            file_path="src/a.py",
            line=2,
        )
    ]
