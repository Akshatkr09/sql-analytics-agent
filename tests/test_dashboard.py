"""Unit tests for dashboard data preparation and automatic chart selection."""
import pandas as pd

from app.ui.dashboard import build_chart_figure, results_to_dataframe


def test_results_to_dataframe_converts_rows():
    frame = results_to_dataframe([{"status": "Delivered", "total": 120.0}])
    assert list(frame.columns) == ["status", "total"]
    assert frame.iloc[0]["total"] == 120.0


def test_results_to_dataframe_handles_empty_results():
    assert results_to_dataframe([]).empty


def test_build_chart_figure_uses_line_for_date_dimension():
    frame = pd.DataFrame({
        "order_date": ["2026-01-01", "2026-02-01"],
        "revenue": [100.0, 150.0],
    })
    figure = build_chart_figure(frame)
    assert figure is not None
    assert figure.data[0].type == "scatter"
    assert figure.data[0].mode == "lines+markers"


def test_build_chart_figure_uses_pie_for_small_category_dimension():
    frame = pd.DataFrame({"status": ["Delivered", "Pending", "Shipped"], "orders": [4, 2, 1]})
    figure = build_chart_figure(frame)
    assert figure is not None
    assert figure.data[0].type == "pie"


def test_build_chart_figure_uses_bar_for_many_categories():
    frame = pd.DataFrame({"city": [f"City {i}" for i in range(8)], "revenue": list(range(8))})
    figure = build_chart_figure(frame)
    assert figure is not None
    assert figure.data[0].type == "bar"


def test_build_chart_figure_skips_non_numeric_data():
    frame = pd.DataFrame({"customer": ["A", "B"], "city": ["Patna", "Bhopal"]})
    assert build_chart_figure(frame) is None
