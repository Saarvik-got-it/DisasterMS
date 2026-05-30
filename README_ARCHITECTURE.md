# Project Architecture

## 1. Executive Summary

This project delivers an end-to-end disaster management workflow that ingests weather observations, forecasts rainfall, predicts disaster likelihood, enriches context with news, assigns a severity, routes the case to a department, and pauses for human approval before sending alerts. The system is designed to be auditable: deterministic ML drives prediction, an LLM provides severity synthesis, and a validation layer repairs inconsistencies before the frontend sees results.

End-to-end workflow:

1. Location input (map or search)
2. Weather ingestion (Open-Meteo)
3. Forecast (Prophet)
4. Disaster classification (RandomForest)
5. News context (NewsAPI/GNews)
6. Severity assessment (Gemini)
7. Routing (risk mapping)
8. Department agent action plan
9. Human approval gate
10. Alert sender (placeholder)

High-level architecture:

```mermaid
flowchart LR
    User[User input] --> FE[Next.js Dashboard]
    FE --> API[FastAPI /run]
    API --> Graph[LangGraph workflow]

    Graph --> Weather[Environmental data ingestion]
    Weather --> Forecast[Prophet forecast]
    Forecast --> Predict[ML classifier]
    Forecast --> News[News monitoring]
    Predict --> Severity[Gemini severity (authoritative)]
    News --> Severity
    Severity --> Router[Router (routes by severity -> department)]
    Router --> Dept[Department agent]
    Dept --> Gate[Human gatekeeper]
    Gate --> Alert[Alert sender]

    Graph --> Validate[State validation]
    Validate --> API
    API --> FE
```

## 2. Technology Stack

**Backend**

- **FastAPI** (framework): HTTP API for workflow execution and approval endpoints. Used in [backend/api/main.py](backend/api/main.py).
- **Python** (language): all backend logic and ML pipeline.
- **LangGraph** (agent framework): state machine orchestration for node-based workflow. Used in [backend/graphs/workflow.py](backend/graphs/workflow.py).
- **Pydantic** (schema validation): request/response models in [backend/models/schemas.py](backend/models/schemas.py).
- **httpx** (HTTP client): external API calls for weather, news, and LLM.
- **python-dotenv** (configuration): auto-loads backend environment variables in [backend/api/main.py](backend/api/main.py).

**Forecasting + ML**

- **Prophet** (forecasting): time-series rainfall forecast in [backend/agents/forecasting.py](backend/agents/forecasting.py).
- **scikit-learn** (ML): RandomForest classifier for disaster prediction in [backend/models/train_classifier.py](backend/models/train_classifier.py).
- **numpy/pandas** (data): dataset generation, transforms, and feature handling.
- **matplotlib** (plots): confusion matrix and forecast charts.

**LLM**

- **Google Gemini REST API** (LLM reasoning): severity assessment in [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py). No LLM framework; direct REST calls via httpx.

**Frontend**

- **Next.js App Router** (framework) and **React** (UI): dashboard and pages under [frontend/src/app](frontend/src/app).
- **Tailwind CSS** (styling): utility-first styling in [frontend/src/app/globals.css](frontend/src/app/globals.css).
- **shadcn/ui + Radix primitives** (UI components): components under [frontend/src/components/ui](frontend/src/components/ui).
- **React Leaflet + Leaflet** (maps): map selection in [frontend/src/components/dashboard/map-inner.tsx](frontend/src/components/dashboard/map-inner.tsx).

**APIs**

- **Open-Meteo**: weather ingestion.
- **NewsAPI/GNews**: headline context.
- **OpenStreetMap + Nominatim**: map tiles and location search.
- **Gemini**: severity assessment.

**Deployment**

- No deployment scripts or cloud config in code. Local execution via uvicorn and Next dev server. Deployment platform is **Unable to determine from code**.

## 3. Folder Structure

Top-level structure and purpose (vendor/build folders are listed but not expanded):

- [ARCHITECTURE.md](ARCHITECTURE.md) - existing architecture summary.
- [DEBUG_REPORT.md](DEBUG_REPORT.md) - debugging notes from previous sessions.
- [LLM_GEMINI_ERROR_REPORT.md](LLM_GEMINI_ERROR_REPORT.md) - Gemini error analysis.
- [README.md](README.md) - primary project documentation.
- [requirements.txt](requirements.txt) - backend dependencies.
- [backend/](backend/) - FastAPI app, LangGraph workflow, ML, and storage.
  - [.env](backend/.env) - backend environment variables (keys not documented here).
  - [**init**.py](backend/__init__.py) - package marker (empty).
  - [agents/](backend/agents/) - workflow nodes and agents.
    - [civil_defense.py](backend/agents/civil_defense.py)
    - [disaster_prediction.py](backend/agents/disaster_prediction.py)
    - [emergency_response.py](backend/agents/emergency_response.py)
    - [environmental_data.py](backend/agents/environmental_data.py)
    - [forecasting.py](backend/agents/forecasting.py)
    - [human_gatekeeper.py](backend/agents/human_gatekeeper.py)
    - [memory_update.py](backend/agents/memory_update.py)
    - [news_monitor.py](backend/agents/news_monitor.py)
    - [notification_sender.py](backend/agents/notification_sender.py)
    - [public_works.py](backend/agents/public_works.py)
    - [reflection.py](backend/agents/reflection.py)
    - [router.py](backend/agents/router.py)
    - [severity_assessor.py](backend/agents/severity_assessor.py)
    - [**init**.py](backend/agents/__init__.py) - package marker (empty).
  - [api/](backend/api/) - FastAPI entrypoint.
    - [main.py](backend/api/main.py)
    - [**init**.py](backend/api/__init__.py) - package marker (empty).
  - [graphs/](backend/graphs/) - LangGraph state and workflow.
    - [state.py](backend/graphs/state.py)
    - [workflow.py](backend/graphs/workflow.py)
    - [**init**.py](backend/graphs/__init__.py) - package marker (empty).
  - [memory/](backend/memory/) - persistent memory store.
    - [memory_retriever.py](backend/memory/memory_retriever.py)
    - [memory_store.py](backend/memory/memory_store.py)
    - [rules.json](backend/memory/rules.json)
    - [rules.py](backend/memory/rules.py)
    - [**init**.py](backend/memory/__init__.py) - package marker (empty).
  - [models/](backend/models/) - ML models and schemas.
    - [disaster_classifier.pkl](backend/models/disaster_classifier.pkl) - trained model artifact.
    - [disaster_inference.py](backend/models/disaster_inference.py)
    - [feature_spec.py](backend/models/feature_spec.py)
    - [schemas.py](backend/models/schemas.py)
    - [synthetic_data.py](backend/models/synthetic_data.py)
    - [train_classifier.py](backend/models/train_classifier.py)
    - [**init**.py](backend/models/__init__.py) - package marker (empty).
  - [services/](backend/services/) - helpers and utilities.
    - [alert_builder.py](backend/services/alert_builder.py)
    - [risk_mapping.py](backend/services/risk_mapping.py)
    - [run_history.py](backend/services/run_history.py)
    - [**init**.py](backend/services/__init__.py) - package marker (empty).
  - [storage/](backend/storage/) - local file storage.
    - [data/](backend/storage/data/)
      - [disaster_training.csv](backend/storage/data/disaster_training.csv)
      - [environmental_history.csv](backend/storage/data/environmental_history.csv)
      - [runs_log.json](backend/storage/data/runs_log.json)
    - [plots/](backend/storage/plots/)
      - [disaster_classification_report.txt](backend/storage/plots/disaster_classification_report.txt)
      - [disaster_confusion_matrix.png](backend/storage/plots/disaster_confusion_matrix.png)
      - [rainfall_forecast.png](backend/storage/plots/rainfall_forecast.png)
  - [validation/](backend/validation/) - validation layer.
    - [state_validator.py](backend/validation/state_validator.py)
- [frontend/](frontend/) - Next.js frontend.
  - [.env.local](frontend/.env.local) - frontend environment variables.
  - [.gitignore](frontend/.gitignore)
  - [.next/](frontend/.next/) - build output (not expanded).
  - [AGENTS.md](frontend/AGENTS.md)
  - [CLAUDE.md](frontend/CLAUDE.md)
  - [components.json](frontend/components.json) - shadcn/ui config.
  - [eslint.config.mjs](frontend/eslint.config.mjs)
  - [next-env.d.ts](frontend/next-env.d.ts)
  - [next.config.ts](frontend/next.config.ts)
  - [node_modules/](frontend/node_modules/) - frontend dependencies (not expanded).
  - [package-lock.json](frontend/package-lock.json)
  - [package.json](frontend/package.json)
  - [postcss.config.mjs](frontend/postcss.config.mjs)
  - [public/](frontend/public/)
    - [file.svg](frontend/public/file.svg)
    - [globe.svg](frontend/public/globe.svg)
    - [next.svg](frontend/public/next.svg)
    - [vercel.svg](frontend/public/vercel.svg)
    - [window.svg](frontend/public/window.svg)
  - [README.md](frontend/README.md)
  - [src/](frontend/src/)
    - [app/](frontend/src/app/)
      - [favicon.ico](frontend/src/app/favicon.ico)
      - [globals.css](frontend/src/app/globals.css)
      - [layout.tsx](frontend/src/app/layout.tsx)
      - [page.tsx](frontend/src/app/page.tsx)
      - [history/](frontend/src/app/history/)
        - [page.tsx](frontend/src/app/history/page.tsx)
      - [settings/](frontend/src/app/settings/)
        - [page.tsx](frontend/src/app/settings/page.tsx)
    - [components/](frontend/src/components/)
      - [dashboard/](frontend/src/components/dashboard/)
        - [forecast-chart.tsx](frontend/src/components/dashboard/forecast-chart.tsx)
        - [map-inner.tsx](frontend/src/components/dashboard/map-inner.tsx)
        - [map-picker.tsx](frontend/src/components/dashboard/map-picker.tsx)
        - [section-card.tsx](frontend/src/components/dashboard/section-card.tsx)
        - [stat-card.tsx](frontend/src/components/dashboard/stat-card.tsx)
        - [status-pill.tsx](frontend/src/components/dashboard/status-pill.tsx)
      - [layout/](frontend/src/components/layout/)
        - [top-nav.tsx](frontend/src/components/layout/top-nav.tsx)
      - [ui/](frontend/src/components/ui/)
        - [badge.tsx](frontend/src/components/ui/badge.tsx)
        - [button.tsx](frontend/src/components/ui/button.tsx)
        - [card.tsx](frontend/src/components/ui/card.tsx)
        - [input.tsx](frontend/src/components/ui/input.tsx)
        - [scroll-area.tsx](frontend/src/components/ui/scroll-area.tsx)
        - [separator.tsx](frontend/src/components/ui/separator.tsx)
        - [skeleton.tsx](frontend/src/components/ui/skeleton.tsx)
        - [tabs.tsx](frontend/src/components/ui/tabs.tsx)
        - [textarea.tsx](frontend/src/components/ui/textarea.tsx)
    - [lib/](frontend/src/lib/)
      - [api.ts](frontend/src/lib/api.ts)
      - [types.ts](frontend/src/lib/types.ts)
      - [utils.ts](frontend/src/lib/utils.ts)
- [venv/](venv/) - Python virtual environment (not expanded).

## 4. Backend Architecture

Each backend file, its purpose, interfaces, and dependencies:

### API Layer

- [backend/api/main.py](backend/api/main.py)
  - Purpose: FastAPI entrypoint and API routes.
  - Key functions: `health_check()`, `run_workflow()`, `approve_alert()`, `reject_alert()`, `get_memory_rules()`, `get_run_history()`, `get_pending_approval()`.
  - Inputs: JSON payloads defined by `RunRequest`, `ApprovalRequest`.
  - Outputs: JSON responses defined by `RunResponse`, `ApprovalResponse`, `MemoryRulesResponse`, `RunHistoryResponse`, `PendingApprovalResponse`.
  - Dependencies: FastAPI, `build_graph()`, `validate_and_repair_state()`, `append_run_log()`.

### Graph Layer

- [backend/graphs/state.py](backend/graphs/state.py)
  - Purpose: Defines the `DisasterState` typed dict.
  - Inputs/Outputs: Shared state keys for LangGraph nodes.
  - Dependencies: typing only.
- [backend/graphs/workflow.py](backend/graphs/workflow.py)
  - Purpose: Defines the LangGraph workflow and routing.
  - Key function: `build_graph()`.
  - Inputs: `DisasterState` payload with `location` and `run_id`.
  - Outputs: Workflow result state.
  - Dependencies: all agents and `langgraph`.

### Agents

- [backend/agents/environmental_data.py](backend/agents/environmental_data.py)
  - Purpose: Weather ingestion and caching.
  - Key functions: `fetch_environmental_data()`, `build_synthetic_weather()`, `store_historical_csv()`, `ingest_environmental_data()`.
  - Inputs: `location` with latitude/longitude.
  - Outputs: `weather_data` list of records.
  - Dependencies: Open-Meteo API, pandas, httpx.
- [backend/agents/forecasting.py](backend/agents/forecasting.py)
  - Purpose: Rainfall forecast and feature extraction.
  - Key functions: `prepare_prophet_frame()`, `summarize_recent_conditions()`, `run_rainfall_forecast()`, `save_forecast_plot()`, `forecast_rainfall()`.
  - Inputs: `weather_data` records.
  - Outputs: `forecast` with points, plot path, and features.
  - Dependencies: Prophet, pandas, matplotlib.
- [backend/agents/disaster_prediction.py](backend/agents/disaster_prediction.py)
  - Purpose: Run classifier inference.
  - Key function: `disaster_prediction_node()`.
  - Inputs: `forecast.features`.
  - Outputs: `disaster_prediction` probabilities with `most_likely`.
  - Dependencies: `predict_disaster()`.
- [backend/agents/news_monitor.py](backend/agents/news_monitor.py)
  - Purpose: Fetch and filter disaster-related headlines.
  - Key functions: `_build_news_query()`, `_score_relevance()`, `filter_relevant_headlines()`, `fetch_local_news()`, `news_monitor_node()`.
  - Inputs: `location`.
  - Outputs: `news_context` list of headlines.
  - Dependencies: NewsAPI/GNews, httpx.
- [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py)
  - Purpose: Gemini-based severity assessment and fallback logic. Gemini (LLM) is authoritative for final severity; prompts include forecast features, classifier probabilities (prediction_confidences), and recent news_headlines to support explainable reasoning.
  - Key functions: `_build_prompt()`, `_invoke_llm()`, `_extract_json_object()`, `assess_severity()`, `severity_assessor_node()`.
  - Inputs: `forecast.features`, `disaster_prediction`, `prediction_confidences`, `news_context`.
  - Outputs: `severity`, `severity_reason`, `classifier_mapped_severity` (for transparency).
  - Dependencies: Gemini REST API, `SeverityAssessment`.
- [backend/agents/router.py](backend/agents/router.py)
  - Purpose: Route workflow by `severity` (LLM authoritative). Maps severity to departmental routing and records `routing_reason` for explainability.
  - Key functions: `routing_node()`, `route_from_department()`.
  - Inputs: `severity`, `disaster_prediction` (for logging/traceability).
  - Outputs: `routed_department`, `routing_reason`.
  - Dependencies: none (routing is severity-driven).
- [backend/agents/public_works.py](backend/agents/public_works.py)
  - Purpose: Public Works alert and action plan.
  - Key function: `public_works_node()`.
  - Inputs: `location`, `severity`, `news_context`, `disaster_prediction`, `feedback`.
  - Outputs: `generated_alert`, `action_plan`.
  - Dependencies: `build_alert_message()`, `retrieve_rules()`.
- [backend/agents/civil_defense.py](backend/agents/civil_defense.py)
  - Purpose: Civil Defense alert and action plan.
  - Key function: `civil_defense_node()`.
  - Inputs/Outputs: same pattern as Public Works.
  - Dependencies: `build_alert_message()`, `retrieve_rules()`.
- [backend/agents/emergency_response.py](backend/agents/emergency_response.py)
  - Purpose: Emergency Response alert and action plan.
  - Key function: `emergency_response_node()`.
  - Inputs/Outputs: same pattern as Public Works.
  - Dependencies: `build_alert_message()`, `retrieve_rules()`.
- [backend/agents/human_gatekeeper.py](backend/agents/human_gatekeeper.py)
  - Purpose: Human approval gate and pending store.
  - Key functions: `set_decision()`, `await_human_decision()`, `set_pending()`, `get_pending()`, `approval_route()`, `human_gatekeeper_node()`.
  - Inputs: `generated_alert`, `action_plan`, `severity`, `routed_department`, `run_id`.
  - Outputs: `approval_status`, `feedback`.
  - Dependencies: threading primitives, environment variables for mode/timeout.
- [backend/agents/notification_sender.py](backend/agents/notification_sender.py)
  - Purpose: Placeholder alert sender.
  - Key function: `send_alert_node()`.
  - Inputs: `generated_alert`, `action_plan`, `routed_department`.
  - Outputs: none (logs only).
- [backend/agents/reflection.py](backend/agents/reflection.py)
  - Purpose: Log rejection feedback.
  - Key function: `reflection_node()`.
  - Inputs: `feedback`, `routed_department`, `run_id`.
  - Outputs: none.
- [backend/agents/memory_update.py](backend/agents/memory_update.py)
  - Purpose: Persist feedback to memory rules.
  - Key function: `memory_update_node()`.
  - Inputs: `feedback`, `memory_rules`, `routed_department`, `run_id`.
  - Outputs: updated `memory_rules`.

### Models

- [backend/models/feature_spec.py](backend/models/feature_spec.py)
  - Purpose: Feature column order and labels.
  - Key constants: `FEATURE_COLUMNS`, `LABELS`.
- [backend/models/synthetic_data.py](backend/models/synthetic_data.py)
  - Purpose: Generate synthetic training data.
  - Key function: `generate_synthetic_dataset()`.
  - Inputs: output path, sample size, seed.
  - Outputs: CSV and DataFrame with `label`.
- [backend/models/train_classifier.py](backend/models/train_classifier.py)
  - Purpose: Train and persist RandomForest classifier.
  - Key functions: `train_classifier()`, `main()`.
  - Inputs: dataset path, model path, plots dir.
  - Outputs: `disaster_classifier.pkl`, plots, report.
- [backend/models/disaster_inference.py](backend/models/disaster_inference.py)
  - Purpose: Load model and run inference.
  - Key functions: `load_disaster_model()`, `predict_disaster()`.
  - Inputs: forecast feature mapping.
  - Outputs: probability mapping plus `most_likely`.
- [backend/models/schemas.py](backend/models/schemas.py)
  - Purpose: Pydantic API schemas.
  - Classes: `RunRequest`, `RunResponse`, `SeverityAssessment`, `ApprovalRequest`, `ApprovalResponse`, `MemoryRulesResponse`, `RunHistoryResponse`, `PendingApprovalResponse`, plus data models.

### Services and Validation

- [backend/services/alert_builder.py](backend/services/alert_builder.py)
  - Purpose: Standardized alert message formatting.
  - Key function: `build_alert_message()`.
  - Inputs: department, location, risk type, severity, confidence, action plan.
  - Outputs: multi-line alert string.
- [backend/services/risk_mapping.py](backend/services/risk_mapping.py)
  - Purpose: Explicit hazard-to-severity and hazard-to-department mapping.
  - Key functions: `select_severity()`, `select_department()`.
- [backend/services/run_history.py](backend/services/run_history.py)
  - Purpose: Append and load run history log.
  - Key functions: `append_run_log()`, `load_run_history()`.
- [backend/validation/state_validator.py](backend/validation/state_validator.py)
  - Purpose: Validate and repair outputs before returning to frontend.
  - Key function: `validate_and_repair_state()`.
  - Inputs: workflow state.
  - Outputs: repaired state with clamped rainfall, corrected severity/department, filtered news, regenerated alerts.

### Memory

- [backend/memory/memory_store.py](backend/memory/memory_store.py)
  - Purpose: Persist memory rules to JSON.
  - Key functions: `store_rule()`, `load_rules()`.
- [backend/memory/memory_retriever.py](backend/memory/memory_retriever.py)
  - Purpose: Retrieve recent rules per department.
  - Key function: `retrieve_rules()`.
- [backend/memory/rules.py](backend/memory/rules.py)
  - Purpose: Default memory rules list.

## 5. Frontend Architecture

### Pages and Layout

- [frontend/src/app/layout.tsx](frontend/src/app/layout.tsx)
  - Purpose: App shell and global fonts/styles.
  - Components: `TopNav`, main content layout.
  - Props: `children`.
- [frontend/src/app/page.tsx](frontend/src/app/page.tsx)
  - Purpose: Main dashboard.
  - State: `locationName`, `latitude`, `longitude`, `searchQuery`, `searchResults`, `searchLoading`, `result`, `pendingList`, `activePendingId`, `memory`, `runs`, `loading`, `error`, `feedback`, `decision`.
  - API calls: `runWorkflow()`, `getPendingApproval()`, `getMemoryRules()`, `getRunHistory()`, `approveAlert()`, `rejectAlert()`.
  - Interactions: search Nominatim, select map, run workflow, approve/reject alerts, poll pending.
- [frontend/src/app/history/page.tsx](frontend/src/app/history/page.tsx)
  - Purpose: Run history listing.
  - State: `runs`, `loading`, `error`.
  - API calls: `getRunHistory()`.
- [frontend/src/app/settings/page.tsx](frontend/src/app/settings/page.tsx)
  - Purpose: Display frontend environment and approval notes.
  - State: none.

### Dashboard Components

- [frontend/src/components/dashboard/map-picker.tsx](frontend/src/components/dashboard/map-picker.tsx)
  - Purpose: Client-only map wrapper.
  - Props: `latitude`, `longitude`, `onSelect`.
  - Interactions: none (delegates to MapInner).
- [frontend/src/components/dashboard/map-inner.tsx](frontend/src/components/dashboard/map-inner.tsx)
  - Purpose: Leaflet map UI.
  - Props: `center`, `marker`, `onSelect`.
  - State: `ready` (client render), `mapKey` (re-mount).
  - Interactions: click map to set coordinates.
- [frontend/src/components/dashboard/forecast-chart.tsx](frontend/src/components/dashboard/forecast-chart.tsx)
  - Purpose: SVG rainfall chart.
  - Props: `points`.
- [frontend/src/components/dashboard/section-card.tsx](frontend/src/components/dashboard/section-card.tsx)
  - Purpose: Section container.
  - Props: `title`, `subtitle`, `children`.
- [frontend/src/components/dashboard/stat-card.tsx](frontend/src/components/dashboard/stat-card.tsx)
  - Purpose: Metric card.
  - Props: `title`, `value`, `description`.
- [frontend/src/components/dashboard/status-pill.tsx](frontend/src/components/dashboard/status-pill.tsx)
  - Purpose: Severity badge.
  - Props: `label`.

### Layout Components

- [frontend/src/components/layout/top-nav.tsx](frontend/src/components/layout/top-nav.tsx)
  - Purpose: Top navigation links.
  - Props: none.

### UI Primitives

- [frontend/src/components/ui/button.tsx](frontend/src/components/ui/button.tsx)
  - Purpose: Button with variants and sizes.
  - Props: `variant`, `size`, `asChild` plus native button props.
- [frontend/src/components/ui/input.tsx](frontend/src/components/ui/input.tsx)
  - Purpose: Styled input.
  - Props: native input props.
- [frontend/src/components/ui/textarea.tsx](frontend/src/components/ui/textarea.tsx)
  - Purpose: Styled textarea.
  - Props: native textarea props.
- [frontend/src/components/ui/badge.tsx](frontend/src/components/ui/badge.tsx)
  - Purpose: Badge variants.
  - Props: `variant`, `asChild` plus span props.
- [frontend/src/components/ui/card.tsx](frontend/src/components/ui/card.tsx)
  - Purpose: Card layout primitives.
  - Components: `Card`, `CardHeader`, `CardContent`, `CardFooter`, `CardTitle`, `CardDescription`, `CardAction`.
- [frontend/src/components/ui/scroll-area.tsx](frontend/src/components/ui/scroll-area.tsx)
  - Purpose: Scrollable container.
  - Components: `ScrollArea`, `ScrollBar`.
- [frontend/src/components/ui/separator.tsx](frontend/src/components/ui/separator.tsx)
  - Purpose: Divider.
- [frontend/src/components/ui/skeleton.tsx](frontend/src/components/ui/skeleton.tsx)
  - Purpose: Loading placeholder.
- [frontend/src/components/ui/tabs.tsx](frontend/src/components/ui/tabs.tsx)
  - Purpose: Tabs primitives and variants.

### Frontend Lib

- [frontend/src/lib/api.ts](frontend/src/lib/api.ts)
  - Purpose: Typed API client.
  - Functions: `runWorkflow()`, `approveAlert()`, `rejectAlert()`, `getMemoryRules()`, `getRunHistory()`, `getPendingApproval()`.
- [frontend/src/lib/types.ts](frontend/src/lib/types.ts)
  - Purpose: Shared data shapes for API payloads and responses.
- [frontend/src/lib/utils.ts](frontend/src/lib/utils.ts)
  - Purpose: `cn()` utility for class name merging.

## 6. API Integration Layer

External APIs in use:

1. **Open-Meteo**
   - Endpoint: `https://api.open-meteo.com/v1/forecast`
   - Request format: query parameters `latitude`, `longitude`, `hourly`, `past_days`, `forecast_days`, `timezone`.
   - Response format: JSON with `hourly` arrays for `time`, `temperature_2m`, `relative_humidity_2m`, `precipitation`, `wind_speed_10m`, `pressure_msl`.
   - Auth: none.
   - Called in: [backend/agents/environmental_data.py](backend/agents/environmental_data.py).

2. **NewsAPI**
   - Endpoint: `https://newsapi.org/v2/everything`
   - Request format: query params `q`, `language`, `pageSize`, `searchIn`, `sortBy`, `apiKey`.
   - Response format: JSON `articles[]` with `title` and optional `description`.
   - Auth: `apiKey` query parameter.
   - Called in: [backend/agents/news_monitor.py](backend/agents/news_monitor.py).

3. **GNews**
   - Endpoint: `https://gnews.io/api/v4/search`
   - Request format: query params `q`, `lang`, `max`, `token`.
   - Response format: JSON `items[]` with `title` and optional `description`.
   - Auth: `token` query parameter.
   - Called in: [backend/agents/news_monitor.py](backend/agents/news_monitor.py).

4. **Gemini**
   - Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
   - Request format: JSON `contents` with `parts.text`, `generationConfig`.
   - Response format: JSON `candidates[0].content.parts[0].text`.
   - Auth: `x-goog-api-key` header.
   - Called in: [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py).

5. **OpenStreetMap Nominatim**
   - Endpoint: `https://nominatim.openstreetmap.org/search`
   - Request format: `format=json`, `q`, `limit`.
   - Response format: array of results with `display_name`, `lat`, `lon`.
   - Auth: none.
   - Called in: [frontend/src/app/page.tsx](frontend/src/app/page.tsx).

6. **OpenStreetMap Tile Server**
   - Endpoint: `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`
   - Request format: Tile URL per Leaflet.
   - Response format: PNG tiles.
   - Auth: none.
   - Called in: [frontend/src/components/dashboard/map-inner.tsx](frontend/src/components/dashboard/map-inner.tsx).

## 7. State Management

### Backend Workflow State

`DisasterState` in [backend/graphs/state.py](backend/graphs/state.py):

- `run_id`: string
- `location`: dict with `latitude`, `longitude`, `name`
- `weather_data`: list of records
- `forecast`: dict with points, plot path, features
- `disaster_prediction`: dict of probabilities plus `most_likely`
- `news_context`: list of headlines
- `severity`: string
- `severity_reason`: string
- `routed_department`: string
- `generated_alert`: string
- `action_plan`: list of strings
- `feedback`: string
- `approval_status`: string
- `memory_rules`: list of strings

State flows through the LangGraph nodes in [backend/graphs/workflow.py](backend/graphs/workflow.py). Each node returns a partial dict that is merged into the global state.

### Frontend State

`RunState` in [frontend/src/lib/types.ts](frontend/src/lib/types.ts) mirrors backend outputs and is stored in React state in [frontend/src/app/page.tsx](frontend/src/app/page.tsx).

## 8. Agent Architecture

All agent nodes are in [backend/agents](backend/agents/).

- **Environmental Data Agent**
  - Purpose: Retrieve and normalize weather data.
  - Prompt: Not applicable (deterministic).
  - Inputs: `location`.
  - Outputs: `weather_data`.
  - Decision logic: Retry Open-Meteo, fallback to cache, optionally synthetic data.
  - Tools: httpx.
  - Memory: none.

- **Forecast Agent**
  - Purpose: Forecast rainfall and extract features.
  - Prompt: Not applicable.
  - Inputs: `weather_data`.
  - Outputs: `forecast`.
  - Decision logic: Reject empty series, clamp negative rainfall.
  - Tools: Prophet.
  - Memory: none.

- **Disaster Prediction Agent**
  - Purpose: ML inference for disaster class probabilities.
  - Prompt: Not applicable.
  - Inputs: `forecast.features`.
  - Outputs: `disaster_prediction`.
  - Decision logic: Validate required features.
  - Tools: scikit-learn model.
  - Memory: none.

- **News Monitoring Agent**
  - Purpose: Fetch and filter disaster-relevant headlines.
  - Prompt: Not applicable.
  - Inputs: `location`.
  - Outputs: `news_context`.
  - Decision logic: relevance scoring, exclude entertainment/tech, keep top scored.
  - Tools: httpx.
  - Memory: none.

- **Severity Assessor Agent**
  - Purpose: Synthesize severity with Gemini.
  - Prompt: Yes, built in `_build_prompt()` in [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py).
  - Inputs: `forecast.features`, `disaster_prediction`, `news_context`.
  - Outputs: `severity`, `severity_reason`.
  - Decision logic: skip LLM on `Normal`, map severity to prediction, fallback on errors.
  - Tools: Gemini REST API.
  - Memory: none.

- **Router Agent**
  - Purpose: Choose department based on hazard.
  - Prompt: Not applicable.
  - Inputs: `disaster_prediction`.
  - Outputs: `routed_department`.
  - Decision logic: mapping in [backend/services/risk_mapping.py](backend/services/risk_mapping.py).
  - Tools: none.
  - Memory: none.

- **Department Agents** (Public Works, Civil Defense, Emergency Response)
  - Purpose: Build alerts and action plans.
  - Prompt: Not applicable (template builder).
  - Inputs: `location`, `severity`, `news_context`, `disaster_prediction`, `feedback`.
  - Outputs: `generated_alert`, `action_plan`.
  - Decision logic: load memory rules, append feedback.
  - Tools: none.
  - Memory: persistent rules in [backend/memory/rules.json](backend/memory/rules.json).

- **Human Gatekeeper Agent**
  - Purpose: Pause for approval and capture feedback.
  - Prompt: Not applicable.
  - Inputs: alert payload and `run_id`.
  - Outputs: `approval_status`, `feedback`.
  - Decision logic: terminal vs API approval mode.
  - Tools: threading + environment configuration.
  - Memory: pending store in memory.

- **Reflection Agent**
  - Purpose: Log feedback.
  - Prompt: Not applicable.
  - Inputs: `feedback`.
  - Outputs: none.

- **Memory Update Agent**
  - Purpose: Persist feedback into memory rules.
  - Prompt: Not applicable.
  - Inputs: `feedback`, `run_id`.
  - Outputs: updated `memory_rules`.

- **Notification Sender Agent**
  - Purpose: Placeholder for outbound alerts.
  - Prompt: Not applicable.
  - Inputs: `generated_alert`, `action_plan`.
  - Outputs: none.

Routing logic: [backend/graphs/workflow.py](backend/graphs/workflow.py) uses `route_from_department()` from [backend/agents/router.py](backend/agents/router.py).

## 9. Machine Learning Components

- **Classifier**: RandomForestClassifier
  - Location: [backend/models/train_classifier.py](backend/models/train_classifier.py), [backend/models/disaster_inference.py](backend/models/disaster_inference.py)
  - Training source: synthetic dataset from [backend/models/synthetic_data.py](backend/models/synthetic_data.py) and stored as [backend/storage/data/disaster_training.csv](backend/storage/data/disaster_training.csv)
  - Input features: `rainfall`, `humidity`, `wind_speed`, `temperature_trend`, `pressure` from [backend/models/feature_spec.py](backend/models/feature_spec.py)
  - Output labels: `Normal`, `Flood`, `Heatwave`, `Storm`
  - Artifact: [backend/models/disaster_classifier.pkl](backend/models/disaster_classifier.pkl)

## 10. Forecasting Components

- Forecasting model: Prophet
- Location: [backend/agents/forecasting.py](backend/agents/forecasting.py)
- Input data: last 72 hours of `rainfall` from `weather_data`
- Horizon: 48 hours
- Output metrics: `forecast.points` with `rainfall`, `rainfall_lower`, `rainfall_upper`; summary feature `predicted_rainfall` and other weather features

## 11. Disaster Prediction Pipeline

Sequence and code paths:

1. **Input** from frontend in [frontend/src/app/page.tsx](frontend/src/app/page.tsx) calls `runWorkflow()` in [frontend/src/lib/api.ts](frontend/src/lib/api.ts).
2. **API** `POST /run` handled by `run_workflow()` in [backend/api/main.py](backend/api/main.py).
3. **Weather Retrieval** `ingest_environmental_data()` in [backend/agents/environmental_data.py](backend/agents/environmental_data.py).
4. **Forecasting** `forecast_rainfall()` in [backend/agents/forecasting.py](backend/agents/forecasting.py).
5. **ML Prediction** `disaster_prediction_node()` in [backend/agents/disaster_prediction.py](backend/agents/disaster_prediction.py).
6. **News Context** `news_monitor_node()` in [backend/agents/news_monitor.py](backend/agents/news_monitor.py).
7. **Severity Assessment** `severity_assessor_node()` in [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py).
8. **Routing** `routing_node()` in [backend/agents/router.py](backend/agents/router.py).
9. **Department Agent** `public_works_node()`, `civil_defense_node()`, or `emergency_response_node()`.
10. **Human Approval** `human_gatekeeper_node()` in [backend/agents/human_gatekeeper.py](backend/agents/human_gatekeeper.py).
11. **Alert Sender** `send_alert_node()` in [backend/agents/notification_sender.py](backend/agents/notification_sender.py).
12. **Validation** `validate_and_repair_state()` in [backend/validation/state_validator.py](backend/validation/state_validator.py).

## 12. News Monitoring System

- Source: NewsAPI or GNews.
- Query strategy: location term AND hazard keyword list.
- Filtering: hazard keyword inclusion, location token boosts, exclusion keywords for entertainment/tech.
- Output: top-scored headlines stored in `news_context`.
- Influence: passed into severity assessment in [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py).

## 13. Cognitive Router

Routing is explicit and deterministic:

- Input: `disaster_prediction.most_likely`.
- Output: `routed_department`.
- Rules from [backend/services/risk_mapping.py](backend/services/risk_mapping.py):
  - `Normal` -> None
  - `Flood` -> Public Works
  - `Heatwave` -> Civil Defense
  - `Storm` -> Emergency Response

Severity mapping in the same file:

- `Normal` -> `LOW`
- `Flood` -> `MEDIUM` or `HIGH` (confidence >= 0.7)
- `Heatwave` -> `MEDIUM` or `HIGH` (confidence >= 0.7)
- `Storm` -> `CRITICAL`

## 14. Department Agents

- **Public Works Agent** ([backend/agents/public_works.py](backend/agents/public_works.py))
  - Trigger: `routed_department == "Public Works"`.
  - Inputs: `location`, `severity`, `disaster_prediction`, `feedback`.
  - Outputs: `generated_alert`, `action_plan`.
  - Prompt: Not applicable (template builder).

- **Civil Defense Agent** ([backend/agents/civil_defense.py](backend/agents/civil_defense.py))
  - Trigger: `routed_department == "Civil Defense"`.
  - Inputs/Outputs: same as Public Works.
  - Prompt: Not applicable.

- **Emergency Response Agent** ([backend/agents/emergency_response.py](backend/agents/emergency_response.py))
  - Trigger: `routed_department == "Emergency Response"`.
  - Inputs/Outputs: same as Public Works.
  - Prompt: Not applicable.

## 15. Human-in-the-Loop System

- Approval mechanism: `set_pending()` and `await_human_decision()` in [backend/agents/human_gatekeeper.py](backend/agents/human_gatekeeper.py).
- Rejection mechanism: `approval_route()` routes to reflection and memory update on `REJECTED`.
- UI flow: frontend polls `GET /pending`, then posts to `/approve` or `/reject` via [frontend/src/lib/api.ts](frontend/src/lib/api.ts).
- Backend flow: gatekeeper blocks graph execution until decision is received.

## 16. Self-Improving Loop

- Feedback storage: `memory_update_node()` in [backend/agents/memory_update.py](backend/agents/memory_update.py) and [backend/memory/memory_store.py](backend/memory/memory_store.py).
- Prompt updates: **NOT IMPLEMENTED**.
- Future behavior changes: limited to appending feedback rules; no prompt rewriting.

## 17. Memory System

- Persistent memory: JSON rules in [backend/memory/rules.json](backend/memory/rules.json).
- Session memory: not persisted; workflow state carries `memory_rules` in `DisasterState`.
- Feedback memory: appended by `memory_update_node()` and retrieved by department agents using `retrieve_rules()`.

## 18. Email Alert System

- Email provider: **NOT IMPLEMENTED**.
- Templates: implemented as a text template builder in [backend/services/alert_builder.py](backend/services/alert_builder.py).
- Sending workflow: placeholder `send_alert_node()` logs output only in [backend/agents/notification_sender.py](backend/agents/notification_sender.py).

## 19. Database Schema

No database is used. Storage is file-based:

1. **Run History** ([backend/storage/data/runs_log.json](backend/storage/data/runs_log.json))
   - Fields (from `RunLogEntry` in [backend/models/schemas.py](backend/models/schemas.py)):
     - `timestamp` (ISO string)
     - `run_id` (string)
     - `location_name` (string)
     - `latitude` (float)
     - `longitude` (float)
     - `severity` (string)
     - `routed_department` (string)
     - `approval_status` (string)
     - `most_likely` (string)

2. **Persistent Memory** ([backend/memory/rules.json](backend/memory/rules.json))
   - Fields (from `MemoryRule` in [backend/models/schemas.py](backend/models/schemas.py)):
     - `timestamp` (ISO string)
     - `department` (string)
     - `rule` (string)
     - `run_id` (string, optional)

3. **Environmental History** ([backend/storage/data/environmental_history.csv](backend/storage/data/environmental_history.csv))
   - Columns: `time`, `temperature`, `humidity`, `rainfall`, `wind_speed`, `pressure` (from [backend/agents/environmental_data.py](backend/agents/environmental_data.py)).

4. **Training Dataset** ([backend/storage/data/disaster_training.csv](backend/storage/data/disaster_training.csv))
   - Columns: `rainfall`, `humidity`, `wind_speed`, `temperature_trend`, `pressure`, `label` (from [backend/models/synthetic_data.py](backend/models/synthetic_data.py)).

## 20. Complete Request Lifecycle

Example request trace:

1. User selects location in [frontend/src/app/page.tsx](frontend/src/app/page.tsx).
2. `handleRun()` calls `runWorkflow()` from [frontend/src/lib/api.ts](frontend/src/lib/api.ts).
3. `POST /run` handled by `run_workflow()` in [backend/api/main.py](backend/api/main.py).
4. Graph invocation in `build_graph()` in [backend/graphs/workflow.py](backend/graphs/workflow.py).
5. Weather ingestion via `ingest_environmental_data()` in [backend/agents/environmental_data.py](backend/agents/environmental_data.py).
6. Forecast via `forecast_rainfall()` in [backend/agents/forecasting.py](backend/agents/forecasting.py).
7. Disaster prediction via `disaster_prediction_node()` in [backend/agents/disaster_prediction.py](backend/agents/disaster_prediction.py).
8. News context via `news_monitor_node()` in [backend/agents/news_monitor.py](backend/agents/news_monitor.py).
9. Severity via `severity_assessor_node()` in [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py).
10. Routing via `routing_node()` in [backend/agents/router.py](backend/agents/router.py).
11. Department output via one of:
    - `public_works_node()` in [backend/agents/public_works.py](backend/agents/public_works.py)
    - `civil_defense_node()` in [backend/agents/civil_defense.py](backend/agents/civil_defense.py)
    - `emergency_response_node()` in [backend/agents/emergency_response.py](backend/agents/emergency_response.py)
12. Approval gate via `human_gatekeeper_node()` in [backend/agents/human_gatekeeper.py](backend/agents/human_gatekeeper.py).
13. Alert sender via `send_alert_node()` in [backend/agents/notification_sender.py](backend/agents/notification_sender.py).
14. Validation via `validate_and_repair_state()` in [backend/validation/state_validator.py](backend/validation/state_validator.py).
15. Response returned to frontend and rendered in dashboard state.

## 21. Requirement Compliance Matrix

| Requirement                  | Implemented?          | File Location                                                                | Evidence                                       |
| ---------------------------- | --------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------- |
| Environmental Data Ingestion | FULLY IMPLEMENTED     | [backend/agents/environmental_data.py](backend/agents/environmental_data.py) | Open-Meteo ingestion with caching and fallback |
| Time Series Forecasting      | FULLY IMPLEMENTED     | [backend/agents/forecasting.py](backend/agents/forecasting.py)               | Prophet-based rainfall forecast                |
| ML Disaster Prediction       | FULLY IMPLEMENTED     | [backend/models/disaster_inference.py](backend/models/disaster_inference.py) | RandomForest inference + probability outputs   |
| News Monitoring              | FULLY IMPLEMENTED     | [backend/agents/news_monitor.py](backend/agents/news_monitor.py)             | NewsAPI/GNews fetch + relevance filtering      |
| Cognitive Router             | FULLY IMPLEMENTED     | [backend/agents/router.py](backend/agents/router.py)                         | Risk mapping to departments                    |
| Department Agents            | FULLY IMPLEMENTED     | [backend/agents/public_works.py](backend/agents/public_works.py)             | Action plan generation                         |
| Human Approval               | FULLY IMPLEMENTED     | [backend/agents/human_gatekeeper.py](backend/agents/human_gatekeeper.py)     | Pending store + approval flow                  |
| Self-Improving Loop          | PARTIALLY IMPLEMENTED | [backend/agents/memory_update.py](backend/agents/memory_update.py)           | Feedback stored, no prompt update              |
| ML-LLM Bridge                | FULLY IMPLEMENTED     | [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py)   | Forecast + classifier + news to Gemini         |
| State-Driven Architecture    | FULLY IMPLEMENTED     | [backend/graphs/workflow.py](backend/graphs/workflow.py)                     | LangGraph state machine                        |
| Frontend                     | FULLY IMPLEMENTED     | [frontend/src/app/page.tsx](frontend/src/app/page.tsx)                       | Dashboard + map + approvals                    |

## 22. Missing Features

- Email delivery provider integration (alert sender logs only).
- Database storage (file-based JSON/CSV only).
- Deployment artifacts (Docker, CI/CD, cloud config) are **Unable to determine from code**.
- Project PDF requirements are not present in the repository; missing items beyond the matrix are **Unable to determine from code**.

## 23. Evaluator Questions (50)

1. **Q:** Where is the workflow orchestrated? **A:** `build_graph()` in [backend/graphs/workflow.py](backend/graphs/workflow.py).
2. **Q:** What initiates the workflow? **A:** `POST /run` in [backend/api/main.py](backend/api/main.py).
3. **Q:** How is weather data fetched? **A:** `fetch_environmental_data()` in [backend/agents/environmental_data.py](backend/agents/environmental_data.py).
4. **Q:** What is the forecast horizon? **A:** 48 hours in `forecast_rainfall()` in [backend/agents/forecasting.py](backend/agents/forecasting.py).
5. **Q:** Which model predicts disasters? **A:** RandomForest in [backend/models/train_classifier.py](backend/models/train_classifier.py).
6. **Q:** Where are features defined? **A:** `FEATURE_COLUMNS` in [backend/models/feature_spec.py](backend/models/feature_spec.py).
7. **Q:** How is the model loaded? **A:** `load_disaster_model()` in [backend/models/disaster_inference.py](backend/models/disaster_inference.py).
8. **Q:** What is the LLM provider? **A:** Gemini via REST in [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py).
9. **Q:** How is severity validated? **A:** `validate_and_repair_state()` in [backend/validation/state_validator.py](backend/validation/state_validator.py).
10. **Q:** What triggers the router? **A:** `severity_assessor_node()` output in [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py).
11. **Q:** How is routing decided? **A:** `select_department()` in [backend/services/risk_mapping.py](backend/services/risk_mapping.py).
12. **Q:** What happens on Normal prediction? **A:** Department set to None and LLM skipped in [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py).
13. **Q:** Where is news fetched? **A:** `fetch_local_news()` in [backend/agents/news_monitor.py](backend/agents/news_monitor.py).
14. **Q:** How are headlines filtered? **A:** `filter_relevant_headlines()` in [backend/agents/news_monitor.py](backend/agents/news_monitor.py).
15. **Q:** How is human approval handled? **A:** `human_gatekeeper_node()` in [backend/agents/human_gatekeeper.py](backend/agents/human_gatekeeper.py).
16. **Q:** What is stored as memory? **A:** Feedback rules in [backend/memory/rules.json](backend/memory/rules.json).
17. **Q:** How are rules retrieved? **A:** `retrieve_rules()` in [backend/memory/memory_retriever.py](backend/memory/memory_retriever.py).
18. **Q:** Where is run history stored? **A:** [backend/storage/data/runs_log.json](backend/storage/data/runs_log.json) via [backend/services/run_history.py](backend/services/run_history.py).
19. **Q:** How are run IDs generated? **A:** `uuid.uuid4()` in [backend/api/main.py](backend/api/main.py).
20. **Q:** Where is forecast plot written? **A:** [backend/storage/plots/rainfall_forecast.png](backend/storage/plots/rainfall_forecast.png) via [backend/agents/forecasting.py](backend/agents/forecasting.py).
21. **Q:** How is synthetic data built? **A:** `generate_synthetic_dataset()` in [backend/models/synthetic_data.py](backend/models/synthetic_data.py).
22. **Q:** Where are API schemas defined? **A:** [backend/models/schemas.py](backend/models/schemas.py).
23. **Q:** How is the frontend calling the API? **A:** `request()` in [frontend/src/lib/api.ts](frontend/src/lib/api.ts).
24. **Q:** Which page shows run history? **A:** [frontend/src/app/history/page.tsx](frontend/src/app/history/page.tsx).
25. **Q:** Which page shows settings? **A:** [frontend/src/app/settings/page.tsx](frontend/src/app/settings/page.tsx).
26. **Q:** How is the map rendered? **A:** Leaflet in [frontend/src/components/dashboard/map-inner.tsx](frontend/src/components/dashboard/map-inner.tsx).
27. **Q:** How does geolocation work? **A:** `navigator.geolocation` in [frontend/src/app/page.tsx](frontend/src/app/page.tsx).
28. **Q:** Where is Nominatim search called? **A:** `fetch()` in [frontend/src/app/page.tsx](frontend/src/app/page.tsx).
29. **Q:** What is the main dashboard component? **A:** `Home()` in [frontend/src/app/page.tsx](frontend/src/app/page.tsx).
30. **Q:** How are alerts formatted? **A:** `build_alert_message()` in [backend/services/alert_builder.py](backend/services/alert_builder.py).
31. **Q:** How is LLM fallback handled? **A:** `assess_severity()` in [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py).
32. **Q:** Is there an email provider? **A:** Not implemented; see [backend/agents/notification_sender.py](backend/agents/notification_sender.py).
33. **Q:** How is CORS configured? **A:** `CORSMiddleware` in [backend/api/main.py](backend/api/main.py).
34. **Q:** How are negative rainfall values handled? **A:** Clamped in [backend/agents/forecasting.py](backend/agents/forecasting.py) and [backend/agents/environmental_data.py](backend/agents/environmental_data.py).
35. **Q:** Where is severity adjusted to prediction mapping? **A:** `select_severity()` in [backend/services/risk_mapping.py](backend/services/risk_mapping.py).
36. **Q:** How does the UI show severity? **A:** `StatusPill` in [frontend/src/components/dashboard/status-pill.tsx](frontend/src/components/dashboard/status-pill.tsx).
37. **Q:** What is the data contract for run results? **A:** `RunState` in [frontend/src/lib/types.ts](frontend/src/lib/types.ts).
38. **Q:** How is pending approval tracked? **A:** `_pending_store` in [backend/agents/human_gatekeeper.py](backend/agents/human_gatekeeper.py).
39. **Q:** What happens when approval times out? **A:** `await_human_decision()` raises timeout in [backend/agents/human_gatekeeper.py](backend/agents/human_gatekeeper.py).
40. **Q:** How are memory rules applied? **A:** `retrieve_rules()` in department agents, e.g. [backend/agents/public_works.py](backend/agents/public_works.py).
41. **Q:** How is the UI polling for pending approvals? **A:** `setInterval` in [frontend/src/app/page.tsx](frontend/src/app/page.tsx).
42. **Q:** What happens when severity is Normal? **A:** LLM is skipped and severity set to LOW in [backend/agents/severity_assessor.py](backend/agents/severity_assessor.py).
43. **Q:** How is Open-Meteo failure handled? **A:** Fallback to cache or synthetic in [backend/agents/environmental_data.py](backend/agents/environmental_data.py).
44. **Q:** How are alerts regenerated after rejection? **A:** Reflection + memory update loop in [backend/graphs/workflow.py](backend/graphs/workflow.py).
45. **Q:** How is the dashboard showing action plans? **A:** `Alert & Action Plan` section in [frontend/src/app/page.tsx](frontend/src/app/page.tsx).
46. **Q:** What is the base URL for the backend in frontend? **A:** `NEXT_PUBLIC_API_BASE_URL` in [frontend/src/lib/api.ts](frontend/src/lib/api.ts).
47. **Q:** Where is the forecast chart built? **A:** [frontend/src/components/dashboard/forecast-chart.tsx](frontend/src/components/dashboard/forecast-chart.tsx).
48. **Q:** What is the default approval mode? **A:** `APPROVAL_MODE` in [backend/agents/human_gatekeeper.py](backend/agents/human_gatekeeper.py).
49. **Q:** How is environment configuration loaded? **A:** `load_dotenv()` in [backend/api/main.py](backend/api/main.py).
50. **Q:** Is a database used? **A:** No, file storage only; see [backend/services/run_history.py](backend/services/run_history.py) and [backend/memory/memory_store.py](backend/memory/memory_store.py).
