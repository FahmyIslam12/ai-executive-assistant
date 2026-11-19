"""Web search through the Tavily API (free plan: 1,000 searches a month).

We call Tavily's REST API directly with httpx (already installed), so no
extra library is needed. The key comes from .env (TAVILY_API_KEY).
"""

import logging
import os
import re

import httpx
from dotenv import load_dotenv

load_dotenv()

TAVILY_URL = "https://api.tavily.com/search"

# A basic search costs 1 credit. Each result's text is shortened, to keep
# the AI's input (and the OpenAI cost) small.
MAX_RESULTS = 5
MAX_TEXT_PER_RESULT = 600

# Looks like an email address: private data must never go to an outside
# search company.
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


class SearchError(Exception):
    """A clear, user-friendly reason the search didn't work."""


def web_search(query: str) -> list[dict[str, str]]:
    """Search the web and return a few results: title, link and short text."""
    query = query.strip()

    if not query:
        raise SearchError("The search query is empty.")

    if EMAIL_PATTERN.search(query):
        # Hard layer: block, don't just ask the AI to be careful.
        raise SearchError(
            "Blocked: the search query contains an email address. "
            "Search with general words only, never private data."
        )

    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        raise SearchError("Web search isn't set up: TAVILY_API_KEY is missing from .env.")

    # Search queries aren't private (we block private data above), so
    # logging them lets us check what the AI searched for.
    logging.info("Web search: %s", query)

    try:
        response = httpx.post(
            TAVILY_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "query": query,
                "search_depth": "basic",  # 1 credit (advanced costs 2)
                "max_results": MAX_RESULTS,
            },
            timeout=20,
        )
    except httpx.HTTPError as error:
        raise SearchError(f"Couldn't reach the search service: {type(error).__name__}.")

    if response.status_code == 401:
        raise SearchError("The Tavily API key was rejected. Check TAVILY_API_KEY in .env.")
    if response.status_code in (429, 432, 433):
        raise SearchError("The monthly free search limit (or rate limit) has been reached.")
    if response.status_code != 200:
        raise SearchError(f"The search service returned an error (status {response.status_code}).")

    results = []
    for item in response.json().get("results", []):
        text = (item.get("content") or "").strip()
        if len(text) > MAX_TEXT_PER_RESULT:
            text = text[:MAX_TEXT_PER_RESULT] + "..."
        results.append(
            {"title": item.get("title", ""), "url": item.get("url", ""), "text": text}
        )
    return results
