"""
Methode 3: Geopolitische & Makro-Daten (GDELT DOC 2.0 API, kostenlos).

Schnittstelle: predict(asset_cfg, params) -> dict (siehe technical_method.py)

Logik: Der durchschnittliche weltweite Nachrichten-"Ton" (Sentiment) zu den
Asset-Suchbegriffen wird über GDELT abgefragt (-10 = sehr negativ,
+10 = sehr positiv). Ton > 0 -> LONG, sonst SHORT. Zusätzlich fließt das
Nachrichtenvolumen als grobes Unsicherheitsmaß in den Score (nicht in das
Signal) ein.
"""
from sources import geo_source, yahoo_source


def predict(asset_cfg: dict, params: dict) -> dict:
    lookback_hours = params.get("lookback_hours", 48)

    keywords = asset_cfg.get("news_keywords", [asset_cfg["symbol"]])
    # GDELT-Query: Suchbegriffe mit OR verknüpfen, in Anführungszeichen für
    # Mehrwort-Begriffe.
    quoted_terms = [f'"{kw}"' if " " in kw else kw for kw in keywords]
    query = " OR ".join(quoted_terms)

    avg_tone = geo_source.get_average_tone(query, lookback_hours=lookback_hours)
    event_count = geo_source.get_event_count(query, lookback_hours=lookback_hours)

    signal = "LONG" if avg_tone >= 0 else "SHORT"

    try:
        last_price = yahoo_source.get_last_price(asset_cfg["yahoo_ticker"])
    except Exception:
        last_price = None

    details = (
        f"GDELT Ø-Ton={avg_tone:.2f} (Skala ca. -10..+10), "
        f"{event_count} Artikel im Betrachtungszeitraum ({lookback_hours}h)"
    )

    return {
        "signal": signal,
        "score": round(float(avg_tone), 4),
        "price": last_price,
        "details": details,
    }
