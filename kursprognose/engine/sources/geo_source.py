"""
Datenquelle: Geopolitische / Makro-Stimmungsdaten über die kostenlose
GDELT DOC 2.0 API (kein API-Key nötig). Es wird der "ToneChart"-Modus
genutzt, der eine Verteilung des Tons (Sentiment) aller weltweit
gefundenen Artikel zu einem Suchbegriff im gewählten Zeitraum liefert.

Austauschbar: Wer eine andere geopolitische/Makro-Quelle nutzen möchte
(z.B. einen Wirtschaftskalender, eine News-API mit Risiko-Tags), kann
hier get_average_tone() mit derselben Rückgabe (float, ca. -10..+10)
neu implementieren.
"""
import requests

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"


def get_average_tone(query: str, lookback_hours: int = 48, timeout: int = 20) -> float:
    """Fragt GDELT nach dem durchschnittlichen (nach Artikelanzahl
    gewichteten) Sentiment-Ton zu einem Suchbegriff der letzten
    `lookback_hours` Stunden ab. Rückgabe: float (negativ = negativ
    gestimmt, positiv = positiv gestimmt, 0 falls keine Daten)."""
    params = {
        "query": query,
        "mode": "tonechart",
        "format": "json",
        "timespan": f"{lookback_hours}h",
    }
    try:
        resp = requests.get(GDELT_DOC_API, params=params, timeout=timeout,
                             headers={"User-Agent": "Mozilla/5.0 (Kursprognose-Bot)"})
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return 0.0

    bins = data.get("tonechart", [])
    if not bins:
        return 0.0

    total_count = sum(b.get("count", 0) for b in bins)
    if total_count == 0:
        return 0.0

    weighted_sum = sum(b.get("bin", 0) * b.get("count", 0) for b in bins)
    return weighted_sum / total_count


def get_event_count(query: str, lookback_hours: int = 48, timeout: int = 20) -> int:
    """Liefert die Anzahl gefundener Artikel/Events (grobes Maß für
    'Aufregung'/Nachrichtenvolumen zu einem Thema)."""
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "maxrecords": 250,
        "timespan": f"{lookback_hours}h",
    }
    try:
        resp = requests.get(GDELT_DOC_API, params=params, timeout=timeout,
                             headers={"User-Agent": "Mozilla/5.0 (Kursprognose-Bot)"})
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return 0

    return len(data.get("articles", []))
