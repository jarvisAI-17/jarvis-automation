"""
Methode: Insider-Transaktionen (meldepflichtige Käufe/Verkäufe).
Nur sinnvoll für Einzelaktien (SAP, Apple), nicht für Indizes/Rohstoffe.

Logik: Netto-Insider-Aktivität (gekaufte minus verkaufte Aktien) der
letzten `lookback_days`. Netto-Käufe -> LONG, Netto-Verkäufe -> SHORT.
"""
from sources import equity_source, yahoo_source


def predict(asset_cfg: dict, params: dict) -> dict:
    ticker = asset_cfg["yahoo_ticker"]
    lookback_days = params.get("lookback_days", 90)

    net_shares = equity_source.get_insider_net_shares(ticker, lookback_days=lookback_days)

    if net_shares is None:
        raise ValueError(
            f"Keine Insider-Transaktionsdaten für '{ticker}' verfügbar"
        )

    signal = "LONG" if net_shares >= 0 else "SHORT"
    # grobe Normierung: 100.000 Aktien Nettobewegung ~ Score 1.0
    score = round(max(-1.0, min(1.0, net_shares / 100_000)), 4)

    try:
        price = yahoo_source.get_last_price(ticker)
    except Exception:
        price = None

    return {
        "signal": signal,
        "score": score,
        "price": price,
        "details": f"Netto-Insider-Aktivität (letzte {lookback_days} Tage): {net_shares:+.0f} Aktien",
    }
