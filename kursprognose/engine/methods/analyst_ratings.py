"""
Methode: Analysten-Ratings (Konsens-Empfehlung).
Nur sinnvoll für Einzelaktien (SAP, Apple), nicht für Indizes/Rohstoffe.

Nutzt bevorzugt Finnhub (zuverlässigere, strukturierte Buy/Hold/Sell-Zahlen),
fällt bei Fehlern/fehlendem Key auf die yfinance-Fallback-Logik zurück.
"""
from config_loader import load_config
from sources import equity_source, finnhub_source, yahoo_source


def _safe_price(ticker):
    try:
        return yahoo_source.get_last_price(ticker)
    except Exception:
        return None


def predict(asset_cfg: dict, params: dict) -> dict:
    ticker = asset_cfg["yahoo_ticker"]
    symbol = asset_cfg["symbol"]
    cfg = load_config()
    finnhub_key = cfg.get("api_keys", {}).get("finnhub")

    if finnhub_key:
        trend = finnhub_source.get_recommendation_trend(symbol, finnhub_key)
        if trend:
            buy = (trend.get("buy") or 0) + (trend.get("strongBuy") or 0)
            sell = (trend.get("sell") or 0) + (trend.get("strongSell") or 0)
            hold = trend.get("hold") or 0
            total = buy + sell + hold
            if total > 0:
                net_score = (buy - sell) / total  # -1..+1
                signal = "LONG" if net_score >= 0 else "SHORT"
                return {
                    "signal": signal,
                    "score": round(net_score, 4),
                    "price": _safe_price(ticker),
                    "details": (f"Finnhub-Konsens ({trend.get('period', '-')}): "
                                f"{buy} Buy / {hold} Hold / {sell} Sell"),
                }

    # Fallback: yfinance recommendationMean
    rec_mean = equity_source.get_analyst_recommendation_mean(ticker)
    if rec_mean is None:
        raise ValueError(
            f"Keine Analysten-Ratings für '{ticker}' verfügbar (Finnhub & yfinance ohne Daten)"
        )

    signal = "LONG" if rec_mean < 3.0 else "SHORT"
    score = round((3.0 - rec_mean) / 2.0, 4)

    return {
        "signal": signal,
        "score": score,
        "price": _safe_price(ticker),
        "details": f"yfinance-Fallback: recommendationMean={rec_mean:.2f} (1=Strong Buy, 5=Sell)",
    }
