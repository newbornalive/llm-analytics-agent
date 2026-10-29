from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from .planner import demo_plan, openai_plan
from .guardrails import validate_sql
from .database import execute_query
from .statistics import analyze_rows

class State(TypedDict, total=False):
    question: str
    plan: dict
    sql: str
    warnings: list
    rows: list
    statistics: dict
    report: dict


def build_workflow(db_path, mode="demo", planner=None):
    if mode not in {"demo", "openai"}:
        raise ValueError("Mode must be demo or openai.")
    selected = planner or (demo_plan if mode == "demo" else openai_plan)
    def plan(state):
        question = state["question"]
        if not isinstance(question, str) or not question.strip() or len(question) > 2000:
            raise ValueError("Question must contain 1-2,000 characters.")
        return {"plan": selected(question)}
    def guard(state):
        sql, warnings = validate_sql(state["plan"]["sql"])
        return {"sql": sql, "warnings": warnings}
    def execute(state):
        return {"rows": execute_query(db_path, state["sql"])}
    def analyze(state):
        return {"statistics": analyze_rows(state["rows"])}
    def report(state):
        return {"report": {"question": state["question"], "mode": mode, "sql": state["sql"],
                "plan_rationale": state["plan"]["rationale"], "statistics": state["statistics"],
                "query_warnings": state["warnings"], "interpretation": "Compare observed conversion rates and uncertainty; this analysis does not identify causal channel effects."}}
    graph = StateGraph(State)
    for name, action in [("plan", plan), ("guard", guard), ("execute", execute), ("analyze", analyze), ("report", report)]:
        graph.add_node(name, action)
    for a, b in [(START, "plan"), ("plan", "guard"), ("guard", "execute"), ("execute", "analyze"), ("analyze", "report"), ("report", END)]:
        graph.add_edge(a, b)
    return graph.compile()


def run_analysis(question, db_path, mode="demo", planner=None):
    return build_workflow(db_path, mode, planner).invoke({"question": question})["report"]
