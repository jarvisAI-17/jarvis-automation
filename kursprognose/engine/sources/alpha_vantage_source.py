"""
Datenquelle: Alpha Vantage NEWS_SENTIMENT.

WICHTIG - Rate Limit: der kostenlose Tier erlaubt nur 25 Anfragen/Tag
(5/Minute, Stand Juli 2026, siehe https://www.alphavantage.co/premium/).
Deshalb wird diese Quelle in sentiment_method.py bewusst NUR für Einzel-
aktien (SAP, AAPL) genutzt, nicht für Indizes/Rohstoffe (die haben
ohnehin keinen gültigen Alpha-Vantage-Ticker) - bei 5 Assets x 3 Läufen/Tag
blieben sonst zu wenig Anfragen für andere Nutzung übrig.
"""
import requests

ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"


def get_average_sentiment(ticker: str, api_key: str, limit: int = 50, timeout: int = 20):
    """Liefert den durchschnittlichen 'overall_sentiment_score' (-1..+1)
    der neuesten `limit` Artikel zu einem Ticker, oder None bei
    Fehlern/keinen Daten/aufgebrauchtem Tageskontingent."""
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "limit": limit,
        "apikey": api_key,
    }
    try:
        resp = requests.get(ALPHA_VANTAGE_BASE, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if "Information" in data or "Note" in data:
            # Kontingent aufgebraucht oder ungültiger Key - kein Fehler, nur keine Daten
            return None
        feed = data.get("feed", [])
        if not feed:
            return None
        scores = [float(item["overall_sentiment_score"]) for item in feed
                  if "overall_sentiment_score" in item]
        if not scores:
            return None
        return sum(scores) / len(scores)
    except Exception:
        return None
