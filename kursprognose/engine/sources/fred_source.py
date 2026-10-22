"""
Datenquelle: FRED (Federal Reserve Economic Data der St. Louis Fed) -
kostenlose, offizielle API. FRED spiegelt neben US-Reihen auch viele
EZB-Reihen, daher genügt ein einziger API-Key für Fed- UND EZB-Zinssatz.

Standard-Reihen (siehe methods/interest_rate_differential.py):
  - FEDFUNDS: Effective Federal Funds Rate (monatlich)
  - ECBDFR:   ECB Deposit Facility Rate (täglich)

Weitere Reihen-IDs lassen sich unter https://fred.stlouisfed.org/ suchen.
"""
import requests

FRED_API_BASE = "https://api.stlouisfed.org/fred/series/observations"


def get_latest_value(series_id: str, api_key: str, timeout: int = 15):
    """Liefert den neuesten verfügbaren Wert einer FRED-Zeitreihe (float),
    oder None bei Fehlern/fehlenden Daten (z.B. ungültige series_id)."""
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
    }
    try:
        resp = requests.get(FRED_API_BASE, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        observations = data.get("observations", [])
        if not observations:
            return None
        value = observations[0].get("value")
        if value in (None, ".", ""):
            return None
        return float(value)
    except Exception:
        return None
