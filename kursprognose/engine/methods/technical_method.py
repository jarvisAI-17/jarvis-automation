"""
Methode 1: Technische Kursanalyse (Yahoo Finance).

Schnittstelle: predict(asset_cfg, params) -> dict mit
    signal:  "LONG" oder "SHORT"
    score:   float, positiver Wert = Richtung LONG, negativ = SHORT
             (Stärke des Signals, nicht auf festen Bereich normiert)
    price:   zuletzt verfügbarer Kurs (für spätere Auswertung)
    details: kurzer Text zur Nachvollziehbarkeit

Logik (bewusst einfach & transparent gehalten, gut erweiterbar):
  - Gleitende Durchschnitte (SMA kurz vs. SMA lang) -> Trendrichtung
  - RSI -> überkauft/überverkauft als Korrektur des Trendsignals
  - MACD-Histogramm als drittes Kriterium
Die drei Teilsignale werden zu einem Score aufsummiert; Score > 0 -> LONG.
"""
import numpy as np
import pandas as pd

from sources import yahoo_source


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def _compute_macd_hist(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd - signal_line


def predict(asset_cfg: dict, params: dict) -> dict:
    lookback_days = params.get("lookback_days", 90)
    sma_short_n = params.get("sma_short", 20)
    sma_long_n = params.get("sma_long", 50)
    rsi_period = params.get("rsi_period", 14)

    hist = yahoo_source.get_price_history(asset_cfg["yahoo_ticker"], lookback_days=lookback_days)
    close = hist["Close"]

    sma_short = close.rolling(window=sma_short_n).mean().iloc[-1]
    sma_long = close.rolling(window=sma_long_n).mean().iloc[-1]
    rsi = _compute_rsi(close, rsi_period).iloc[-1]
    macd_hist = _compute_macd_hist(close).iloc[-1]
    last_price = float(close.iloc[-1])

    score = 0.0
    reasons = []

    # 1) Trendrichtung über SMA-Kreuzung
    if pd.notna(sma_short) and pd.notna(sma_long):
        if sma_short > sma_long:
            score += 1.0
            reasons.append(f"SMA{sma_short_n} > SMA{sma_long_n} (Aufwärtstrend)")
        else:
            score -= 1.0
            reasons.append(f"SMA{sma_short_n} < SMA{sma_long_n} (Abwärtstrend)")

    # 2) RSI: überkauft (>70) dämpft LONG, überverkauft (<30) dämpft SHORT
    if rsi > 70:
        score -= 0.5
        reasons.append(f"RSI={rsi:.1f} (überkauft)")
    elif rsi < 30:
        score += 0.5
        reasons.append(f"RSI={rsi:.1f} (überverkauft)")
    else:
        reasons.append(f"RSI={rsi:.1f} (neutral)")

    # 3) MACD-Histogramm
    if pd.notna(macd_hist):
        if macd_hist > 0:
            score += 0.5
            reasons.append("MACD-Histogramm positiv")
        else:
            score -= 0.5
            reasons.append("MACD-Histogramm negativ")

    signal = "LONG" if score > 0 else "SHORT"

    return {
        "signal": signal,
        "score": round(float(score), 4),
        "price": last_price,
        "details": "; ".join(reasons),
    }
