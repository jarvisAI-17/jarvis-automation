"""
Methode: US-Zinsstrukturkurve als Frühindikator. Makro-Signal, gilt
identisch für alle Assets (wie schon bei 'geopolitical' üblich).

Logik: Differenz 10-Jahres- minus 13-Wochen-Rendite (US-Treasuries,
über Yahoo Finance: ^TNX bzw. ^IRX). Positive (normale) Kurve gilt als
Wachstumssignal -> LONG, inverse Kurve (Differenz negativ) gilt
klassisch als Rezessionswarnung -> SHORT.
"""
from sources import yahoo_source


def predict(asset_cfg: dict, params: dict) -> dict:
    ticker = asset_cfg["yahoo_ticker"]
    ticker_10j = params.get("ticker_10j", "^TNX")
    ticker_13w = params.get("ticker_13w", "^IRX")

    rendite_10j = yahoo_source.get_last_price(ticker_10j)
    rendite_13w = yahoo_source.get_last_price(ticker_13w)

    kurve = rendite_10j - rendite_13w  # in Prozentpunkten

    signal = "LONG" if kurve >= 0 else "SHORT"
    score = round(max(-1.0, min(1.0, kurve)), 4)

    price = yahoo_source.get_last_price(ticker)

    return {
        "signal": signal,
        "score": score,
        "price": price,
        "details": f"10J-Rendite={rendite_10j:.2f}%, 13W-Rendite={rendite_13w:.2f}% (Kurve={kurve:+.2f})",
    }
