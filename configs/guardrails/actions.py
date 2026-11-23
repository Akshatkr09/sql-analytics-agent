"""Local deterministic action used by the NeMo input rail."""
from typing import Optional

from nemoguardrails.actions import action
from nemoguardrails.actions.rail_outcome import RailOutcome


_BLOCK_PATTERNS = [
    r"<\s*script\b",
    r"\b(?:DROP|TRUNCATE|ALTER)\s+(?:TABLE|DATABASE|VIEW|INDEX)\b",
    r"\b(?:DELETE\s+FROM|UPDATE\s+\w+\s+SET|INSERT\s+INTO)\b",
    r"(?:--|/\*|\*/|;\s*--)",
    r"\b(?:OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?",
]


@action(is_system_action=True)
async def screen_sql_agent_input(context: Optional[dict] = None):
    """Block obvious SQL injection and destructive instructions locally."""
    import re

    context = context or {}
    message = str(context.get("user_message", ""))
    if not message.strip():
        return RailOutcome.block(reason="The request is empty.")
    for pattern in _BLOCK_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return RailOutcome.block(reason="Input violates the SQL analytics agent security policy.")
    return RailOutcome.allow()
