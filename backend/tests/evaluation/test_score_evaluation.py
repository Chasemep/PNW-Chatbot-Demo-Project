import json
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SCORER = BACKEND_ROOT / "scripts" / "score_evaluation.py"


def run_scorer(
    tmp_path: Path,
    results: list[dict[str, object]],
) -> subprocess.CompletedProcess[str]:
    result_path = tmp_path / "results.json"
    result_path.write_text(json.dumps(results), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCORER), "--results", str(result_path)],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_scorer_reports_measured_metrics_and_leaves_missing_metrics_unscored(
    tmp_path: Path,
) -> None:
    results = [
        {
            "case_id": f"SC001-{case}",
            "answer_correct": True,
            "citation_correct": True,
        }
        for case in (
            "ADD-DEADLINE",
            "DROP-PROCEDURE",
            "ACADEMIC-STANDING",
            "GRADE-APPEAL",
            "ABSENCE",
        )
    ]

    completed = run_scorer(tmp_path, results)

    assert completed.returncode == 0
    report = json.loads(completed.stdout)
    assert report["criteria"]["SC-001"]["status"] == "PASS"
    assert report["criteria"]["SC-001"]["score"] == 1.0
    assert report["criteria"]["SC-004"]["status"] == "NOT_EVALUATED"


def test_scorer_fails_a_measured_criterion_below_threshold(tmp_path: Path) -> None:
    completed = run_scorer(
        tmp_path,
        [
            {
                "case_id": "SC001-ADD-DEADLINE",
                "answer_correct": False,
                "citation_correct": True,
            }
        ],
    )

    assert completed.returncode == 1
    report = json.loads(completed.stdout)
    assert report["criteria"]["SC-001"]["status"] == "FAIL"
