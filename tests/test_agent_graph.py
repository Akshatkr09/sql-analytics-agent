from app.agent.graph import route_after_execution


def test_success_routes_to_done():
    assert route_after_execution({"status": "success", "retry_count": 0}) == "done"


def test_security_block_routes_to_done():
    assert route_after_execution({"status": "blocked", "retry_count": 0}) == "done"


def test_database_error_routes_to_reflection():
    assert route_after_execution({"status": "error", "retry_count": 0}) == "reflect"


def test_retry_limit_routes_to_done():
    assert route_after_execution({"status": "error", "retry_count": 3}) == "done"
