"""
Methode: Volatilitätsregime. Gilt für alle Assets.

Logik: kurzfristige realisierte Volatilität (z.B. 10 Tage) vs.
längerfristige (z.B. 60 Tage). Steigt die kurzfristige Vola deutlich
über die langfristige -> erhöhte Unsicherheit -> SHORT (Risiko-Aus),
sonst -> LONG (ruhiges Umfeld).
"""
from sources import yahoo_source


def predict(asset_cfg: dict, params: dict) -> dict:
    ticker = asset_cfg["yahoo_ticker"]
    kurz_tage = params.get("kurz_tage", 10)
    lang_tage = params.get("lang_tage", 60)

    returns = yahoo_source.get_returns(ticker, lookback_days=lang_tage + 10)
    if len(returns) < lang_tage:
        raise ValueError("Zu wenig Kurshistorie für Volatilitätsberechnung")

    vola_kurz = returns[-kurz_tage:].std()
    vola_lang = returns.std()

    verhaeltnis = vola_kurz / vola_lang if vola_lang > 0 else 1.0
    signal = "SHORT" if verhaeltnis > 1.3 else "LONG"
    score = round(max(-1.0, min(1.0, 1.0 - verhaeltnis)), 4)

    price = yahoo_source.get_last_price(ticker)

    return {
        "signal": signal,
        "score": score,
        "price": price,
        "details": (f"Vola {kurz_tage}T={vola_kurz*100:.2f}% vs. {lang_tage}T="
                    f"{vola_lang*100:.2f}% (Verhältnis={verhaeltnis:.2f})"),
    }
