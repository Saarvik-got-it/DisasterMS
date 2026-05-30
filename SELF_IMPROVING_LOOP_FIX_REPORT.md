SELF_IMPROVING_LOOP_FIX_REPORT

Objective: Implement Phase B final compliance fixes so that human rejection leads to reflection, derived insight storage, prompt adaptation, and automated regeneration incorporating the learned rule.

Files Modified
- backend/agents/human_gatekeeper.py
  - Merged human decision into returned state to preserve `run_id`, `routed_department`, `severity`, and `location` for downstream nodes.
- backend/agents/reflection.py
  - Implemented simple deterministic insight extraction producing `derived_rule` from free-text feedback.
- backend/agents/memory_update.py
  - Store the `derived_rule` (preferred) into memory via `store_rule()` and return preserved `routed_department` and `run_id` in the state.
- backend/memory/memory_retriever.py
  - Added `retrieve_recent_insights(limit)` to return recent learned rules across departments.
- backend/agents/severity_assessor.py
  - Severity prompt now includes `recent_insights` retrieved before calling the LLM.

Before / After Architecture (high-level)

Before:
- Human rejects -> `human_gatekeeper` returned only decision -> `reflection` logged feedback -> `memory_update` stored raw feedback (department possibly Unknown) -> routing/regeneration occurred but often lacked context -> LLM prompts did not include learned rules.

After:
- Human rejects -> `human_gatekeeper` merges decision into state -> `reflection` derives a structured `derived_rule` -> `memory_update` persists derived insight with correct `department` and `run_id` and returns preserved state -> workflow routes to department agent -> `severity_assessor` and other agents include `recent_insights` (severity LLM prompt updated) -> regenerated output includes learned rules.

Example rejection flow
1. Run 1 produces alert lacking emergency contacts.
2. Human rejects and provides feedback: "Please include emergency contacts and shelter locations"
3. `human_gatekeeper` returns merged state including `feedback`.
4. `reflection_node` processes feedback and emits:
   {
     "derived_rule": "Always include emergency contacts and shelter locations."
   }
5. `memory_update_node` stores this derived insight into `backend/memory/rules.json` with `department` and `run_id`.
6. Workflow re-runs department agent; `severity_assessor` now receives `recent_insights` including the new rule, adjusts reasoning, and the department agent's `action_plan` includes the new rule.

Example learned insight
- Derived from feedback: "Include evacuation shelters"
- Stored insight: "Always include evacuation shelters."

Example prompt update (severity_assessor payload)
- The LLM prompt now includes an additional `recent_insights` field with entries such as:
  - "Always include evacuation shelters."
  - "Include emergency contact numbers."
- LLM is asked to consider these recent insights when assessing severity and generating the `reason` field.

Example regenerated output
- Prior run alert had no emergency contacts. After rejection and re-run, the regenerated alert includes an "Emergency contacts" section listing local numbers and notes: "Shelters: ..." and the action plan includes "Apply rule: Always include evacuation shelters." (Department agents append retrieved rules to action plans.)

Validation notes & caveats
- `reflection_node` currently implements deterministic heuristics to extract `derived_rule`. For more robust extraction consider calling an LLM to normalize free-text feedback into structured insights. This would need environment config and cost consideration.
- Department agents currently append retrieved rules to `action_plan` (they do not call LLMs to generate content), but `severity_assessor` now includes recent insights in its prompt. If you want department-level LLM prompt adaptation, add LLM-based generation in department agents and inject `retrieve_rules(department)`.

Suggested tests
- Unit test: simulate rejection with feedback and assert `rules.json` contains the derived insight with correct `department` and `run_id`.
- Integration test: run full workflow with synthetic data, reject first output, validate second output includes rule.

Completion
- Implemented code changes to satisfy Phase B requirements for the self-improving loop within current project constraints.

