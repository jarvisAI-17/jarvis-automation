"""
Methode: Korrelationsverschiebung (Correlation Breakdown).

Logik: vergleicht die kurzfristige rollierende Korrelation zwischen
Asset und einem Referenzindex mit der langfristigen durchschnittlichen
Korrelation. Bricht die Korrelation stark ein (= ungewöhnliche
Entkopplung) -> als Unsicherheitssignal gewertet -> SHORT.
Normale/stabile Korrelation -> LONG.
"""
from sources import yahoo_source

STANDARD_BENCHMARKS = {
    "DAX": "^STOXX50E",
    "MDAX": "^GDAXI",
    "SAP": "^GDAXI",
    "AAPL": "^GSPC",
    "OEL": "^GSPC",
}
FALLBACK_BENCHMARK = "^GSPC"


def predict(asset_cfg: dict, params: dict) -> dict:
    ticker = asset_cfg["yahoo_ticker"]
    symbol = asset_cfg["symbol"]
    kurz_tage = params.get("kurz_tage", 15)
    lang_tage = params.get("lang_tage", 90)
    benchmark = params.get("benchmark_ticker") or STANDARD_BENCHMARKS.get(symbol, FALLBACK_BENCHMARK)

    asset_returns = yahoo_source.get_returns(ticker, lookback_days=lang_tage + 10)
    bench_returns = yahoo_source.get_returns(benchmark, lookback_days=lang_tage + 10)

    df = asset_returns.to_frame("asset").join(bench_returns.to_frame("bench"), how="inner")
    if len(df) < lang_tage:
        raise ValueError("Zu wenig gemeinsame Historie für Korrelationsberechnung")

    korr_lang = df["asset"].corr(df["bench"])
    korr_kurz = df["asset"].iloc[-kurz_tage:].corr(df["bench"].iloc[-kurz_tage:])

    if korr_lang is None or korr_kurz is None or pd_isna(korr_lang) or pd_isna(korr_kurz):
        raise ValueError("Korrelation konnte nicht berechnet werden (zu wenig Varianz?)")

    abweichung = korr_lang - korr_kurz  # positiv = Korrelation ist eingebrochen

    signal = "SHORT" if abweichung > 0.3 else "LONG"
    score = round(max(-1.0, min(1.0, abweichung)), 4)

    price = yahoo_source.get_last_price(ticker)

    return {
        "signal": signal,
        "score": score,
        "price": price,
        "details": (f"Korrelation zu {benchmark}: langfristig={korr_lang:.2f}, "
                    f"kurzfristig={korr_kurz:.2f} (Abweichung={abweichung:+.2f})"),
    }


def pd_isna(x):
    import pandas as pd
    return pd.isna(x)
