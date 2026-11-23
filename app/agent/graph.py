"""LangGraph SQL agent with pre-LLM input screening and bounded correction."""
from langgraph.graph import END, START, StateGraph

from app.agent.nodes import execute_query_node, generate_sql_node, inspect_schema_node, reflection_node
from app.agent.state import SQLAgentState
from app.security.guardrails import validate_user_input

MAX_RETRIES = 3


def route_after_execution(state: SQLAgentState) -> str:
    if state.get("status") in {"success", "blocked"}:
        return "done"
    if state.get("retry_count", 0) >= MAX_RETRIES:
        return "done"
    return "reflect"


def route_after_reflection(state: SQLAgentState) -> str:
    if state.get("retry_count", 0) >= MAX_RETRIES:
        return "done"
    return "generate"


def build_sql_agent():
    graph = StateGraph(SQLAgentState)
    graph.add_node("inspect_schema_node", inspect_schema_node)
    graph.add_node("generate_sql_node", generate_sql_node)
    graph.add_node("execute_query_node", execute_query_node)
    graph.add_node("reflection_node", reflection_node)
    graph.add_edge(START, "inspect_schema_node")
    graph.add_edge("inspect_schema_node", "generate_sql_node")
    graph.add_edge("generate_sql_node", "execute_query_node")
    graph.add_conditional_edges("execute_query_node", route_after_execution, {"done": END, "reflect": "reflection_node"})
    graph.add_conditional_edges("reflection_node", route_after_reflection, {"done": END, "generate": "generate_sql_node"})
    return graph.compile()


def run_sql_agent(user_query: str) -> dict:
    if not user_query or not user_query.strip():
        raise ValueError("User question cannot be empty.")
    # Blocked raw input never reaches schema inspection or Gemini.
    guardrail = validate_user_input(user_query)
    if not guardrail.allowed:
        return {
            "user_query": user_query.strip(), "generated_sql": "", "db_result": [],
            "error_message": f"Security warning: {guardrail.reason}", "retry_count": 0,
            "schema_text": "", "status": "blocked", "correction_logs": [],
            "guardrail_nemo_checked": guardrail.nemo_checked,
        }
    initial_state: SQLAgentState = {
        "user_query": user_query.strip(), "generated_sql": "", "db_result": [],
        "error_message": None, "retry_count": 0, "schema_text": "",
        "status": "started", "correction_logs": [],
    }
    result = build_sql_agent().invoke(initial_state)
    result["guardrail_nemo_checked"] = guardrail.nemo_checked
    return result
