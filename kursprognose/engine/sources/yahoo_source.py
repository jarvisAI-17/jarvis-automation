"""
Datenquelle: Yahoo Finance (kostenlos, kein API-Key nötig) über die
Bibliothek yfinance. Liefert historische Kursdaten für ein Asset.

Austauschbar: Wer eine andere Kursquelle nutzen möchte (z.B. eine
Broker-API), muss hier nur get_price_history() /  get_last_price()
mit derselben Signatur neu implementieren - der Rest des Systems
bleibt unverändert.

NEU (für die zusätzlichen Methoden): get_returns() liefert die
Tages-Renditen eines Tickers - wird von currency_correlation,
commodity_correlation, sector_rotation und correlation_breakdown
genutzt, um zwei beliebige Ticker miteinander zu vergleichen.

NEU (Rate-Limit-Schutz): get_price_history() cacht Ergebnisse pro
Prozesslauf (Ticker + lookback_days). Bei 20 Methoden x 5 Assets fragen
mehrere Methoden denselben Ticker mehrfach ab (z.B. Referenz-Ticker wie
EURUSD=X oder GC=F) - ohne Cache waeren das unnoetig viele Yahoo-Finance-
Anfragen in kurzer Zeit, was zu "possibly delisted; no price data found"-
Fehlern durch Rate-Limiting fuehren kann. Zusaetzlich ein kurzer Retry
mit Wartezeit, falls Yahoo einmal kurz nicht antwortet.
"""
import time

import yfinance as yf
import pandas as pd

_cache: dict[tuple[str, int], pd.DataFrame] = {}


def get_price_history(yahoo_ticker: str, lookback_days: int = 90,
                       max_retries: int = 2, retry_wait_seconds: float = 3.0) -> pd.DataFrame:
    """Liefert ein DataFrame mit OHLCV-Daten der letzten `lookback_days` Tage.
    Wird innerhalb eines Prozesslaufs pro (Ticker, lookback_days) gecacht."""
    cache_key = (yahoo_ticker, lookback_days)
    if cache_key in _cache:
        return _cache[cache_key]

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            ticker = yf.Ticker(yahoo_ticker)
            hist = ticker.history(period=f"{lookback_days}d", interval="1d")
            if hist.empty:
                raise ValueError(f"Keine Kursdaten für Ticker '{yahoo_ticker}' erhalten.")
            hist = hist.dropna(subset=["Close"])
            _cache[cache_key] = hist
            return hist
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(retry_wait_seconds)

    raise ValueError(
        f"Keine Kursdaten für Ticker '{yahoo_ticker}' erhalten nach {max_retries} Versuchen "
        f"(letzter Fehler: {last_error})"
    )


def get_last_price(yahoo_ticker: str) -> float:
    """Aktuellster verfügbarer Schlusskurs / Kurs."""
    hist = get_price_history(yahoo_ticker, lookback_days=5)
    return float(hist["Close"].iloc[-1])


def get_returns(yahoo_ticker: str, lookback_days: int = 90) -> pd.Series:
    """Tägliche prozentuale Renditen (pct_change) der letzten lookback_days.
    Wird für Korrelations-/Vergleichsmethoden genutzt (zwei Ticker
    gegenüberstellen, z.B. Asset vs. EUR/USD oder Asset vs. Gold)."""
    hist = get_price_history(yahoo_ticker, lookback_days=lookback_days)
    return hist["Close"].pct_change().dropna()