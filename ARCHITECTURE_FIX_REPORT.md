ARCHITECTURE FIX REPORT

Summary

- Problem: System used deterministic classifier mappings and a `Normal` shortcut that bypassed the LLM (Gemini). Severity outputs from Gemini were sometimes overwritten by classifier heuristics and routing used classifier predictions instead of LLM severity.
- Goal: Make Gemini the authoritative source for severity, remove deterministic overrides and `Normal` shortcut, route by severity, and surface explainability fields (`severity_reason`, `routing_reason`, `classifier_mapped_severity`).

Files Modified

- backend/agents/severity_assessor.py
  - Removed the `Normal` shortcut that skipped the LLM.
  - Removed deterministic overwrite of Gemini's severity with classifier mapping.
  - Enhanced prompt to include `prediction_confidences` and `news_headlines` and updated instructions to an emergency-operations-analyst persona.
  - Returned `classifier_mapped_severity` in the state for transparency.
- backend/validation/state_validator.py
  - Changed behavior to NOT overwrite valid `severity` values. Default `severity` to `LOW` only when missing/invalid.
  - No longer forces `routed_department` from classifier outputs; uses existing `routed_department` when present and falls back to classifier mapping only for alert generation.
- backend/agents/router.py
  - Routing now uses `severity` to decide department: LOW -> None, MEDIUM -> Public Works, HIGH -> Civil Defense, CRITICAL -> Emergency Response.
  - Adds `routing_reason` to state explaining the routing decision.
- README_ARCHITECTURE.md
  - Documented the corrected workflow: Gemini authoritative, router routes by severity, explainability fields included.

Rationale

- Authoritative LLM: Gemini was already being used for nuanced severity reasoning; forcing deterministic mappings negated LLM benefits and reduced explainability.
- Explainability: Keeping classifier mapping and routing reasons in the state preserves auditability and allows humans to compare LLM vs classifier reasoning.
- Routing by severity: Operational teams act on severity, not on classifier labels. Making routing severity-driven simplifies decision-making.

Notes and Next Steps

- Ensure downstream department agents consume `routing_reason` and include it in generated alerts/action plans if helpful.
- Consider adding unit tests validating routing logic for each severity level and integration tests ensuring `severity_reason`/`routing_reason` are present in run outputs.
- Update any external documentation or frontend displays to show `severity_reason`, `classifier_mapped_severity`, and `routing_reason` for transparency.

End of report.
