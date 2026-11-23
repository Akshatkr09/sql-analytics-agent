# NeMo Guardrails configuration

The application loads this directory with `RailsConfig.from_path()` and invokes
NeMo's check-only input-rail API before the LangGraph workflow. No NeMo model is
configured because Gemini is the project's generation model and the guardrail
pass must not generate a second answer. A deterministic local screening layer
always runs first; it remains active if the installed NeMo release does not
support the check-only API/configuration combination.
