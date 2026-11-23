"""Input screening with deterministic checks and a NeMo Guardrails input rail.

The local deterministic screen runs first. NeMo then executes a configured
Colang 1.0 input rail backed by a local Python action; no second LLM is called.
"""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    reason: str
    nemo_checked: bool = False


_BLOCK_PATTERNS = [
    (re.compile(r"<\s*script\b", re.IGNORECASE), "Script tags are not allowed."),
    (re.compile(r"\b(?:DROP|TRUNCATE|ALTER)\s+(?:TABLE|DATABASE|VIEW|INDEX)\b", re.IGNORECASE), "Destructive SQL instructions are blocked."),
    (re.compile(r"\b(?:DELETE\s+FROM|UPDATE\s+\w+\s+SET|INSERT\s+INTO)\b", re.IGNORECASE), "Write operations are not allowed."),
    (re.compile(r"(?:--|/\*|\*/|;\s*--)", re.IGNORECASE), "SQL comments or statement-expansion patterns are not allowed in the request."),
    (re.compile(r"\b(?:OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?", re.IGNORECASE), "Possible tautology or injection pattern detected."),
]


def _deterministic_reason(message: str) -> str | None:
    if not isinstance(message, str) or not message.strip():
        return "The request is empty."
    for pattern, reason in _BLOCK_PATTERNS:
        if pattern.search(message):
            return reason
    return None


def _deterministic_input_check(message: str) -> GuardrailResult:
    reason = _deterministic_reason(message)
    return GuardrailResult(reason is None, reason or "Input passed deterministic security checks.")


@lru_cache(maxsize=1)
def _load_nemo_rails():
    """Load the configured NeMo input rail using the installed NeMo API."""
    from nemoguardrails import Guardrails, RailsConfig
    from nemoguardrails.rails.llm.options import RailType

    config_dir = Path(__file__).resolve().parents[2] / "configs" / "guardrails"
    config = RailsConfig.from_path(str(config_dir))
    # This project uses a local custom Colang action and deliberately does not
    # invoke a second model. NeMo 0.25 routes this legacy flow through LLMRails.
    rails = Guardrails(config, use_iorails=False)
    return rails, RailType


def validate_user_input(message: str) -> GuardrailResult:
    """Check raw user text before it reaches schema inspection or Gemini."""
    baseline = _deterministic_input_check(message)
    if not baseline.allowed:
        return baseline

    try:
        rails, rail_types = _load_nemo_rails()
        checked = rails.check(
            [{"role": "user", "content": message}],
            rail_types=[rail_types.INPUT],
        )
        status = getattr(checked, "status", None)
        if status is None and isinstance(checked, dict):
            status = checked.get("status")
        status_text = str(getattr(status, "value", status)).upper()
        if "BLOCKED" in status_text:
            return GuardrailResult(False, "NeMo Guardrails blocked this request.", True)
        return GuardrailResult(True, "Input passed deterministic and NeMo checks.", True)
    except Exception as exc:
        # A configured security layer must not silently fail open.
        return GuardrailResult(
            False,
            f"NeMo Guardrails could not verify this request; blocked for safety ({type(exc).__name__}).",
            False,
        )
