from __future__ import annotations

import logging
import os
from typing import Any, List, Mapping

import httpx

from backend.graphs.state import DisasterState

logger = logging.getLogger(__name__)

NEWSAPI_URL = "https://newsapi.org/v2/everything"
GNEWS_URL = "https://gnews.io/api/v4/search"

HAZARD_KEYWORDS = [
    "flood",
    "flash flood",
    "storm",
    "cyclone",
    "hurricane",
    "typhoon",
    "landslide",
    "disaster",
    "emergency",
    "evacuation",
    "rain",
    "rainfall",
    "monsoon",
    "drought",
    "heatwave",
    "heat wave",
    "wildfire",
    "infrastructure",
    "public safety",
]

EXCLUDED_KEYWORDS = [
    "movie",
    "film",
    "tv",
    "series",
    "anime",
    "manga",
    "trailer",
    "game",
    "gaming",
    "playstation",
    "xbox",
    "nintendo",
    "steam",
    "script",
    "code",
    "developer",
    "software",
    "app",
    "ai",
    "machine learning",
    "openai",
    "chatgpt",
    "github",
    "crypto",
    "bitcoin",
    "stock",
    "earnings",
]

MIN_RELEVANCE_SCORE = 2


def _location_query(location: Mapping[str, Any]) -> str:
    name = location.get("name")
    if name:
        cleaned = str(name).strip()
        if cleaned.lower() not in {"current location", "current"}:
            return cleaned
    latitude = location.get("latitude")
    longitude = location.get("longitude")
    if latitude is None or longitude is None:
        return ""
    return f"{latitude},{longitude}"


def _build_news_query(location: Mapping[str, Any]) -> str:
    location_term = _location_query(location)
    keyword_query = " OR ".join(HAZARD_KEYWORDS)
    if location_term:
        return f"{location_term} AND ({keyword_query})"
    return keyword_query


def _location_tokens(location: Mapping[str, Any]) -> List[str]:
    name = (location.get("name") or "").lower()
    if name in {"current location", "current"}:
        return []
    return [
        token
        for token in name.replace(",", " ").split()
        if token and token not in {"current", "location"}
    ]


def _score_relevance(text: str, location: Mapping[str, Any]) -> int:
    lower = text.lower()
    hazard_hits = sum(1 for keyword in HAZARD_KEYWORDS if keyword in lower)
    if hazard_hits == 0:
        return -1
    score = hazard_hits * 3
    location_hits = sum(1 for token in _location_tokens(location) if token in lower)
    score += location_hits * 2
    excluded_hits = sum(1 for keyword in EXCLUDED_KEYWORDS if keyword in lower)
    score -= excluded_hits * 5
    return score


def filter_relevant_headlines(
    articles: List[Mapping[str, Any]],
    location: Mapping[str, Any],
    limit: int,
) -> List[str]:
    ranked: List[tuple[int, str]] = []
    for article in articles:
        title = str(article.get("title") or "").strip()
        if not title:
            continue
        description = str(article.get("description") or "").strip()
        text = f"{title}. {description}" if description else title
        score = _score_relevance(text, location)
        if score < MIN_RELEVANCE_SCORE:
            continue
        ranked.append((score, title))

    ranked.sort(key=lambda item: item[0], reverse=True)
    seen = set()
    headlines: List[str] = []
    for _, title in ranked:
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        headlines.append(title)
        if len(headlines) >= limit:
            break
    return headlines


def _filter_headlines(headlines: List[str], location: Mapping[str, Any]) -> List[str]:
    if not headlines:
        return []
    location_name = (location.get("name") or "").lower()
    location_tokens = [
        token
        for token in location_name.replace(",", " ").split()
        if token and token not in {"current", "location"}
    ]
    filtered = []
    for title in headlines:
        lower = title.lower()
        if any(keyword in lower for keyword in HAZARD_KEYWORDS) or any(
            token in lower for token in location_tokens
        ):
            filtered.append(title)
    return filtered if filtered else headlines


def fetch_local_news(location: Mapping[str, Any], limit: int = 5) -> List[str]:
    provider = os.getenv("NEWS_PROVIDER", "newsapi").lower()
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        logger.warning("NEWS_API_KEY not set; skipping news fetch")
        return []

    query = _build_news_query(location)
    fetch_limit = min(max(limit * 4, 20), 50)
    logger.info("News query (provider=%s, query=%s, fetch_limit=%s)", provider, query, fetch_limit)

    try:
        with httpx.Client(timeout=10) as client:
            if provider == "gnews":
                response = client.get(
                    GNEWS_URL,
                    params={
                        "q": query,
                        "lang": "en",
                        "max": fetch_limit,
                        "token": api_key,
                    },
                )
            else:
                response = client.get(
                    NEWSAPI_URL,
                    params={
                        "q": query,
                        "language": "en",
                        "pageSize": fetch_limit,
                        "searchIn": "title,description",
                        "sortBy": "publishedAt",
                        "apiKey": api_key,
                    },
                )

            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        logger.warning("News fetch failed: %s", exc)
        return []
    except ValueError as exc:
        logger.warning("News response could not be parsed: %s", exc)
        return []

    articles = payload.get("articles") or payload.get("items") or []
    headlines = filter_relevant_headlines(articles, location, limit)
    logger.info(
        "News filter applied (fetched=%s, kept=%s)",
        len(articles),
        len(headlines),
    )
    return headlines


def news_monitor_node(state: DisasterState) -> DisasterState:
    location = state.get("location") or {}
    run_id = state.get("run_id")
    headlines = fetch_local_news(location)

    summary = "; ".join(headlines) if headlines else "No relevant headlines"
    logger.info("News summary: %s", summary)
    logger.info("News state (run_id=%s, headlines=%s)", run_id, len(headlines))

    return {"news_context": headlines}
