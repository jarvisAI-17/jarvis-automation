"""
Methode: Institutionelle Holdings.
Nur sinnvoll für Einzelaktien (SAP, Apple), nicht für Indizes/Rohstoffe.

Hinweis: yfinance liefert nur den aktuellen Stand (heldPercentInstitutions),
keine historische Zeitreihe - daher wird hier ein einfacher Schwellenwert
genutzt (hoher institutioneller Anteil = als stabilisierend gewertet),
nicht eine "Veränderung" wie ursprünglich angedacht. Für eine echte
Veränderungs-Analyse müsste der Wert bei jedem Lauf mitgeschrieben und
mit dem Vorlauf verglichen werden (z.B. über die `details`-Spalte).
"""
from sources import equity_source, yahoo_source

SCHWELLENWERT = 0.60  # 60% institutioneller Anteil als neutrale Mitte


def predict(asset_cfg: dict, params: dict) -> dict:
    ticker = asset_cfg["yahoo_ticker"]
    schwelle = params.get("schwellenwert", SCHWELLENWERT)

    held_pct = equity_source.get_held_percent_institutions(ticker)

    if held_pct is None:
        raise ValueError(
            f"Keine Daten zu institutionellen Holdings für '{ticker}' verfügbar"
        )

    signal = "LONG" if held_pct >= schwelle else "SHORT"
    score = round(held_pct - schwelle, 4)

    try:
        price = yahoo_source.get_last_price(ticker)
    except Exception:
        price = None

    return {
        "signal": signal,
        "score": score,
        "price": price,
        "details": f"Institutioneller Anteil={held_pct*100:.1f}% (Schwelle={schwelle*100:.0f}%)",
    }
