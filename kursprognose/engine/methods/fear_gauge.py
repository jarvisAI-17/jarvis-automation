"""
Methode 23: Angstbarometer VIX (nur DAX/MDAX).

Der VDAX-NEW ist über Yahoo nicht abrufbar; der VIX (US-Optionsvolatilität)
läuft eng mit dem VDAX und wirkt über Nacht auf Europa.
  - Tagesveränderung des VIX: steigende Angst → SHORT, fallende → LONG
  - Extremniveau (z-Wert ggü. 60 Tagen > 1,5): Angst übertrieben → Gegenbewegung
    nach oben wahrscheinlicher (+0,5); sehr niedrige Angst (z < -1) → Sorglosigkeit (-0,25)
Score = -VIX-Tagesänderung in % / 5 + Extremkomponente.
"""
import statistics

from sources import yahoo_source


def predict(asset_cfg: dict, params: dict) -> dict:
    if asset_cfg["symbol"] not in params.get("assets", ["DAX", "MDAX"]):
        raise ValueError(f"Angstbarometer für {asset_cfg['symbol']} nicht verfügbar")
    v = yahoo_source.get_price_history("^VIX", lookback_days=100)["Close"]
    if len(v) < 40:
        raise ValueError("Zu wenig VIX-Historie")
    last, prev = float(v.iloc[-1]), float(v.iloc[-2])
    win = [float(x) for x in v.iloc[-61:-1]]
    mu, sd = statistics.mean(win), statistics.pstdev(win) or 1.0
    z = (last - mu) / sd
    chg = (last / prev - 1) * 100
    extreme = 0.5 if z > 1.5 else (-0.25 if z < -1.0 else 0.0)
    score = -chg / 5.0 + extreme
    lage = "Angst hoch (Gegenbewegung)" if z > 1.5 else "Sorglosigkeit" if z < -1.0 else "normal"
    return {
        "signal": "LONG" if score >= 0 else "SHORT",
        "score": round(score, 4),
        "price": yahoo_source.get_last_price(asset_cfg["yahoo_ticker"]),
        "details": f"VIX {last:.2f} ({chg:+.1f} % ggü. Vortag), z={z:+.2f} ggü. 60 Tagen → {lage}",
    }
