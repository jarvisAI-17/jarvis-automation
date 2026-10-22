"""
Methode: Rohstoffkorrelation (Gold als Risiko-Barometer). Gilt für alle
Assets - steigender Goldpreis wird klassisch als "Risk-off"-Signal
gelesen (Kapitalflucht in sichere Häfen), daher hier als Gegenindikator
für risikobehaftete Assets (Aktien/Indizes) genutzt.

Für das Asset 'OEL' (Öl) selbst ist Gold als Referenz weniger passend -
über params.referenz_ticker lässt sich das je nach Bedarf umstellen.
"""
from sources import yahoo_source


def predict(asset_cfg: dict, params: dict) -> dict:
    ticker = asset_cfg["yahoo_ticker"]
    referenz = params.get("referenz_ticker", "GC=F")  # Gold Futures
    lookback_days = params.get("lookback_days", 10)

    ref_returns = yahoo_source.get_returns(referenz, lookback_days=lookback_days + 5)
    if ref_returns.empty:
        raise ValueError(f"Keine Kursdaten für Referenz-Ticker '{referenz}'")

    kum_rendite = float((1 + ref_returns[-lookback_days:]).prod() - 1)

    # steigt Gold deutlich -> Risk-off -> SHORT-Tendenz fürs Asset
    signal = "SHORT" if kum_rendite > 0 else "LONG"
    score = round(max(-1.0, min(1.0, -kum_rendite * 10)), 4)

    price = yahoo_source.get_last_price(ticker)

    return {
        "signal": signal,
        "score": score,
        "price": price,
        "details": f"Gold-Rendite ({lookback_days}T)={kum_rendite*100:+.2f}% (Referenz={referenz})",
    }
