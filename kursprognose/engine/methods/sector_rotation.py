"""
Methode: Sektorrotation / relative Stärke gegenüber einem Referenzindex.

Logik: Performance des Assets der letzten `lookback_days` verglichen
mit der Performance eines Referenzindex. Outperformance -> LONG
(relative Stärke), Underperformance -> SHORT.

Referenzindex je Asset-Symbol (Default-Zuordnung unten, per params.
benchmark_ticker global überschreibbar). Da config.yaml nur globale
Methodenparameter erlaubt, ist die Zuordnung hier im Code hinterlegt -
bei Bedarf gerne auf eine Pro-Asset-Konfiguration erweitern.
"""
from sources import yahoo_source

STANDARD_BENCHMARKS = {
    "DAX": "^STOXX50E",
    "MDAX": "^STOXX50E",
    "SAP": "^GDAXI",
    "AAPL": "^IXIC",
    "OEL": "^GSPC",
}
FALLBACK_BENCHMARK = "^GSPC"


def predict(asset_cfg: dict, params: dict) -> dict:
    ticker = asset_cfg["yahoo_ticker"]
    symbol = asset_cfg["symbol"]
    lookback_days = params.get("lookback_days", 20)
    benchmark = params.get("benchmark_ticker") or STANDARD_BENCHMARKS.get(symbol, FALLBACK_BENCHMARK)

    asset_returns = yahoo_source.get_returns(ticker, lookback_days=lookback_days + 5)
    bench_returns = yahoo_source.get_returns(benchmark, lookback_days=lookback_days + 5)

    asset_perf = float((1 + asset_returns[-lookback_days:]).prod() - 1)
    bench_perf = float((1 + bench_returns[-lookback_days:]).prod() - 1)
    relative_staerke = asset_perf - bench_perf

    signal = "LONG" if relative_staerke >= 0 else "SHORT"
    score = round(max(-1.0, min(1.0, relative_staerke * 5)), 4)

    price = yahoo_source.get_last_price(ticker)

    return {
        "signal": signal,
        "score": score,
        "price": price,
        "details": (f"{symbol} {lookback_days}T={asset_perf*100:+.2f}% vs. "
                    f"{benchmark}={bench_perf*100:+.2f}% (rel.={relative_staerke*100:+.2f}%)"),
    }
