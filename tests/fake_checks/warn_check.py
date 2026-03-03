from agentlint.models import CheckResult


def run(diff, task_description=None):
    return [
        CheckResult(
            check_id="warn_check",
            severity="warning",
            message="warning result",
            file_path="src/b.py",
            line=4,
        )
    ]
