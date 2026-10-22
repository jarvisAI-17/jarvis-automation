"""
Methode: Gewinnüberraschungen (Earnings Surprise).
Nur sinnvoll für Einzelaktien (SAP, Apple), nicht für Indizes/Rohstoffe.

Nutzt bevorzugt Finnhub, fällt bei Fehlern/fehlendem Key auf yfinance zurück.
"""
from config_loader import load_config
from sources import equity_source, finnhub_source, yahoo_source


def predict(asset_cfg: dict, params: dict) -> dict:
    ticker = asset_cfg["yahoo_ticker"]
    symbol = asset_cfg["symbol"]
    cfg = load_config()
    finnhub_key = cfg.get("api_keys", {}).get("finnhub")

    surprise_pct = None
    source_label = None

    if finnhub_key:
        surprise_pct = finnhub_source.get_latest_earnings_surprise_pct(symbol, finnhub_key)
        if surprise_pct is not None:
            source_label = "Finnhub"

    if surprise_pct is None:
        surprise_pct = equity_source.get_latest_earnings_surprise_pct(ticker)
        if surprise_pct is not None:
            source_label = "yfinance-Fallback"

    if surprise_pct is None:
        raise ValueError(
            f"Keine Earnings-Surprise-Daten für '{ticker}' verfügbar (Finnhub & yfinance)"
        )

    signal = "LONG" if surprise_pct >= 0 else "SHORT"
    score = round(max(-1.0, min(1.0, surprise_pct / 10.0)), 4)

    try:
        price = yahoo_source.get_last_price(ticker)
    except Exception:
        price = None

    return {
        "signal": signal,
        "score": score,
        "price": price,
        "details": f"{source_label}: letzte Gewinnüberraschung {surprise_pct:+.2f}% vs. Konsens",
    }
