from app.security.guardrails import _deterministic_input_check


def test_blocks_drop_table_input():
    result = _deterministic_input_check("DROP TABLE orders; --")
    assert not result.allowed


def test_blocks_script_tag():
    result = _deterministic_input_check("<script>alert(1)</script>")
    assert not result.allowed


def test_blocks_tautology_pattern():
    result = _deterministic_input_check("Show users OR 1=1")
    assert not result.allowed


def test_allows_normal_analytics_question():
    result = _deterministic_input_check("Show total sales by month")
    assert result.allowed
