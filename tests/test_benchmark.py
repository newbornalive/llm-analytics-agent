import json
from pathlib import Path

from analytics_agent.planner import SQL, demo_plan
from analytics_agent.workflow import run_analysis
from evaluation.benchmark import run_benchmark, evaluate_case


def test_scoped_demo_benchmark():
    result = run_benchmark()
    assert result["case_count"] == 17
    assert result["supported_pass_rate"] == 1
    assert result["unsupported_rejection_rate"] == 1
    assert result["overall_pass_rate"] == 1


def test_infrastructure_failure_cannot_pass_unsupported():
    case = {"id": "err", "question": "What is revenue?", "supported": False}
    def fail(question, db_path, mode):
        raise ValueError("Database does not exist.")
    assert evaluate_case(case, mode="demo", db_path=Path("unused"), runner=fail)["passed"] is False


def test_valid_execution_with_wrong_statistics_fails():
    case = {"id": "bad", "question": "Compare conversion rates by channel", "supported": True}
    def wrong(question, db_path, mode):
        return {"sql": SQL, "query_warnings": [], "statistics": {
            "sample_size": 1000, "groups": [{"channel": "Email", "events": 319, "conversions": 0,
            "rate": 0.0, "wilson_95_ci": [0, 0.1]}]}}
    assert evaluate_case(case, mode="demo", db_path=Path("unused"), runner=wrong)["passed"] is False
