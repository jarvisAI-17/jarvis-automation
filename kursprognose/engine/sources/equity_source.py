"""
Datenquelle: Einzelaktien-Fundamentaldaten über yfinance (Ticker.info,
Ticker.option_chain, Ticker.insider_transactions, Ticker.earnings_dates).

WICHTIG: Diese Werte existieren nur für Einzelaktien (z.B. SAP.DE, AAPL),
NICHT für Indizes (^GDAXI, ^MDAXI) oder Rohstoff-Futures (BZ=F). Alle
Funktionen geben bei fehlenden Daten None zurück, statt einen Fehler zu
werfen - die aufrufende Methode entscheidet dann, ob sie den Lauf für
dieses Asset überspringt.
"""
import yfinance as yf


def _get_info(yahoo_ticker: str) -> dict:
    try:
        return yf.Ticker(yahoo_ticker).info or {}
    except Exception:
        return {}


def get_analyst_recommendation_mean(yahoo_ticker: str):
    """1.0 = Strong Buy ... 5.0 = Sell. None falls nicht verfügbar (z.B. Index)."""
    info = _get_info(yahoo_ticker)
    val = info.get("recommendationMean")
    return float(val) if val is not None else None


def get_short_percent_of_float(yahoo_ticker: str):
    """z.B. 0.03 = 3% des Streubesitzes leerverkauft. None falls nicht verfügbar."""
    info = _get_info(yahoo_ticker)
    val = info.get("shortPercentOfFloat")
    return float(val) if val is not None else None


def get_held_percent_institutions(yahoo_ticker: str):
    info = _get_info(yahoo_ticker)
    val = info.get("heldPercentInstitutions")
    return float(val) if val is not None else None


def get_put_call_volume_ratio(yahoo_ticker: str):
    """Put/Call-Verhältnis (Volumen) der naechstgelegenen Optionsverfallzeit.
    None, falls das Asset keine gehandelten Optionen hat (z.B. Indizes)."""
    try:
        t = yf.Ticker(yahoo_ticker)
        expirations = t.options
        if not expirations:
            return None
        chain = t.option_chain(expirations[0])
        call_volume = chain.calls["volume"].fillna(0).sum()
        put_volume = chain.puts["volume"].fillna(0).sum()
        if call_volume == 0:
            return None
        return float(put_volume) / float(call_volume)
    except Exception:
        return None


def get_insider_net_shares(yahoo_ticker: str, lookback_days: int = 90):
    """Summe (gekaufte - verkaufte) Insider-Aktien der letzten lookback_days.
    Positiv = Netto-Käufe, negativ = Netto-Verkäufe. None falls keine Daten."""
    try:
        t = yf.Ticker(yahoo_ticker)
        df = t.insider_transactions
        if df is None or df.empty:
            return None
        import pandas as pd
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(days=lookback_days)
        df = df.copy()
        df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
        df = df[df["Start Date"] >= cutoff]
        if df.empty:
            return None

        def _signed_shares(row):
            shares = row.get("Shares", 0) or 0
            text = str(row.get("Text", "")).lower()
            if "sale" in text or "sold" in text:
                return -abs(shares)
            return abs(shares)

        return float(df.apply(_signed_shares, axis=1).sum())
    except Exception:
        return None


def get_latest_earnings_surprise_pct(yahoo_ticker: str):
    """Prozentuale Abweichung des zuletzt gemeldeten Gewinns vom Analysten-
    Konsens (positiv = positive Überraschung). None falls nicht verfügbar."""
    try:
        t = yf.Ticker(yahoo_ticker)
        df = t.earnings_dates
        if df is None or df.empty:
            return None
        df = df.dropna(subset=["Surprise(%)"])
        if df.empty:
            return None
        df = df.sort_index()
        return float(df["Surprise(%)"].iloc[-1])
    except Exception:
        return None
