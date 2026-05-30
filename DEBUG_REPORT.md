# Debug Report

## Scope

- Forecast node inputs/outputs and weather history checks
- Classifier inputs, model load, and probabilities
- News query relevance and headline filtering
- Severity assessor config and error visibility
- End-to-end state logging after each node

## Findings

- **Weather ingestion**: Recent weather history in [backend/storage/data/environmental_history.csv](backend/storage/data/environmental_history.csv) shows rainfall of `0.0` for the entire period inspected, which drives a flat forecast and makes downstream outputs look unrealistic.
- **Forecast**: Prophet only uses the last 72 hourly points (3 days). With near-zero rainfall history, the forecast will stay flat and `predicted_rainfall` will be near 0.
- **Classifier**: The model is trained on synthetic data with broader rainfall ranges; when live inputs are near zero, probabilities skew to "Normal". This is expected given current inputs, not a loading failure.
- **News monitoring**: Location-only queries can return unrelated headlines. Filtering is needed to keep hazard-related context for the LLM.
- **Severity assessor**: The LLM path has seen rate limits (429). When rate limited or misconfigured, the severity falls back, which can look unrealistic.

## Fixes Applied (Debug Only)

- Added detailed logging for weather ingestion source, rainfall stats, and time range in [backend/agents/environmental_data.py](backend/agents/environmental_data.py).
- Added forecast input/output summaries and short-history warnings in [backend/agents/forecasting.py](backend/agents/forecasting.py).
- Added classifier input and probability logging, plus model load details in [backend/models/disaster_inference.py](backend/models/disaster_inference.py) and [backend/agents/disaster_prediction.py](backend/agents/disaster_prediction.py).
- Improved news query relevance and applied hazard-keyword filtering with counts logged in [backend/agents/news_monitor.py](backend/agents/news_monitor.py).
- Added safe LLM config logging and state summaries in [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py).
- Added per-node state summaries for router and department nodes in [backend/agents/router.py](backend/agents/router.py), [backend/agents/public_works.py](backend/agents/public_works.py), [backend/agents/civil_defense.py](backend/agents/civil_defense.py), and [backend/agents/emergency_response.py](backend/agents/emergency_response.py).

## Failing Nodes

- **Severity assessor**: Rate limited (429) or invalid LLM responses can trigger fallback severity.

## Likely Causes of Unrealistic Outputs

- Rainfall inputs are all zeros, so forecast and classifier outputs stay low/normal.
- Limited history (72 points) reduces Prophet stability.
- News headlines can be unrelated without hazard-focused query terms.
- LLM rate limits can force fallback severity.

## Remaining Issues / Next Checks

- Verify Open-Meteo rainfall by querying the API directly for the same coordinates and time range.
- Run a workflow and inspect logs to confirm:
  - weather source (`live`, `cache`, or `synthetic`)
  - rainfall mean/min/max
  - forecast mean/min/max
  - classifier probabilities
  - news filter results
  - severity node LLM config and errors
- If rainfall is legitimately zero, consider validating the model on dry-region data before expecting higher severities.
- Isolated LLM test (manual): make a single request to the configured `LLM_BASE_URL` using the same `LLM_MODEL` to confirm quota and response format.
