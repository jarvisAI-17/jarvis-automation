"""
Methode 24: Marktbreite DAX 40 (DAX/MDAX; für den MDAX als Stimmungsindikator
des deutschen Gesamtmarkts).

  - Anteil der DAX-Werte über ihrem 50-Tage-Schnitt (Trendbreite)
  - Veränderung dieses Anteils über 5 Tage (verbessert / verschlechtert sich die Breite?)
  - Anteil steigender Werte am letzten Handelstag (Advance/Decline)
Score = (Anteil>SMA50 - 0,5) + 2·Δ5T + (Anteil steigend - 0,5)
Eine breit getragene Bewegung ist stabiler als eine, die nur von 2-3 Schwergewichten kommt.
"""
import pandas as pd
import yfinance as yf

from sources import yahoo_source

DAX40 = ["ADS", "AIR", "ALV", "BAS", "BAYN", "BEI", "BMW", "BNR", "CBK", "CON", "DB1", "DBK",
         "DHL", "DTE", "DTG", "ENR", "EOAN", "FRE", "G1A", "HEI", "HEN3", "HNR1", "IFX", "MBG",
         "MRK", "MTX", "MUV2", "P911", "QIA", "RHM", "RWE", "SAP", "SHL", "SIE", "SRT3", "SY1",
         "VNA", "VOW3", "ZAL", "FME"]
_cache = {}


def _closes():
    if "c" in _cache:
        return _cache["c"]
    tickers = [t + ".DE" for t in DAX40]
    df = yf.download(tickers, period="120d", interval="1d", progress=False, auto_adjust=True, threads=True)
    c = df["Close"] if isinstance(df.columns, pd.MultiIndex) else df
    c = c.dropna(axis=1, thresh=60).ffill()
    _cache["c"] = c
    return c


def predict(asset_cfg: dict, params: dict) -> dict:
    if asset_cfg["symbol"] not in params.get("assets", ["DAX", "MDAX"]):
        raise ValueError(f"Marktbreite für {asset_cfg['symbol']} nicht verfügbar")
    c = _closes()
    if c.shape[1] < 25 or len(c) < 60:
        raise ValueError(f"Zu wenig Einzelwerte für Marktbreite ({c.shape[1]})")
    sma = c.rolling(50).mean()
    above = (c > sma).sum(axis=1) / c.notna().sum(axis=1)
    a_now, a_5 = float(above.iloc[-1]), float(above.iloc[-6])
    adv = float((c.iloc[-1] > c.iloc[-2]).sum() / c.shape[1])
    score = (a_now - 0.5) + 2 * (a_now - a_5) + (adv - 0.5)
    return {
        "signal": "LONG" if score >= 0 else "SHORT",
        "score": round(score, 4),
        "price": yahoo_source.get_last_price(asset_cfg["yahoo_ticker"]),
        "details": (f"{a_now*100:.0f} % der {c.shape[1]} DAX-Werte über SMA50 (vor 5 Tagen {a_5*100:.0f} %), "
                    f"{adv*100:.0f} % gestern/heute im Plus"),
    }
