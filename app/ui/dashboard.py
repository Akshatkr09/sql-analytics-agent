"""Streamlit dashboard for the SQL analytics agent."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px


def results_to_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Convert agent result rows to a DataFrame suitable for display/charting."""
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def build_chart_figure(dataframe: pd.DataFrame):
    """Build a suitable Plotly chart from tabular query results.

    Heuristics:
    - Date/time-like columns + numeric values -> line chart.
    - Small categorical dimension + numeric values -> pie chart.
    - Other numeric result sets -> bar chart.
    Returns None when the result set is not chartable.
    """
    if dataframe is None or dataframe.empty or len(dataframe.columns) < 2:
        return None

    numeric_columns = [
        column for column in dataframe.select_dtypes(include="number").columns
        if not pd.api.types.is_bool_dtype(dataframe[column])
    ]
    if not numeric_columns:
        return None

    non_numeric_columns = [column for column in dataframe.columns if column not in numeric_columns]
    x_column = non_numeric_columns[0] if non_numeric_columns else None
    y_column = numeric_columns[0]

    if x_column is None:
        chart_data = dataframe.reset_index().rename(columns={"index": "row"})
        return px.bar(chart_data, x="row", y=y_column, title=f"{y_column} by row")

    x_name = str(x_column).lower()
    if any(token in x_name for token in ("date", "time", "month", "year")):
        chart_data = dataframe.copy()
        parsed_dates = pd.to_datetime(chart_data[x_column], errors="coerce")
        if parsed_dates.notna().any():
            chart_data[x_column] = parsed_dates
            chart_data = chart_data.sort_values(x_column)
            return px.line(
                chart_data, x=x_column, y=y_column, markers=True,
                title=f"{y_column} over {x_column}",
            )

    distinct_count = dataframe[x_column].nunique(dropna=True)
    if 1 < distinct_count <= 6 and (dataframe[y_column].dropna() >= 0).all():
        return px.pie(
            dataframe, names=x_column, values=y_column,
            title=f"{y_column} by {x_column}",
        )

    return px.bar(
        dataframe, x=x_column, y=y_column,
        title=f"{y_column} by {x_column}",
    )


def _render_results(st, result: dict[str, Any], elapsed_ms: float) -> None:
    status = result.get("status", "unknown")
    if status == "blocked":
        st.error(result.get("error_message") or "Security warning: request blocked.", icon="🛡️")
    elif status == "success":
        st.success("Query executed successfully.")
    else:
        st.warning(result.get("error_message") or f"Agent finished with status: {status}")

    metric_columns = st.columns(3)
    metric_columns[0].metric("Execution time", f"{elapsed_ms:.0f} ms")
    metric_columns[1].metric("Rows returned", len(result.get("db_result") or []))
    metric_columns[2].metric("Correction retries", result.get("retry_count", 0))

    generated_sql = result.get("generated_sql") or "No SQL generated (request was blocked before generation)."
    with st.expander("Generated SQL", expanded=True):
        st.code(generated_sql, language="sql")

    with st.expander("Execution logs & telemetry", expanded=False):
        st.write({
            "status": status,
            "execution_time_ms": round(elapsed_ms, 2),
            "retry_count": result.get("retry_count", 0),
            "nemo_guardrails_checked": result.get("guardrail_nemo_checked", False),
            "schema_inspected": bool(result.get("schema_text")),
        })
        logs = result.get("correction_logs") or []
        if logs:
            st.markdown("**Self-correction history**")
            for log_entry in logs:
                st.write(f"- {log_entry}")
        else:
            st.caption("No self-correction retries were required.")
        if result.get("error_message"):
            st.text_area("Agent message", result["error_message"], height=90, disabled=True)

    rows = result.get("db_result") or []
    if rows:
        dataframe = results_to_dataframe(rows)
        st.subheader("Query results")
        st.dataframe(dataframe, use_container_width=True, hide_index=True)
        figure = build_chart_figure(dataframe)
        if figure is not None:
            st.subheader("Automatic visualization")
            st.plotly_chart(figure, use_container_width=True)
        else:
            st.info("These results do not contain enough structured numeric data for an automatic chart.")
    elif status == "success":
        st.info("The query executed successfully but returned no rows.")


def render_dashboard() -> None:
    """Render the complete Streamlit dashboard."""
    import time
    import streamlit as st

    from app.agent.graph import run_sql_agent
    from app.database.connection import get_database_url
    from app.database.seed import seed_database

    st.set_page_config(
        page_title="SQL Analytics Agent",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("📊 SQL & Database Analytics Agent")
    st.caption("Ask questions in plain English. The agent inspects your schema, generates read-only SQL, and self-corrects execution errors.")

    with st.sidebar:
        st.header("Workspace")
        st.markdown("**Database**")
        database_url = get_database_url()
        if database_url.startswith("sqlite"):
            st.code("SQLite", language=None)
        else:
            st.code(database_url.split("@")[-1], language=None)
        st.caption("Database credentials are not displayed.")
        if st.button("Seed / verify sample database", use_container_width=True):
            try:
                seed_database()
                st.success("Sample database is ready.")
            except Exception as exc:
                st.error(f"Could not seed the database: {exc}")
        st.divider()
        st.markdown("**Example questions**")
        st.markdown(
            "- Show orders sorted by date\n"
            "- What is the total revenue by order status?\n"
            "- List the top 5 customers by total spending\n"
            "- Show monthly sales trends"
        )
        st.divider()
        st.caption("Security: NeMo input screening + SQLGlot read-only AST validation.")

    with st.form("analytics_query_form", clear_on_submit=False):
        user_query = st.text_area(
            "What would you like to know?",
            placeholder="e.g. Show orders sorted by date",
            height=110,
            help="Ask a business question. The agent will generate and validate a read-only SQL query.",
        )
        submitted = st.form_submit_button("Run analysis", type="primary", use_container_width=True)

    if submitted:
        if not user_query.strip():
            st.warning("Enter a question before running the analysis.")
            return
        with st.spinner("Inspecting schema and running the SQL analytics agent..."):
            started = time.perf_counter()
            try:
                result = run_sql_agent(user_query)
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - started) * 1000
                st.error(f"The agent encountered an unexpected error: {exc}")
                with st.expander("Error details"):
                    st.exception(exc)
                st.metric("Time before failure", f"{elapsed_ms:.0f} ms")
                return
            elapsed_ms = (time.perf_counter() - started) * 1000
        _render_results(st, result, elapsed_ms)
    else:
        st.info("Enter a question above and select **Run analysis** to begin.")
        st.markdown("### How it works")
        cols = st.columns(4)
        cols[0].markdown("**1. Inspect**\n\nRead database tables and columns.")
        cols[1].markdown("**2. Generate**\n\nGemini translates your question into SQL.")
        cols[2].markdown("**3. Validate**\n\nNeMo and SQLGlot enforce security boundaries.")
        cols[3].markdown("**4. Reflect**\n\nLangGraph retries recoverable query errors.")
