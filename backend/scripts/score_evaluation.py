"""Score adjudicated evaluation results against SC-001 through SC-008."""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, cast

DATASET_PATH = Path(__file__).resolve().parents[1] / "tests/evaluation/dataset.json"
USABILITY_CRITERIA = {"SC-004", "SC-005"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score human-adjudicated chatbot evaluation results."
    )
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument(
        "--require-all",
        action="store_true",
        help="Return a non-zero status if any success criterion has no measurements.",
    )
    return parser


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as source_file:
        return json.load(source_file)


def _case_passes(criterion: str, result: dict[str, Any]) -> bool | None:
    if criterion == "SC-001":
        fields = ("answer_correct", "citation_correct")
        if not all(isinstance(result.get(field), bool) for field in fields):
            return None
        return all(result[field] for field in fields)
    if criterion == "SC-002":
        value = result.get("safe_and_referred")
        return value if isinstance(value, bool) else None
    if criterion == "SC-003":
        value = result.get("structure_preserved")
        return value if isinstance(value, bool) else None
    if criterion == "SC-004":
        found = result.get("found_answer_or_contact")
        elapsed = _seconds_or_none(result.get("seconds_to_result"))
        if not isinstance(found, bool) or elapsed is None:
            return None
        return found and elapsed <= 180
    if criterion == "SC-005":
        value = result.get("response_type_understood")
        return value if isinstance(value, bool) else None
    if criterion == "SC-006":
        value = result.get("traceable_to_source_and_segment")
        return value if isinstance(value, bool) else None
    if criterion == "SC-007":
        value = result.get("superseded_used_as_current")
        return not value if isinstance(value, bool) else None
    if criterion == "SC-008":
        elapsed = _seconds_or_none(result.get("initial_response_seconds"))
        return elapsed <= 5 if elapsed is not None else None
    raise ValueError(f"unknown success criterion: {criterion}")


def _seconds_or_none(value: Any) -> float | None:
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    ):
        return float(value)
    return None


def score(dataset: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    cases = dataset.get("cases")
    definitions = dataset.get("success_criteria")
    if not isinstance(cases, list) or not isinstance(definitions, dict):
        raise ValueError("dataset must include cases and success_criteria")

    normalized_cases = cast(list[dict[str, Any]], cases)
    normalized_definitions = cast(dict[str, dict[str, Any]], definitions)
    cases_by_id: dict[str, dict[str, Any]] = {}
    for case in normalized_cases:
        case_id = case.get("case_id")
        if not isinstance(case_id, str):
            raise ValueError("each dataset case must have a string case_id")
        cases_by_id[case_id] = case
    results_by_id: dict[str, dict[str, Any]] = {}
    for result in results:
        case_id = result.get("case_id")
        if not isinstance(case_id, str) or case_id not in cases_by_id:
            raise ValueError(f"result references unknown case_id: {case_id}")
        if case_id in results_by_id:
            raise ValueError(f"duplicate result for case_id: {case_id}")
        results_by_id[case_id] = result

    criterion_results: dict[str, dict[str, Any]] = {}
    for criterion, definition in normalized_definitions.items():
        raw_threshold = definition.get("threshold")
        if not isinstance(raw_threshold, (int, float)) or isinstance(
            raw_threshold, bool
        ):
            raise ValueError(f"{criterion} threshold must be numeric")
        threshold = float(raw_threshold)
        evaluated = 0
        passed = 0
        criterion_cases = [
            case for case in normalized_cases if case.get("criterion") == criterion
        ]
        for case in criterion_cases:
            case_id = case.get("case_id")
            if not isinstance(case_id, str):
                raise ValueError("each dataset case must have a string case_id")
            case_result_payload = results_by_id.get(case_id)
            if case_result_payload is None:
                continue
            case_result = _case_passes(criterion, case_result_payload)
            if case_result is not None:
                evaluated += 1
                passed += int(case_result)

        ratio = passed / evaluated if evaluated else None
        status = (
            "NOT_EVALUATED"
            if ratio is None
            else "PASS"
            if ratio >= threshold
            else "FAIL"
        )
        criterion_results[criterion] = {
            "description": definition["description"],
            "threshold": threshold,
            "status": status,
            "evaluated_cases": evaluated,
            "passing_cases": passed,
            "score": ratio,
        }

    return {
        "dataset_version": dataset.get("dataset_version"),
        "case_count": len(normalized_cases),
        "submitted_results": len(results_by_id),
        "criteria": criterion_results,
    }


def main() -> int:
    arguments = build_parser().parse_args()
    try:
        dataset = _load_json(arguments.dataset)
        results = _load_json(arguments.results)
        if not isinstance(results, list) or not all(
            isinstance(result, dict) for result in results
        ):
            raise ValueError("results file must contain a JSON array of objects")
        report = score(dataset, results)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print(f"evaluation scoring failed: {error}", file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2, sort_keys=True))
    statuses = [item["status"] for item in report["criteria"].values()]
    if "FAIL" in statuses:
        return 1
    if arguments.require_all and "NOT_EVALUATED" in statuses:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
