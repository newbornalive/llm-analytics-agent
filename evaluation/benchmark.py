"""Run a scoped, versioned question-to-analysis acceptance benchmark.

This measures accepted/rejected intent and guarded end-to-end execution, not SQL
semantic accuracy on arbitrary databases or statistical generalisation.
"""
import argparse
import json
from pathlib import Path

from analytics_agent.workflow import run_analysis

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "evaluation" / "cases.json"
DEFAULT_DB = ROOT / "data" / "marketing.db"
EXPECTED_GROUPS = {
    "Email": (319, 30),
    "Paid Search": (354, 31),
    "Social": (327, 14),
}


def evaluate_case(case, *, mode, db_path, runner=run_analysis):
    try:
        result = runner(case["question"], db_path, mode)
    except ValueError as exc:
        message = str(exc)
        # Only an explicit unsupported-intent outcome counts as a correct refusal.
        rejected = message.startswith(("Unsupported question:", "Demo mode supports"))
        return {"id": case["id"], "expected_supported": case["supported"],
                "predicted_supported": False if rejected else None,
                "passed": (not case["supported"]) and rejected,
                "error": message if not rejected else None}
    except (OSError, RuntimeError) as exc:
        return {"id": case["id"], "expected_supported": case["supported"],
                "predicted_supported": None, "passed": False,
                "error": type(exc).__name__ + ": " + str(exc)}
    stats = result["statistics"]
    groups = {g["channel"]: (g["events"], g["conversions"]) for g in stats["groups"]}
    valid = (stats["sample_size"] == 1000 and groups == EXPECTED_GROUPS
             and result.get("sql") and isinstance(result.get("query_warnings"), list)
             and all(0 <= g["rate"] <= 1 and len(g["wilson_95_ci"]) == 2
                     for g in stats["groups"]))
    return {"id": case["id"], "expected_supported": case["supported"],
            "predicted_supported": True, "passed": bool(case["supported"] and valid),
            "error": None if valid else "Unexpected statistical or report output"}


def run_benchmark(mode="demo", cases_path=DEFAULT_CASES, db_path=DEFAULT_DB, runner=run_analysis):
    payload = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    cases = payload["cases"]
    if not cases or len({item["id"] for item in cases}) != len(cases):
        raise ValueError("Cases must be nonempty and have unique IDs.")
    if any(not isinstance(c.get("supported"), bool) or not isinstance(c.get("question"), str)
           for c in cases):
        raise ValueError("Cases require a question and boolean supported label.")
    results = [evaluate_case(case, mode=mode, db_path=db_path, runner=runner) for case in cases]
    supported = [r for r in results if r["expected_supported"]]
    unsupported = [r for r in results if not r["expected_supported"]]
    score = lambda rows: sum(r["passed"] for r in rows) / len(rows) if rows else None
    return {"benchmark": "scoped-v1", "mode": mode, "case_count": len(results),
            "supported_pass_rate": score(supported), "unsupported_rejection_rate": score(unsupported),
            "overall_pass_rate": score(results), "results": results,
            "limitations": "Curated synthetic-schema acceptance checks; no BIRD/Spider evaluation, no causal validity or real-world accuracy claims."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["demo", "openai"], default="demo")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    summary = run_benchmark(args.mode, args.cases, args.db)
    output = json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output)
    raise SystemExit(0 if summary["overall_pass_rate"] == 1 else 1)


if __name__ == "__main__":
    main()
