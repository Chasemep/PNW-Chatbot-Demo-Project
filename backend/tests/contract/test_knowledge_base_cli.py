import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
COMMAND = [sys.executable, "scripts/prepare_knowledge_base.py"]


def run_command(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*COMMAND, *arguments],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_preparation_command_documents_the_contractual_arguments():
    result = run_command("--help")

    assert result.returncode == 0
    for argument in (
        "--manifest",
        "--release-label",
        "--source-root",
        "--dry-run",
        "--activate",
    ):
        assert argument in result.stdout


def test_preparation_command_requires_manifest_and_release_label():
    result = run_command()

    assert result.returncode != 0
    assert "--manifest" in result.stderr
    assert "--release-label" in result.stderr