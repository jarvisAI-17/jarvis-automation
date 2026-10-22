"""
Datenquelle: Finnhub (kostenloser Tier: 60 Anfragen/Minute, kein Tages-
limit dokumentiert). Liefert saubere Analysten-Konsens- und Earnings-
Surprise-Daten für Einzelaktien - zuverlässiger als die inoffiziellen
yfinance-Felder.

Hinweis: Finnhub deckt primär US-gelistete Ticker gut ab (SAP als
US-ADR unter dem Symbol "SAP", AAPL direkt). Für DAX/MDAX/OEL liefert
Finnhub erwartungsgemäß keine Daten - die aufrufenden Methoden fallen
dann automatisch auf yfinance zurück.
"""
import requests

FINNHUB_BASE = "https://finnhub.io/api/v1"


def get_recommendation_trend(symbol: str, api_key: str, timeout: int = 15):
    """Neuestes Analysten-Empfehlungsbild:
    {'buy': n, 'hold': n, 'sell': n, 'strongBuy': n, 'strongSell': n, 'period': 'YYYY-MM-DD'}
    oder None bei Fehlern/keinen Daten."""
    try:
        resp = requests.get(
            f"{FINNHUB_BASE}/stock/recommendation",
            params={"symbol": symbol, "token": api_key}, timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        return data[0]  # neuester Monat zuerst
    except Exception:
        return None


def get_latest_earnings_surprise_pct(symbol: str, api_key: str, timeout: int = 15):
    """Prozentuale Überraschung (surprisePercent) des zuletzt gemeldeten
    Quartals, oder None bei Fehlern/keinen Daten."""
    try:
        resp = requests.get(
            f"{FINNHUB_BASE}/stock/earnings",
            params={"symbol": symbol, "token": api_key}, timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        val = data[0].get("surprisePercent")
        return float(val) if val is not None else None
    except Exception:
        return None
