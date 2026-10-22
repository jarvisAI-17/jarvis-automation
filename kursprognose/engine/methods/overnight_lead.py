"""
Methode 22: Übernacht-Vorlauf (nur DAX/MDAX).

Idee: Was nach dem Xetra-Schluss (17:30) bzw. vor der Eröffnung passiert,
steckt noch nicht im DAX-Schlusskurs, wirkt aber auf den nächsten Handelstag.
  - S&P-500-Future (ES=F) und Nasdaq-100-Future (NQ=F): Veränderung seit dem
    letzten Xetra-Schluss (15-Minuten-Kurse)
  - Nikkei 225 (^N225): Tagesveränderung, sofern der letzte Nikkei-Handelstag
    nach dem letzten Xetra-Schluss liegt (Morgenlauf)
Score = gewichtete Veränderung in Prozent (ES 50 %, NQ 30 %, Nikkei 20 %).
"""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import yfinance as yf

from sources import yahoo_source

TZ = ZoneInfo("Europe/Berlin")


def _last_xetra_close(now):
    d = now.date()
    cand = datetime.combine(d, time(17, 30), TZ)
    if now < cand:
        cand -= timedelta(days=1)
    while cand.weekday() >= 5:
        cand -= timedelta(days=1)
    return cand


def _move_since(ticker, since):
    h = yf.Ticker(ticker).history(period="5d", interval="15m")
    if h.empty:
        raise ValueError(f"Keine Intraday-Daten für {ticker}")
    h = h.dropna(subset=["Close"])
    idx = h.index.tz_convert(TZ)
    before = h["Close"][idx <= since]
    if before.empty:
        raise ValueError(f"Kein Kurs von {ticker} vor dem Xetra-Schluss")
    ref, last = float(before.iloc[-1]), float(h["Close"].iloc[-1])
    return (last / ref - 1) * 100


def predict(asset_cfg: dict, params: dict) -> dict:
    if asset_cfg["symbol"] not in params.get("assets", ["DAX", "MDAX"]):
        raise ValueError(f"Übernacht-Vorlauf für {asset_cfg['symbol']} nicht verfügbar")
    now = datetime.now(TZ)
    since = _last_xetra_close(now)
    parts, score, wsum = [], 0.0, 0.0
    for tk, w, name in (("ES=F", 0.5, "S&P-Future"), ("NQ=F", 0.3, "Nasdaq-Future")):
        try:
            mv = _move_since(tk, since)
            score += w * mv; wsum += w
            parts.append(f"{name} {mv:+.2f} %")
        except Exception as exc:
            parts.append(f"{name} n/v")
    try:
        nk = yahoo_source.get_price_history("^N225", lookback_days=10)["Close"]
        last_day = nk.index[-1].date()
        if last_day > since.date():
            mv = (float(nk.iloc[-1]) / float(nk.iloc[-2]) - 1) * 100
            score += 0.2 * mv; wsum += 0.2
            parts.append(f"Nikkei {mv:+.2f} %")
        else:
            parts.append("Nikkei noch ohne neuen Handelstag")
    except Exception:
        parts.append("Nikkei n/v")
    if wsum == 0:
        raise ValueError("Keine Vorlauf-Daten verfügbar")
    score = score / wsum
    return {
        "signal": "LONG" if score >= 0 else "SHORT",
        "score": round(score, 4),
        "price": yahoo_source.get_last_price(asset_cfg["yahoo_ticker"]),
        "details": f"Seit Xetra-Schluss {since:%d.%m. %H:%M}: " + "; ".join(parts) + f" → gewichtet {score:+.2f} %",
    }
