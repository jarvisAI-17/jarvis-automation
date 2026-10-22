"""
Datenquelle: Truth Social - inoffiziell via ScrapeCreators
(https://scrapecreators.com/truthsocial-api). Truth Social selbst bietet
kein öffentliches Entwickler-API (das offizielle "Truth API" von Trump
Media ist institutionell bepreist, siehe Docstring in
methods/political_influencers.py).

Endpoint (laut ScrapeCreators-Doku, Stand Juli 2026):
  GET https://api.scrapecreators.com/v1/truthsocial/user/posts
  Parameter: user_id (schneller als handle) oder handle

Trumps user_id ist laut Doku 107780257626128497 - direkt verwendet,
damit kein zusätzlicher Profile-Lookup-Call (und damit Credit) nötig ist.
"""
import re
import requests

TRUMP_USER_ID = "107780257626128497"
DEFAULT_BASE = "https://api.scrapecreators.com"


def _strip_html(text: str) -> str:
    """ScrapeCreators liefert Post-Inhalte vermutlich als HTML (Truth Social
    basiert auf einem Mastodon-Fork) - einfache Tag-Entfernung fürs Sentiment-Scoring."""
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def get_recent_posts(api_key: str, api_base: str = None, user_id: str = TRUMP_USER_ID,
                      max_results: int = 10, timeout: int = 15):
    """Liefert eine Liste der neuesten Post-Texte (HTML-bereinigt) eines
    Truth-Social-Profils, oder [] bei Fehlern/aufgebrauchtem Kontingent/
    fehlendem Key."""
    if not api_key:
        return []
    base = (api_base or DEFAULT_BASE).rstrip("/")
    try:
        resp = requests.get(
            f"{base}/v1/truthsocial/user/posts",
            headers={"x-api-key": api_key},
            params={"user_id": user_id},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        posts = data if isinstance(data, list) else data.get("posts", data.get("data", []))
        texte = []
        for p in posts[:max_results]:
            roh = p.get("content") or p.get("text") or ""
            bereinigt = _strip_html(roh)
            if bereinigt:
                texte.append(bereinigt)
        return texte
    except Exception:
        return []
