"""
Datenquelle: X (vormals Twitter) - offizielles Pay-per-Use-API (seit
6. Feb. 2026, kein Free-Tier mehr). Kosten: ca. 0,005 $ pro gelesenem
Post - für das gelegentliche Abrufen weniger Posts eines Accounts
(hier: @elonmusk) im Cent-Bereich pro Tag.

Benötigt einen Bearer Token aus dem X Developer Portal
(https://developer.x.com) mit aufgeladenen Pay-per-Use-Credits.
"""
import requests

X_API_BASE = "https://api.x.com/2"


def get_recent_posts(username: str, bearer_token: str, max_results: int = 10, timeout: int = 15):
    """Liefert eine Liste der neuesten Post-Texte eines X-Nutzers,
    oder [] bei Fehlern (z.B. kein Guthaben, ungültiger Token)."""
    headers = {"Authorization": f"Bearer {bearer_token}"}
    try:
        user_resp = requests.get(
            f"{X_API_BASE}/users/by/username/{username}", headers=headers, timeout=timeout
        )
        user_resp.raise_for_status()
        user_id = user_resp.json()["data"]["id"]

        posts_resp = requests.get(
            f"{X_API_BASE}/users/{user_id}/tweets",
            headers=headers,
            params={"max_results": max_results, "tweet.fields": "created_at"},
            timeout=timeout,
        )
        posts_resp.raise_for_status()
        data = posts_resp.json().get("data", [])
        return [p["text"] for p in data]
    except Exception:
        return []
