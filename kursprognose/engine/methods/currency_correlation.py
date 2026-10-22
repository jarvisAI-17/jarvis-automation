"""
Methode: Währungskorrelation (EUR/USD als Proxy für USD-Stärke). Gilt
für alle Assets, ist aber v.a. für DAX/MDAX/SAP (europäische Exporteure)
konzeptionell sinnvoll - ein schwächerer Euro begünstigt europäische
Exporteure tendenziell.

Logik: 10-Tage-Rendite von EUR/USD. Fällt der Euro (Rendite < 0) ->
LONG-Tendenz für das Asset, steigt der Euro -> SHORT-Tendenz.
"""
from sources import yahoo_source


def predict(asset_cfg: dict, params: dict) -> dict:
    ticker = asset_cfg["yahoo_ticker"]
    referenz = params.get("referenz_ticker", "EURUSD=X")
    lookback_days = params.get("lookback_days", 10)

    ref_returns = yahoo_source.get_returns(referenz, lookback_days=lookback_days + 5)
    if ref_returns.empty:
        raise ValueError(f"Keine Kursdaten für Referenz-Ticker '{referenz}'")

    kum_rendite = float((1 + ref_returns[-lookback_days:]).prod() - 1)

    signal = "LONG" if kum_rendite <= 0 else "SHORT"
    score = round(max(-1.0, min(1.0, -kum_rendite * 10)), 4)

    price = yahoo_source.get_last_price(ticker)

    return {
        "signal": signal,
        "score": score,
        "price": price,
        "details": f"EUR/USD-Rendite ({lookback_days}T)={kum_rendite*100:+.2f}%",
    }
