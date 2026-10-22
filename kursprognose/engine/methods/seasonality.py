"""
Methode: Saisonalität (Kalendereffekte).

Logik: historische Durchschnittsrendite des Assets im aktuellen
Kalendermonat über die letzten `jahre` Jahre. Positiver historischer
Schnitt -> LONG, negativer -> SHORT.
"""
from datetime import datetime

from sources import yahoo_source


def predict(asset_cfg: dict, params: dict) -> dict:
    ticker = asset_cfg["yahoo_ticker"]
    jahre = params.get("jahre", 5)

    hist = yahoo_source.get_price_history(ticker, lookback_days=365 * jahre)
    monatsrendite = hist["Close"].resample("ME").last().pct_change().dropna()

    aktueller_monat = datetime.now().month
    monatsrendite_gleicher_monat = monatsrendite[monatsrendite.index.month == aktueller_monat]

    if monatsrendite_gleicher_monat.empty:
        raise ValueError("Zu wenig Historie für Saisonalitäts-Auswertung")

    durchschnitt = float(monatsrendite_gleicher_monat.mean())
    anzahl_jahre = len(monatsrendite_gleicher_monat)

    signal = "LONG" if durchschnitt >= 0 else "SHORT"
    score = round(max(-1.0, min(1.0, durchschnitt * 5)), 4)

    price = yahoo_source.get_last_price(ticker)

    return {
        "signal": signal,
        "score": score,
        "price": price,
        "details": (f"Ø-Rendite Monat {aktueller_monat} über {anzahl_jahre} Jahre: "
                    f"{durchschnitt*100:+.2f}%"),
    }
