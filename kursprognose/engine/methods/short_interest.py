"""
Methode: Leerverkaufsquote (Short Interest).
Nur sinnvoll für Einzelaktien (SAP, Apple), nicht für Indizes/Rohstoffe.

Logik: hohe Leerverkaufsquote wird hier als bearishes Signal gewertet
(einfache Variante - manche Trader lesen sehr hohe Quoten stattdessen
als Kontraindikator wegen möglicher Short-Squeezes; das ist bewusst
NICHT implementiert, um die Methode einfach & nachvollziehbar zu halten).
"""
from sources import equity_source, yahoo_source

SCHWELLENWERT = 0.03  # 3% des Streubesitzes als neutrale Mitte


def predict(asset_cfg: dict, params: dict) -> dict:
    ticker = asset_cfg["yahoo_ticker"]
    schwelle = params.get("schwellenwert", SCHWELLENWERT)

    short_pct = equity_source.get_short_percent_of_float(ticker)

    if short_pct is None:
        raise ValueError(
            f"Keine Leerverkaufs-Daten für '{ticker}' verfügbar"
        )

    signal = "SHORT" if short_pct >= schwelle else "LONG"
    score = round(short_pct - schwelle, 4)

    try:
        price = yahoo_source.get_last_price(ticker)
    except Exception:
        price = None

    return {
        "signal": signal,
        "score": score,
        "price": price,
        "details": f"Leerverkaufsquote={short_pct*100:.2f}% des Streubesitzes (Schwelle={schwelle*100:.1f}%)",
    }
