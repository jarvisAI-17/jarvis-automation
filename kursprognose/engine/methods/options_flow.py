"""
Methode: Optionsmarkt-Flow (Put/Call-Volumen-Ratio).
Nur sinnvoll für Assets mit gehandelten Optionen (SAP, Apple),
nicht für Indizes ohne Yahoo-Optionsdaten oder Rohstoff-Futures.

Logik: Put/Call-Ratio < 1 (mehr Calls als Puts gehandelt) -> LONG,
>= 1 (mehr Puts als Calls) -> SHORT. Sehr hohe Put/Call-Ratios gelten
klassisch als Angst-Indikator.
"""
from sources import equity_source, yahoo_source


def predict(asset_cfg: dict, params: dict) -> dict:
    ticker = asset_cfg["yahoo_ticker"]
    ratio = equity_source.get_put_call_volume_ratio(ticker)

    if ratio is None:
        raise ValueError(
            f"Keine Optionsmarkt-Daten für '{ticker}' verfügbar "
            f"(vermutlich keine gehandelten Optionen)"
        )

    signal = "LONG" if ratio < 1.0 else "SHORT"
    score = round(max(-1.0, min(1.0, 1.0 - ratio)), 4)

    try:
        price = yahoo_source.get_last_price(ticker)
    except Exception:
        price = None

    return {
        "signal": signal,
        "score": score,
        "price": price,
        "details": f"Put/Call-Volumen-Ratio (nächster Verfall)={ratio:.2f}",
    }
