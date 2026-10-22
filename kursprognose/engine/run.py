"""
Kursprognose - Cloud-Lauf (v2).

    python run.py --slot morning|afternoon|evening --indir in --outdir out [--claude claude.json]
    python run.py --recompute --indir in --outdir out      # nur Kalibrierung + Auswertung neu

Dokumente:
  days/<YYYY-MM-DD>
    {date, upd, a: {SYM: {
        s:  {mid: [sig, score, px, slot, details, csig, strength]},
              sig    = Rohsignal der Methode (L/S)
              csig   = kalibriertes Signal (L/S/N): Score relativ zum Median der
                       letzten 60 Tage derselben Methode/desselben Assets; N = neutral
              strength = 0..1 (Abstand zum Median in MAD-Einheiten, gekappt)
        h:  {mid: [[slot, sig, score, px], ...]},
        ev: {v:2, d1, c0, c1, ok:{mid:0|1}, okc:{mid:0|1},          # 1 Handelstag
                  d5, c5, ok5:{...}, okc5:{...}} }}}               # 5 Handelstage
    Auswertung: Schlusskurs Prognosetag -> Schlusskurs naechster (bzw. 5.) Handelstag.
    Nur finale Tageskurse (Datum < heute, oder heute ab 22:00 Berlin).
  prices/all  {upd, s: {SYM: [[date, close], ...]}}
  meta/status {upd, lastRun, assets, methods}
"""
import argparse, glob, importlib, json, logging, os, statistics, sys, traceback
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_loader import load_config, get_assets, get_methods  # noqa: E402

TZ = ZoneInfo("Europe/Berlin")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("kp")
SLOT_ORDER = {"morning": 0, "afternoon": 1, "evening": 2}
CAL_WINDOW, CAL_MIN = 60, 15        # Kalibrierfenster (Handelstage), Mindesthistorie
NEUTRAL_Z = 0.25                     # |z| darunter -> neutral
CLAUDE_MID = "21"


def r(x, n=4):
    try:
        return None if x is None else round(float(x), n)
    except Exception:
        return None


def load_in_days(indir):
    days = {}
    for f in glob.glob(os.path.join(indir, "**", "*.json"), recursive=True):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict) and "data" in d and "version" in d and isinstance(d["data"], dict):
            d = d["data"]
        if isinstance(d, dict) and "date" in d and "a" in d:
            days[d["date"]] = d
    return days


# ---------------------------------------------------------------- Kalibrierung
def calibrate(days, only=None):
    """Setzt csig/strength fuer alle Signale. Nutzt nur Scores frueherer Tage
    (kein Blick in die Zukunft). Gibt Menge geaenderter Tage zurueck."""
    changed = set()
    hist = {}  # (sym, mid) -> [scores frueherer Tage]
    for d in sorted(days):
        doc = days[d]
        for sym, ad in doc.get("a", {}).items():
            for mid, x in ad.get("s", {}).items():
                while len(x) < 7:
                    x.append(None)
                sig, score = x[0], x[1]
                prev = hist.setdefault((sym, mid), [])
                if mid == CLAUDE_MID:
                    conf = x[6] if x[6] is not None else 0.5
                    cs, st = (sig if conf >= 0.55 else "N"), r(max(0.0, (conf - 0.5) * 2), 3)
                elif score is None or len(prev) < CAL_MIN:
                    cs, st = sig, None           # zu wenig Historie: Rohsignal
                else:
                    win = prev[-CAL_WINDOW:]
                    med = statistics.median(win)
                    mad = statistics.median([abs(v - med) for v in win])
                    if mad == 0:
                        if score == med:
                            cs, st = "N", 0.0
                        else:
                            cs, st = ("L" if score > med else "S"), 1.0
                    else:
                        z = (score - med) / (1.4826 * mad)
                        cs = "N" if abs(z) < NEUTRAL_Z else ("L" if z > 0 else "S")
                        st = r(min(1.0, abs(z) / 2.0), 3)
                if only is None or d in only:
                    if x[5] != cs or x[6] != st:
                        x[5], x[6] = cs, st
                        changed.add(d)
                if score is not None and mid != CLAUDE_MID:
                    prev.append(score)
    return changed


# ---------------------------------------------------------------- Auswertung
def final_closes(prices, now):
    today = now.date().isoformat()
    after_close = now.hour >= 22
    out = {}
    for sym, rows in prices.items():
        out[sym] = [(d, c) for d, c in rows if d < today or (d == today and after_close)]
    return out


def evaluate(days, closes):
    changed = set()
    for d, doc in days.items():
        for sym, ad in doc.get("a", {}).items():
            rows = closes.get(sym) or []
            idx = {dt: i for i, (dt, _) in enumerate(rows)}
            if d not in idx:
                continue
            i0 = idx[d]
            c0 = rows[i0][1]
            ev = ad.get("ev") or {}
            new = dict(ev) if ev.get("v") == 2 else {"v": 2}
            upd = False
            for h, key in ((1, ""), (5, "5")):
                if i0 + h >= len(rows) or ("c" + (key or "1")) in new:
                    continue
                dh, ch = rows[i0 + h]
                act = "L" if ch > c0 else "S"
                ok, okc = {}, {}
                for mid, x in ad.get("s", {}).items():
                    ok[mid] = 1 if x[0] == act else 0
                    cs = x[5] if len(x) > 5 else None
                    if cs in ("L", "S"):
                        okc[mid] = 1 if cs == act else 0
                new["c0"] = r(c0, 3)
                new["d" + (key or "1")] = dh
                new["c" + (key or "1")] = r(ch, 3)
                new["ok" + key] = ok
                new["okc" + key] = okc
                upd = True
            if upd or (ev and ev.get("v") != 2):
                if not upd:  # alte Auswertung ohne finalen Folgekurs verwerfen
                    new = None
                if new:
                    ad["ev"] = new
                else:
                    ad.pop("ev", None)
                changed.add(d)
    return changed


# ---------------------------------------------------------------- Hauptlauf
def run(slot, indir, outdir, claude_file=None, recompute=False):
    cfg = load_config()
    assets = get_assets(cfg)
    methods = get_methods(cfg, enabled_only=True)
    now = datetime.now(TZ)
    today = now.date().isoformat()
    days = load_in_days(indir)
    changed, errors, ok_count = set(), [], 0
    from sources import yahoo_source

    # Kurse
    prices = {"upd": now.isoformat(timespec="seconds"), "s": {}}
    for a in assets:
        try:
            h = yahoo_source.get_price_history(a["yahoo_ticker"], lookback_days=400)
            prices["s"][a["symbol"]] = [[idx.date().isoformat(), round(float(c), 3)]
                                        for idx, c in h["Close"].items()]
        except Exception as exc:
            errors.append(f"Historie {a['symbol']}: {exc}")

    # Prognosen
    if not recompute:
        doc = days.get(today) or {"date": today, "a": {}}
        for a in assets:
            sym = a["symbol"]
            ad = doc["a"].setdefault(sym, {"s": {}, "h": {}})
            for m in methods:
                if m.get("module") == "claude":
                    continue
                mid = str(m["id"])
                try:
                    mod = importlib.import_module(m["module"])
                    res = mod.predict(a, m.get("params", {}))
                    sig = "L" if res["signal"] == "LONG" else "S"
                    sc, px = r(res.get("score")), r(res.get("price"), 3)
                    det = (res.get("details") or "")[:300]
                    ad["s"][mid] = [sig, sc, px, slot, det, None, None]
                    hist = [h for h in ad["h"].get(mid, []) if h[0] != slot]
                    hist.append([slot, sig, sc, px])
                    hist.sort(key=lambda h: SLOT_ORDER.get(h[0], 9))
                    ad["h"][mid] = hist
                    ok_count += 1
                except Exception as exc:
                    msg = str(exc).strip().splitlines()[0][:160] if str(exc).strip() else type(exc).__name__
                    errors.append(f"{sym}/{m['name']}: {msg}")
        # Claude-Methode (vom Lauf per Websuche erstellt)
        if claude_file and os.path.exists(claude_file):
            try:
                cj = json.load(open(claude_file, encoding="utf-8"))
                for sym, v in cj.items():
                    if sym not in doc["a"]:
                        continue
                    ad = doc["a"][sym]
                    sig = "L" if str(v.get("signal", "")).upper().startswith("L") else "S"
                    conf = max(0.5, min(1.0, float(v.get("confidence", 0.5))))
                    px = next((x[2] for x in ad["s"].values() if x[2] is not None), None)
                    det = (v.get("reason") or "")[:600]
                    ad["s"][CLAUDE_MID] = [sig, r((1 if sig == "L" else -1) * conf), px, slot, det, None, r(conf, 3)]
                    hist = [h for h in ad["h"].get(CLAUDE_MID, []) if h[0] != slot]
                    hist.append([slot, sig, r(conf, 3), px])
                    hist.sort(key=lambda h: SLOT_ORDER.get(h[0], 9))
                    ad["h"][CLAUDE_MID] = hist
                    ok_count += 1
            except Exception as exc:
                errors.append(f"Claude-Methode: {exc}")
        elif claude_file:
            errors.append("Claude-Methode: keine Einschaetzung erstellt")
        doc["upd"] = now.isoformat(timespec="seconds")
        days[today] = doc
        changed.add(today)

    # Kalibrierung (Historie bleibt stabil, nur heute + neue Tage aendern sich)
    closes = final_closes(prices["s"], now) if prices["s"] else {}
    if recompute:
        for doc in days.values():
            for ad in doc.get("a", {}).values():
                ad.pop("ev", None)
                for x in ad.get("s", {}).values():
                    while len(x) < 7:
                        x.append(None)
                    x[5] = x[6] = None
        calibrate(days)
        changed |= set(days)
    else:
        need = {d for d, doc in days.items()
                if any(len(x) < 7 or x[5] is None for ad in doc.get("a", {}).values() for x in ad.get("s", {}).values())}
        need.add(today)
        changed |= calibrate(days, only=need)

    # Auswertung
    if closes:
        changed |= evaluate(days, closes)

    status = {
        "upd": now.isoformat(timespec="seconds"),
        "lastRun": {"at": now.isoformat(timespec="seconds"), "slot": "recompute" if recompute else slot,
                    "date": today, "ok": ok_count, "errors": errors[:80], "nErrors": len(errors),
                    "evalMode": "close-to-close (1T/5T), kalibriert v2"},
        "assets": [{"symbol": a["symbol"], "name": a.get("name", a["symbol"]),
                    "ticker": a["yahoo_ticker"]} for a in assets],
        "methods": [{"id": m["id"], "name": m["name"], "label": m["label"],
                     "enabled": bool(m.get("enabled", True))} for m in get_methods(cfg, False)],
    }

    manifest = []
    def put(coll, did, data):
        p = os.path.join(outdir, coll, did + ".json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        manifest.append({"collection": coll, "doc_id": did, "file": os.path.abspath(p),
                         "kb": round(os.path.getsize(p) / 1024, 1)})
    for d in sorted(changed):
        if d in days:
            put("days", d, days[d])

    # Alarme
    new_alerts, mail_obj = [], None
    if not recompute and prices["s"]:
        try:
            import alerts as alerts_mod
            existing = set()
            for f in glob.glob(os.path.join(indir, "**", "alerts", "*.json"), recursive=True):
                existing.add(os.path.basename(f)[:-5])
            try:
                vix = [float(x) for x in yahoo_source.get_price_history("^VIX", lookback_days=120)["Close"]]
            except Exception:
                vix = None
            cand = alerts_mod.compute(prices["s"], days.get(today), today, now.isoformat(timespec="seconds"),
                                      cfg.get("alerts"), vix)
            new_alerts = [a for a in cand if a["id"] not in existing]
            for a in new_alerts:
                put("alerts", a["id"], a)
            mail_obj = alerts_mod.mail(new_alerts, days.get(today), cfg.get("alerts"))
            if mail_obj:
                json.dump(mail_obj, open(os.path.join(outdir, "mail.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            status["lastRun"]["alerts"] = [a["id"] for a in new_alerts]
        except Exception as exc:
            errors.append(f"Alarme: {exc}")
            status["lastRun"]["errors"] = errors[:80]
            status["lastRun"]["nErrors"] = len(errors)
    if prices["s"]:
        put("prices", "all", prices)
    put("meta", "status", status)
    json.dump(manifest, open(os.path.join(outdir, "manifest.json"), "w"), indent=1)
    print(json.dumps({"ok": ok_count, "errors": len(errors),
                      "new_alerts": [f"{a['level']}: {a['title']}" for a in new_alerts],
                      "mail": os.path.join(os.path.abspath(outdir), "mail.json") if mail_obj else None,
                      "writes": manifest}, indent=1))


def run_alerts_only(indir, outdir):
    """Kurz-Check: nur Alarmregeln fuer DAX/MDAX, ohne Prognosen. Schreibt nur neue Alarme."""
    import alerts as alerts_mod
    from sources import yahoo_source
    cfg = load_config()
    acfg = cfg.get("alerts") or {}
    syms = acfg.get("assets", ["DAX", "MDAX"])
    now = datetime.now(TZ)
    today = now.date().isoformat()
    tick = {a["symbol"]: a["yahoo_ticker"] for a in get_assets(cfg)}
    prices = {}
    for s in syms:
        h = yahoo_source.get_price_history(tick[s], lookback_days=400)
        prices[s] = [[i.date().isoformat(), round(float(c), 3)] for i, c in h["Close"].items()]
    try:
        vix = [float(x) for x in yahoo_source.get_price_history("^VIX", lookback_days=120)["Close"]]
    except Exception:
        vix = None
    days = load_in_days(indir)
    existing = {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(indir, "**", "alerts", "*.json"), recursive=True)}
    cand = alerts_mod.compute(prices, days.get(today), today, now.isoformat(timespec="seconds"), acfg, vix)
    new = [a for a in cand if a["id"] not in existing]
    manifest = []
    for a in new:
        a["source"] = "kurzcheck"
        p = os.path.join(outdir, "alerts", a["id"] + ".json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(a, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        manifest.append({"collection": "alerts", "doc_id": a["id"], "file": os.path.abspath(p)})
    m = alerts_mod.mail(new, days.get(today), acfg)
    mp = None
    if m:
        os.makedirs(outdir, exist_ok=True)
        mp = os.path.join(os.path.abspath(outdir), "mail.json")
        json.dump(m, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    kurs = {s: f"{prices[s][-1][1]:.0f} ({(prices[s][-1][1]/prices[s][-2][1]-1)*100:+.2f} %)" for s in syms}
    print(json.dumps({"kurse": kurs, "new_alerts": [f"{a['level']}: {a['title']}" for a in new],
                      "mail": mp, "writes": manifest}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", choices=list(SLOT_ORDER), default="evening")
    ap.add_argument("--indir", default="in")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--claude", default=None)
    ap.add_argument("--recompute", action="store_true")
    ap.add_argument("--alerts-only", action="store_true")
    a = ap.parse_args()
    try:
        if a.alerts_only:
            run_alerts_only(a.indir, a.outdir)
        else:
            run(a.slot, a.indir, a.outdir, a.claude, a.recompute)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
