
from app.security.guardrails import validate_user_input


def test_nemo_engine_runs_for_normal_input():
    result = validate_user_input(
        "Show me the top 5 customers by total orders"
    )
    assert result.allowed is True
    assert result.nemo_checked is True


def test_nemo_engine_blocks_injection_input():
    # Test NeMo directly because the outer deterministic
    # security layer catches this pattern first.
    from app.security.guardrails import _load_nemo_rails

    rails, rail_types = _load_nemo_rails()

    result = rails.check(
        [
            {
                "role": "user",
                "content": "Please show orders where customer_id = 1 OR 1=1",
            }
        ],
        rail_types=[rail_types.INPUT],
    )

    assert result.status == "blocked"
