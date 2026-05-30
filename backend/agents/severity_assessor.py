from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Mapping

import httpx
from pydantic import ValidationError

from backend.graphs.state import DisasterState
from backend.models.schemas import SeverityAssessment
from backend.services.risk_mapping import select_severity
from backend.memory.memory_retriever import retrieve_recent_insights

logger = logging.getLogger(__name__)

DEFAULT_LLM_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_LLM_MODEL = "gemini-2.0-flash"


def _truncate_text(value: str | None, limit: int = 300) -> str:
    if not value:
        return ""
    return value if len(value) <= limit else f"{value[:limit]}..."


def _mask_secret(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "***"
    return f"***{value[-4:]}"


def _summarize_gemini_response(payload: Dict[str, Any]) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        return "candidates=0"
    candidate = candidates[0]
    finish_reason = candidate.get("finishReason")
    safety = candidate.get("safetyRatings")
    has_content = "content" in candidate and bool(candidate.get("content"))
    return f"finishReason={finish_reason}, safetyRatings={bool(safety)}, hasContent={has_content}"


def _extract_gemini_text(payload: Dict[str, Any]) -> str | None:
    candidates = payload.get("candidates") or []
    if not candidates:
        return None
    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []
    for part in parts:
        text = part.get("text") if isinstance(part, dict) else None
        if text:
            return str(text)
    return None


def _build_prompt(
    features: Mapping[str, Any],
    disaster_prediction: Mapping[str, Any],
    news_context: List[str],
    recent_insights: List[str] | None = None,
) -> str:
    # Provide explicit fields and confidence values to the LLM for explainable reasoning
    user_payload = {
        "forecast_features": features,
        "disaster_prediction": disaster_prediction,
        "prediction_confidences": {k: v for k, v in disaster_prediction.items() if k != "most_likely"},
        "news_headlines": news_context,
        "recent_insights": recent_insights or [],
    }

    instructions = (
        "You are an emergency operations analyst.\n"
        "Evaluate forecast features, ML prediction probabilities, and real-world news context.\n"
        "Return only a JSON object with keys 'severity' and 'reason'.\n"
        "Severity must be one of: LOW, MEDIUM, HIGH, CRITICAL.\n"
        "Example output: {\"severity\": \"HIGH\", \"reason\": \"...\"}\n"
    )

    return f"{instructions}\nPayload:\n{json.dumps(user_payload)}"


def _invoke_llm(prompt: str) -> str:
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        logger.error("LLM_API_KEY missing; severity assessor cannot call LLM")
        raise EnvironmentError("LLM_API_KEY is not set")

    base_url = os.getenv("LLM_BASE_URL", DEFAULT_LLM_BASE_URL).rstrip("/")
    model = os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL)
    logger.info(
        "LLM config (base_url=%s, model=%s, key=%s)",
        base_url,
        model,
        _mask_secret(api_key),
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 256,
            "responseMimeType": "application/json",
        },
    }

    attempts = int(os.getenv("LLM_RETRY_ATTEMPTS", "3"))
    base_delay = float(os.getenv("LLM_RETRY_BASE_SECONDS", "1.0"))
    last_exc: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            with httpx.Client(timeout=20) as client:
                response = client.post(
                    f"{base_url}/models/{model}:generateContent",
                    headers={"x-goog-api-key": api_key},
                    json=payload,
                )
            response.raise_for_status()
            data = response.json()
            text = _extract_gemini_text(data)
            if text:
                return text

            logger.warning(
                "Gemini response missing content parts (%s)",
                _summarize_gemini_response(data),
            )
            fallback_payload = dict(payload)
            generation_config = dict(payload.get("generationConfig") or {})
            generation_config.pop("responseMimeType", None)
            fallback_payload["generationConfig"] = generation_config
            with httpx.Client(timeout=20) as client:
                fallback_response = client.post(
                    f"{base_url}/models/{model}:generateContent",
                    headers={"x-goog-api-key": api_key},
                    json=fallback_payload,
                )
            fallback_response.raise_for_status()
            fallback_data = fallback_response.json()
            text = _extract_gemini_text(fallback_data)
            if text:
                logger.info("Gemini response recovered without responseMimeType")
                return text

            logger.warning(
                "Gemini response still missing content parts (%s)",
                _summarize_gemini_response(fallback_data),
            )
            raise ValueError("Gemini response missing content parts")
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            response_text = _truncate_text(exc.response.text)
            retry_after = exc.response.headers.get("Retry-After")
            logger.warning(
                "LLM HTTP error status=%s attempt=%s/%s model=%s base_url=%s retry_after=%s response=%s",
                status,
                attempt,
                attempts,
                model,
                base_url,
                retry_after,
                response_text,
            )
            if status == 429 and attempt < attempts:
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "LLM rate limited (429). Retry %s/%s in %.1fs",
                    attempt,
                    attempts,
                    delay,
                )
                time.sleep(delay)
                last_exc = exc
                continue
            raise
        except httpx.RequestError as exc:
            logger.warning(
                "LLM request error attempt=%s/%s model=%s base_url=%s error=%s",
                attempt,
                attempts,
                model,
                base_url,
                exc,
            )
            if attempt < attempts:
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "LLM request failed. Retry %s/%s in %.1fs",
                    attempt,
                    attempts,
                    delay,
                )
                time.sleep(delay)
                last_exc = exc
                continue
            raise

    if last_exc:
        raise last_exc
    raise RuntimeError("LLM request failed")


def assess_severity(
    features: Mapping[str, Any],
    disaster_prediction: Mapping[str, Any],
    news_context: List[str],
    recent_insights: List[str] | None = None,
) -> SeverityAssessment:
    prompt = _build_prompt(features, disaster_prediction, news_context, recent_insights)
    try:
        content = _invoke_llm(prompt)
        parsed = _extract_json_object(content)
        try:
            return SeverityAssessment.model_validate_json(parsed)
        except (ValidationError, ValueError) as exc:
            logger.warning(
                "LLM response parse failed; using fallback. error=%s response=%s",
                exc,
                _truncate_text(content, 500),
            )
            raise
    except (EnvironmentError, httpx.HTTPError, ValidationError, ValueError) as exc:
        logger.warning("Severity LLM unavailable, using fallback. error=%s", exc)
        return SeverityAssessment(
            severity="MEDIUM",
            reason="LLM unavailable; default severity applied.",
        )


def _extract_json_object(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    if "```" in stripped:
        parts = stripped.split("```")
        for part in parts:
            candidate = part.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                logger.info("Extracted JSON from fenced block")
                return candidate

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = stripped[start : end + 1]
        logger.info("Extracted JSON from response substring")
        return candidate

    return stripped


def severity_assessor_node(state: DisasterState) -> DisasterState:
    forecast = state.get("forecast") or {}
    features = forecast.get("features") or {}
    prediction = state.get("disaster_prediction") or {}
    news_context = state.get("news_context") or []
    run_id = state.get("run_id")

    if not features:
        raise ValueError("Forecast features missing for severity assessment")
    if not prediction:
        raise ValueError("Disaster prediction missing for severity assessment")

    # Retrieve recent insights to adapt LLM prompt
    recent_insights = retrieve_recent_insights(limit=5)

    # Always consult the LLM (Gemini) — its output is authoritative for severity
    assessment = assess_severity(features, prediction, news_context, recent_insights)

    # For transparency, keep the classifier-derived mapped severity but DO NOT overwrite LLM
    classifier_mapped = select_severity(prediction)

    logger.info("Severity (LLM): %s", assessment.severity)
    logger.info(
        "Severity state (run_id=%s, news_count=%s, most_likely=%s, classifier_mapped=%s)",
        run_id,
        len(news_context),
        prediction.get("most_likely"),
        classifier_mapped,
    )

    return {
        "severity": assessment.severity,
        "severity_reason": assessment.reason,
        "classifier_mapped_severity": classifier_mapped,
    }
