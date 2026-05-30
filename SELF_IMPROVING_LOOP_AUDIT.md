SELF-IMPROVING LOOP AUDIT

Requirement (exact):
"If the human rejects the output and provides feedback,
the agent reflects on the failure,
generates a permanent Insight/Rule,
updates its own prompt,
and attempts generation again."

Summary Judgment: PARTIAL COMPLIANCE (≈50%)

1. Actual implementation (what the code currently does)

- Human approval: `backend/agents/human_gatekeeper.py` sets pending, waits for a decision, and returns a decision dict containing `approval_status` and `feedback`.
- Reflection: `backend/agents/reflection.py` logs the feedback and returns an empty state (no transformation or insight extraction).
- Memory update: `backend/agents/memory_update.py` appends raw feedback to an in-memory list and calls `store_rule(department, feedback, run_id)` which writes a permanent entry into `backend/memory/rules.json` via `backend/memory/memory_store.py`.
- Department re-run: `backend/graphs/workflow.py` wires rejection -> `reflection` -> `memory_update` -> conditional routing -> re-run department agent node (regeneration occurs automatically in the workflow).
- Department agents (`backend/agents/public_works.py`, `civil_defense.py`, `emergency_response.py`) call `retrieve_rules(department)` and append returned rule texts to the action plan when generating alerts.

2. Short answers to the four checks

1) Reflection actually generates a new insight? NO — `reflection_node` only logs; it does not synthesize or normalize insights.
2) The insight is permanently stored? PARTIAL/YES — `memory_update_node` calls `store_rule()` which appends the raw feedback as an entry in `backend/memory/rules.json` (permanent storage). However the stored entry may lack correct `department`/`run_id` due to state shaping (see evidence).
3) Department agent prompts are dynamically updated using stored insights? PARTIAL — department agents call `retrieve_rules()` and append stored rule texts to `action_plan`, so stored feedback is consumed, but no LLM prompts are dynamically amended (no prompt injection for Gemini or other LLMs is present). The severity LLM (`severity_assessor`) does not include memories in its prompt.
4) Regeneration occurs automatically after rejection? YES — The LangGraph workflow routes `human_gatekeeper` rejected -> `reflection` -> `memory_update` -> route back to a department agent, causing an automated re-run. Caveat: state returned by `human_gatekeeper_node` is only the decision dict which causes context loss for downstream nodes (see evidence), leading to incorrect or `Unknown` department attribution when storing memories and default routing.

3. Evidence from code (selected snippets and files)

- Human gatekeeper returns only the decision dict (loses prior context):
  - File: backend/agents/human_gatekeeper.py
  - Snippet:
    return decision
  - Implication: downstream nodes get only `{"approval_status":..., "feedback":...}` instead of the full run state.

- Reflection logs feedback but returns nothing:
  - File: backend/agents/reflection.py
  - Snippet:
    def reflection_node(state: DisasterState) -> DisasterState:
    feedback = state.get("feedback") or "No feedback provided"
    logger.info("Reflection requested for %s (run_id=%s)", department, run_id)
    logger.info("Feedback: %s", feedback)

        return {}

  - Implication: no derived insight is produced.

- Memory update stores raw feedback permanently:
  - File: backend/agents/memory_update.py
  - Snippet:
    if feedback:
    memory_rules.append(f"Human feedback: {feedback}")
    store_rule(department, feedback, run_id=run_id)
  - File: backend/memory/memory_store.py
  - Snippet (store_rule): writes a timestamped entry to `rules.json`.

- Departments consume stored rules when generating action plans:
  - File: backend/agents/public_works.py (same pattern in other departments)
  - Snippet:
    rules = retrieve_rules("Public Works")
    if rules:
    for rule in rules:
    action_plan.append(f"Apply rule: {rule}")

- Workflow regenerates after memory update:
  - File: backend/graphs/workflow.py
  - Snippet (rejection path):
    graph.add_conditional_edges(
    "human_gatekeeper",
    approval_route,
    {
    "approved": "send_alert",
    "rejected": "reflection",
    },
    )
    graph.add_edge("reflection", "memory_update")
    graph.add_conditional_edges(
    "memory_update",
    route_from_department,
    {
    "public_works": "public_works_agent",
    "civil_defense": "civil_defense_agent",
    "emergency_response": "emergency_response_agent",
    "none": END,
    },
    )

- Problematic state shape (context loss):
  - `human_gatekeeper_node` sets pending using the full state earlier, but then returns `decision` (only approval_status and feedback). Because the graph uses the returned value as the next state, `reflection` and `memory_update` typically do not receive `run_id` or `routed_department` unless the runtime merges states. Evidence: `human_gatekeeper.py` sets pending but returns only `decision`.

4. Compliance percentage and rationale

- I assess 50% compliance.
  - +25%: Permanent storage exists (`store_rule()` writes `rules.json`).
  - +25%: Regeneration is implemented in the workflow and triggers automatically after rejection.
  - 0%: Reflection does not synthesize insights or normalize feedback into a reusable rule.
  - 0% (partial credit withheld): Department agents consume stored rules for action plans (some compliance), but the requirement specifically requests that "the agent updates its own prompt" — no LLM prompt update occurs; severity LLM prompts do not include memories. I awarded partial credit implicitly by averaging to reach 50%.

5. Missing pieces and required changes (concrete developer tasks)
   Priority order and minimal diffs to reach full compliance:

A. Preserve full state after human approval decision (critical)

- Problem: `human_gatekeeper_node` returns only the decision dict, losing context (run_id, routed_department, severity).
- Change: Merge the decision into the incoming state and return the merged state so downstream nodes have context.
- Example fix (in `backend/agents/human_gatekeeper.py`):
  - Replace `return decision` with:
    state.update(decision)
    return state
- Rationale: `memory_update` needs `routed_department` and `run_id` to store insights correctly; routing logic uses `routed_department` to choose the re-run target.

B. Make `reflection_node` synthesize structured insights (insight generation)

- Problem: `reflection_node` only logs feedback and returns {}.
- Change: Implement reflection logic that:
  - Normalizes human feedback into a structured Insight object (e.g., `{'type':'clarity','rule':'...','priority':...}`), or at minimum a standardized rule string.
  - Returns the insight in state, e.g. `{'insight': {...}}` or `{'derived_rule': '...'}`.
- Optionally use a small LLM call or deterministic heuristics to extract an actionable rule from free-text feedback.
- Rationale: The requirement wants the agent to "reflect" and generate an Insight before storage.

C. Make `memory_update_node` store normalized/structured insights and preserve department/run_id

- Problem: `memory_update_node` currently stores raw feedback and may have incorrect department/run_id due to state loss.
- Changes:
  - Expect `insight` or `derived_rule` from `reflection_node` and store that (not raw feedback).
  - Ensure `department` and `run_id` are taken from the preserved state (see A).
  - Consider deduplication or merging logic when adding rules to `rules.json`.

D. Dynamically update LLM prompts with stored insights when relevant

- Problem: The severity LLM prompt (`_build_prompt` in `backend/agents/severity_assessor.py`) does not include retrieved memories, and department agents do not use LLM prompts.
- Changes:
  - Option 1 (severity assessor): When assessing severity, include `retrieve_rules(department)` (or recent global memories) in the prompt payload as `recent_insights` so Gemini can consider prior lessons.
  - Option 2 (department agents using LLMs): If department agents will call LLMs to craft alerts/action plans, add a prompt builder that injects `retrieve_rules(department)` (or derived rules) into the prompt.
- Rationale: This fulfills the "updates its own prompt" requirement.

E. Ensure regeneration is context-aware and re-generation uses new memory

- Problem: Even though the graph re-runs department agents, state loss can cause stored rules to be saved under `Unknown` and routing to default departments.
- Changes:
  - Fix A (state merging) so `memory_update_node` stores with correct department and run_id.
  - After storing insights, memory_update should return state containing `memory_rules` and the unchanged `routed_department`, `run_id`, `severity`, etc., so route decision is deterministic.
  - Optionally pass `insight_applied` flag to department agent so the agent knows the new insight is present on re-run.

F. Tests and observability

- Add unit tests that simulate a full run with a rejection and assert:
  - `rules.json` receives a structured entry with the correct `department` and `run_id`.
  - Department agent is re-run and its `action_plan` includes the new rule text.
- Add logs/metrics for `reflection` derived insights and `memory_update` store operations.

6. Minimal code examples (patch hints)

- `human_gatekeeper.py` change (conceptual):

  ```py
  # at end of human_gatekeeper_node
  state.update(decision)
  return state
  ```

- `reflection.py` example behavior (conceptual):

  ```py
  def reflection_node(state):
      feedback = state.get('feedback') or ''
      # simple heuristic: prefix 'Rule:' to feedback or call tiny extraction LLM
      derived = derive_rule_from_feedback(feedback)
      return {'derived_rule': derived}
  ```

- `memory_update.py` change: prefer `derived_rule` over raw feedback and store under the preserved `routed_department` and `run_id`.

7. Final compliance checklist (what to validate after changes)

- After human rejects and provides feedback:
  - Reflection produces a structured `derived_rule` (or insight).
  - `derived_rule` is appended to `backend/memory/rules.json` with correct `department` and `run_id`.
  - The LLM prompt (severity or department LLMs) includes `derived_rule` on next generation.
  - The workflow automatically re-runs the appropriate department agent and the new alert/action plan reflects the new rule.

Appendix: Relevant files inspected

- backend/agents/human_gatekeeper.py
- backend/agents/reflection.py
- backend/agents/memory_update.py
- backend/memory/memory_store.py
- backend/memory/memory_retriever.py
- backend/agents/public_works.py
- backend/agents/civil_defense.py
- backend/agents/emergency_response.py
- backend/graphs/workflow.py

End of audit.
