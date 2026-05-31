# Deployment Guide

This repository is split into two deployable parts:

- Frontend: Next.js app in [frontend/](frontend/)
- Backend: FastAPI app in [backend/](backend/)

The recommended production setup is:

- Deploy the frontend to Vercel.
- Deploy the backend to Render.
- Point the frontend at the Render URL with `NEXT_PUBLIC_API_BASE_URL`.
- Allow the Vercel origin in the backend `CORS_ORIGINS` setting.

## 1. Prerequisites

Before deploying, make sure you have:

- A GitHub repository connected to both Vercel and Render.
- API keys for the services the backend expects:
  - `NEWS_API_KEY`
  - `LLM_API_KEY`
- A decision about your LLM provider settings:
  - `LLM_BASE_URL`
  - `LLM_MODEL`
- The frontend API base URL for the deployed backend.

Example environment files are available at [backend/.env.example](backend/.env.example) and [frontend/.env.example](frontend/.env.example).

## 2. Deploy The Backend On Render

Create a new **Web Service** in Render and connect it to this repository.

Use the following settings:

- **Root Directory:** repository root, or leave blank if Render already uses the repo root.
- **Runtime:** Python 3.
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`

Render will expose a public URL such as `https://your-service.onrender.com`.

### Backend Environment Variables

Set these in the Render dashboard:

- `NEWS_API_KEY`: required for news enrichment.
- `NEWS_PROVIDER`: `newsapi` or `gnews`.
- `LLM_API_KEY`: required for the severity-assessment model call.
- `LLM_BASE_URL`: OpenAI-compatible API base URL.
- `LLM_MODEL`: model name used by the backend.
- `APPROVAL_MODE`: set to `api` for hosted deployment.
- `APPROVAL_TIMEOUT_SECONDS`: optional, defaults to `900`.
- `CORS_ORIGINS`: comma-separated list of allowed frontend origins.
- `ALLOW_SYNTHETIC_FALLBACK`: set to `true` if you want weather fallback data when Open-Meteo fails.
- `AUTO_TRAIN_MODEL`: set to `true` so Render can train the classifier automatically when the model file is missing.

### Important Backend Notes

- The deployed backend should use `APPROVAL_MODE=api`. Terminal approval mode is not suitable for Render.
- The classifier artifact is not committed in this repo, so the first backend boot may train it automatically if `AUTO_TRAIN_MODEL=true`.
- If you want faster cold starts, train the model locally and commit the generated artifact before deploying.
- The health check endpoint is `GET /health`.

## 3. Deploy The Frontend On Vercel

Create a new **Project** in Vercel and import the same repository.

Set the frontend root to the `frontend` directory.

Use these settings:

- **Framework Preset:** Next.js
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Install Command:** `npm install`
- **Output Directory:** leave empty and let Vercel detect Next.js automatically

### Frontend Environment Variables

Set these in Vercel:

- `NEXT_PUBLIC_API_BASE_URL`: the full Render backend URL, for example `https://your-service.onrender.com`
- `NEXT_PUBLIC_NOMINATIM_URL`: optional override for the map search endpoint

Important:

- `NEXT_PUBLIC_API_BASE_URL` is read at build time by the frontend.
- Set it before the first Vercel deployment, or redeploy after changing it.

## 4. Connect The Two Services

After both deployments are live:

- Add your Vercel domain to the backend `CORS_ORIGINS` variable.
- Redeploy the backend after updating `CORS_ORIGINS`.
- Confirm that the frontend is pointing at the Render URL in `NEXT_PUBLIC_API_BASE_URL`.
- Confirm that the backend is returning successful responses from `GET /health`.

Example `CORS_ORIGINS` value:

```text
https://your-app.vercel.app,https://your-custom-domain.com
```

## 5. Verification Checklist

Use this order to verify the deployment:

1. Open the Render service URL and confirm `GET /health` returns `{"status":"ok"}`.
2. Open the Vercel frontend and submit a location from the dashboard.
3. Confirm the frontend can call `POST /run` on the backend.
4. Confirm pending approvals appear through `GET /pending`.
5. Approve or reject one run to verify the full workflow.

## 6. Common Deployment Issues

- If the frontend cannot reach the backend, check `NEXT_PUBLIC_API_BASE_URL` and `CORS_ORIGINS`.
- If the backend fails on startup, check that `NEWS_API_KEY` and `LLM_API_KEY` are set.
- If the backend spends a long time starting, the classifier may be training automatically on first boot.
- If the frontend shows stale configuration, redeploy it after changing public environment variables.

## 7. Local Development References

For local development, the usual commands are:

- Backend: `uvicorn backend.api.main:app --reload`
- Frontend: `cd frontend && npm run dev`

Those local commands are not the production deployment commands for Vercel or Render.