"""
Methode: Zinsdifferenz Fed/EZB - über die kostenlose FRED-API (St. Louis Fed).

FRED spiegelt auch EZB-Reihen, daher genügt ein einziger API-Key (FRED)
für beide Zinssätze:
  - Fed:  FEDFUNDS (Effective Federal Funds Rate, monatlich)
  - EZB:  ECBDFR   (ECB Deposit Facility Rate, täglich)

Logik: Differenz Fed minus EZB. Steigt die Differenz (Fed relativ
restriktiver/höher) -> tendenziell stärkerer USD -> hier als SHORT-Signal
gewertet (v.a. für die europäischen Assets DAX/MDAX/SAP gedacht),
fallende/negative Differenz -> LONG.
"""
from config_loader import load_config
from sources import fred_source, yahoo_source


def predict(asset_cfg: dict, params: dict) -> dict:
    ticker = asset_cfg["yahoo_ticker"]
    cfg = load_config()
    api_key = cfg.get("api_keys", {}).get("fred")
    if not api_key:
        raise ValueError("Kein FRED-API-Key in config.yaml (api_keys.fred) hinterlegt")

    fed_series = params.get("fed_series", "FEDFUNDS")
    ecb_series = params.get("ecb_series", "ECBDFR")

    fed_rate = fred_source.get_latest_value(fed_series, api_key)
    ecb_rate = fred_source.get_latest_value(ecb_series, api_key)

    if fed_rate is None or ecb_rate is None:
        raise ValueError(
            f"Keine aktuellen Zinsdaten von FRED erhalten (fed={fed_rate}, ecb={ecb_rate})"
        )

    differenz = fed_rate - ecb_rate
    signal = "SHORT" if differenz >= 0 else "LONG"
    score = round(max(-1.0, min(1.0, differenz / 3.0)), 4)

    try:
        price = yahoo_source.get_last_price(ticker)
    except Exception:
        price = None

    return {
        "signal": signal,
        "score": score,
        "price": price,
        "details": f"Fed={fed_rate:.2f}%, EZB={ecb_rate:.2f}% (Differenz={differenz:+.2f} Pkt.)",
    }
