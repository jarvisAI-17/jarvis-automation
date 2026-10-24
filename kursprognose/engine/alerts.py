"""
Alarme für DAX/MDAX (Krisen, starke Bewegungen, Kaufgelegenheiten).

Jede Regel liefert höchstens einen Alarm je Tag und Stufe. Die ID
<datum>_<asset>_<regel>_<stufe> verhindert doppelte Meldungen über die drei
Tagesläufe hinweg; eine Verschärfung (Warnung -> Kritisch) wird neu gemeldet.

Stufen: info | warnung | kritisch      Art: chance (Kaufsignal) | risiko | info
"""
import statistics


def _de(x, d=0):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

DEFAULTS = {
    "assets": ["DAX", "MDAX"],
    "move1d_warn": -2.0, "move1d_crit": -3.5, "move1d_up": 2.5,
    "move3d_warn": -5.0, "move3d_crit": -8.0,
    "dd_warn": -10.0, "dd_crit": -20.0,
    "rsi_low": 25.0, "rsi_high": 75.0, "overheat_sma50": 7.0,
    "vix_level": 30.0, "vix_jump": 20.0,
    "overnight": 1.5,
    "consensus_agree": 0.8, "consensus_min": 6, "claude_conf": 0.6,
    "mail_levels": ["warnung", "kritisch"],
    "mail_to": "dergrewing@live.de",
    "app_url": "https://claude.ai/artifact/1fegs9crRCQvYy3NT5tzGn",
}
LEVEL_ORDER = {"info": 0, "warnung": 1, "kritisch": 2}


def _rsi(closes, n=14):
    if len(closes) < n + 1:
        return None
    gains, losses = [], []
    for a, b in zip(closes[-n - 1:-1], closes[-n:]):
        d = b - a
        gains.append(max(d, 0)); losses.append(max(-d, 0))
    ag, al = sum(gains) / n, sum(losses) / n
    if al == 0:
        return 100.0
    return 100 - 100 / (1 + ag / al)


def _sma(closes, n):
    return sum(closes[-n:]) / n if len(closes) >= n else None


def compute(prices, today_doc, today, now_iso, cfg_alerts=None, vix=None):
    """prices: {SYM: [[date, close], ...]} (letzter Eintrag = aktueller Kurs)
    today_doc: days/<heute> mit Signalen; vix: Liste Schlusskurse (letzter = aktuell)."""
    P = dict(DEFAULTS); P.update(cfg_alerts or {})
    out = []

    def add(asset, rule, level, kind, title, text, values):
        out.append({"id": f"{today}_{asset}_{rule}_{level}", "date": today, "at": now_iso,
                    "asset": asset, "rule": rule, "level": level, "kind": kind,
                    "title": title, "text": text, "values": values, "ack": False})

    for sym in P["assets"]:
        rows = prices.get(sym) or []
        c = [x[1] for x in rows]
        if len(c) < 60:
            continue
        last, prev = c[-1], c[-2]
        ch1 = (last / prev - 1) * 100
        ch3 = (last / c[-4] - 1) * 100
        hi = max(c[-252:])
        dd, dd_prev = (last / hi - 1) * 100, (prev / max(c[-253:-1]) - 1) * 100
        rsi = _rsi(c)
        s50, s200 = _sma(c, 50), _sma(c, 200)
        s200_prev = _sma(c[:-1], 200)
        v = {"kurs": round(last, 2), "tag_pct": round(ch1, 2), "3tage_pct": round(ch3, 2),
             "abstand_hoch_pct": round(dd, 2), "rsi14": round(rsi, 1) if rsi is not None else None}

        # 1) Starke Tagesbewegung
        if ch1 <= P["move1d_crit"]:
            add(sym, "move1d", "kritisch", "risiko", f"{sym} bricht ein: {ch1:+.1f} %",
                f"{sym} verliert heute {ch1:+.2f} % auf {_de(last)} Punkte. Solche Tage treten meist bei Krisen oder Schocks auf.", v)
        elif ch1 <= P["move1d_warn"]:
            add(sym, "move1d", "warnung", "risiko", f"{sym} deutlich im Minus: {ch1:+.1f} %",
                f"{sym} fällt heute um {ch1:+.2f} % auf {_de(last)} Punkte.", v)
        elif ch1 >= P["move1d_up"]:
            add(sym, "move1d_up", "info", "info", f"{sym} stark im Plus: {ch1:+.1f} %",
                f"{sym} steigt heute um {ch1:+.2f} % auf {_de(last)} Punkte.", v)

        # 2) Abverkauf über 3 Tage
        if ch3 <= P["move3d_crit"]:
            add(sym, "move3d", "kritisch", "risiko", f"{sym} Ausverkauf: {ch3:+.1f} % in 3 Tagen",
                f"Seit drei Handelstagen {ch3:+.2f} %. Breiter Abverkauf, Knock-out-Risiko bei LONG-Positionen hoch.", v)
        elif ch3 <= P["move3d_warn"]:
            add(sym, "move3d", "warnung", "risiko", f"{sym} Abverkauf: {ch3:+.1f} % in 3 Tagen",
                f"{sym} hat in drei Handelstagen {ch3:+.2f} % verloren.", v)

        # 3) Korrektur / Bärenmarkt (nur beim Unterschreiten)
        if dd <= P["dd_crit"] < dd_prev:
            add(sym, "drawdown", "kritisch", "risiko", f"{sym} im Bärenmarkt ({dd:.1f} % vom Hoch)",
                f"{sym} liegt jetzt {dd:.1f} % unter dem 52-Wochen-Hoch von {_de(hi)}.", v)
        elif dd <= P["dd_warn"] < dd_prev:
            add(sym, "drawdown", "warnung", "risiko", f"{sym} in der Korrektur ({dd:.1f} % vom Hoch)",
                f"{sym} ist mehr als 10 % unter das 52-Wochen-Hoch von {_de(hi)} gefallen.", v)

        # 4) Kapitulation -> antizyklische Kaufchance
        vz = None
        if vix and len(vix) > 61:
            win = vix[-61:-1]
            vz = (vix[-1] - statistics.mean(win)) / (statistics.pstdev(win) or 1)
        cap_rsi = rsi is not None and rsi < P["rsi_low"]
        cap_vix = vz is not None and vz > 2 and vix[-1] >= 25 and dd <= -8
        if cap_rsi or cap_vix:
            lvl = "kritisch" if (cap_rsi and cap_vix) else "warnung"
            grund = []
            if cap_rsi: grund.append(f"RSI {rsi:.0f} (stark überverkauft)")
            if cap_vix: grund.append(f"VIX {vix[-1]:.1f} mit z={vz:.1f} bei {dd:.1f} % Abstand zum Hoch")
            add(sym, "capitulation", lvl, "chance", f"KAUFCHANCE {sym}: Panik/Überverkauft",
                "Antizyklisches Kaufsignal: " + ", ".join(grund) + ". Historisch folgen auf solche Phasen oft Erholungen – "
                "Einstieg gestaffelt und mit weiter KO-Schwelle, nicht in den fallenden Markt hinein alles auf einmal.", v)

        # 5) Überhitzung
        if rsi is not None and s50 and rsi > P["rsi_high"] and (last / s50 - 1) * 100 >= P["overheat_sma50"]:
            add(sym, "overheat", "warnung", "risiko", f"{sym} überhitzt (RSI {rsi:.0f})",
                f"{sym} liegt {(last/s50-1)*100:.1f} % über dem 50-Tage-Schnitt bei RSI {rsi:.0f}. Rücksetzer-Risiko erhöht, Gewinne absichern.", v)

        # 6) Trendbruch 200-Tage-Linie
        if s200 and s200_prev:
            if last < s200 * 0.99 and prev >= s200_prev * 0.99 and min(c[-11:-1]) > _sma(c[:-1], 200) * 0.99:
                add(sym, "sma200_down", "warnung", "risiko", f"{sym} unter 200-Tage-Linie",
                    f"{sym} schließt/notiert mit {_de(last)} unter der 200-Tage-Linie ({_de(s200)}). Langfristiger Trend wackelt.", v)
            elif last > s200 * 1.01 and prev <= s200_prev * 1.01 and max(c[-11:-1]) < _sma(c[:-1], 200) * 1.01:
                add(sym, "sma200_up", "info", "chance", f"{sym} zurück über 200-Tage-Linie",
                    f"{sym} steigt mit {_de(last)} wieder über die 200-Tage-Linie ({_de(s200)}). Mögliche Trendwende nach oben.", v)

        # 7) Übernacht-Schock (Methode 22) und starkes Gesamtsignal
        ad = (today_doc or {}).get("a", {}).get(sym, {})
        s = ad.get("s", {})
        on = s.get("22")
        if on and on[1] is not None:
            if on[1] <= -P["overnight"]:
                add(sym, "overnight", "warnung", "risiko", f"Übernacht-Schock für {sym}: {on[1]:+.1f} %",
                    f"US-Futures/Asien seit Xetra-Schluss gewichtet {on[1]:+.2f} %. Schwache Eröffnung wahrscheinlich. {on[4]}", v)
            elif on[1] >= P["overnight"]:
                add(sym, "overnight_up", "info", "chance", f"Starker Rückenwind für {sym}: {on[1]:+.1f} %",
                    f"US-Futures/Asien seit Xetra-Schluss gewichtet {on[1]:+.2f} %. {on[4]}", v)
        l = sum(1 for x in s.values() if len(x) > 5 and x[5] == "L")
        sh = sum(1 for x in s.values() if len(x) > 5 and x[5] == "S")
        n = l + sh
        cl = s.get("21")
        if n >= P["consensus_min"]:
            agree = max(l, sh) / n
            dirn = "L" if l > sh else "S"
            claude_ok = cl and cl[0] == dirn and (cl[6] or 0) >= (P["claude_conf"] - 0.5) * 2
            if agree >= P["consensus_agree"] and claude_ok:
                word = "LONG" if dirn == "L" else "SHORT"
                add(sym, f"consensus_{dirn}", "warnung", "chance" if dirn == "L" else "risiko",
                    f"Starkes Gesamtsignal {sym}: {word}",
                    f"{max(l, sh)} von {n} kalibrierten Methoden und die Claude-Nachrichtenanalyse zeigen {word}. "
                    f"Hinweis: Die Methoden sind einzeln noch nicht statistisch belastbar.", v)

    # Marktweite Panik (VIX)
    if vix and len(vix) > 2:
        vj = (vix[-1] / vix[-2] - 1) * 100
        if vix[-1] >= P["vix_level"] or (vj >= P["vix_jump"] and vix[-1] >= 22):
            lvl = "kritisch" if (vix[-1] >= P["vix_level"] and vj >= P["vix_jump"] / 2) else "warnung"
            add("MARKT", "vix", lvl, "risiko", f"Panik-Barometer: VIX {vix[-1]:.1f} ({vj:+.0f} %)",
                f"Die Angst an den Märkten steigt sprunghaft (VIX {vix[-1]:.1f}, {vj:+.1f} % zum Vortag). "
                "Erfahrungsgemäß fallen DAX/MDAX in solchen Phasen mit; Kaufchancen ergeben sich oft erst nach dem Höhepunkt der Angst.",
                {"vix": round(vix[-1], 2), "vix_pct": round(vj, 1)})
    return out


def mail(new_alerts, today_doc, cfg_alerts=None):
    P = dict(DEFAULTS); P.update(cfg_alerts or {})
    sel = [a for a in new_alerts if a["level"] in P["mail_levels"]]
    if not sel:
        return None
    sel.sort(key=lambda a: (-LEVEL_ORDER[a["level"]], a["kind"] != "chance"))
    top = sel[0]
    tag = "KAUFCHANCE" if any(a["kind"] == "chance" for a in sel) and top["kind"] == "chance" else top["level"].upper()
    subject = f"[Kursprognose] {tag}: {top['title']}" + (f" (+{len(sel)-1} weitere)" if len(sel) > 1 else "")
    lines, html = [], []
    for a in sel:
        lab = {"chance": "Kaufchance", "risiko": "Risiko", "info": "Info"}[a["kind"]]
        lines.append(f"[{a['level'].upper()} · {lab}] {a['title']}\n{a['text']}\n")
        col = "#137346" if a["kind"] == "chance" else ("#bf2a2a" if a["level"] == "kritisch" else "#7a5600")
        html.append(f'<div style="border:1px solid #d3dde4;border-radius:10px;padding:12px 14px;margin:0 0 12px">'
                    f'<div style="font:600 12px/16px Arial;letter-spacing:.06em;color:{col};text-transform:uppercase">{a["level"]} · {lab}</div>'
                    f'<div style="font:600 17px/24px Arial;color:#0f171d;margin:4px 0">{a["title"]}</div>'
                    f'<div style="font:14px/21px Arial;color:#0f171d">{a["text"]}</div></div>')
    ctx = []
    for sym in ("DAX", "MDAX"):
        s = (today_doc or {}).get("a", {}).get(sym, {}).get("s", {})
        l = sum(1 for x in s.values() if len(x) > 5 and x[5] == "L"); sh = sum(1 for x in s.values() if len(x) > 5 and x[5] == "S")
        cl = s.get("21")
        ctx.append(f"{sym}: Methoden {l} LONG / {sh} SHORT" + (f", Claude {'LONG' if cl[0]=='L' else 'SHORT'}" if cl else ""))
    foot = ("Stand der Signale: " + " · ".join(ctx) + f"\nApp: {P['app_url']}\n"
            "Automatischer Hinweis deines Kursprognose-Systems. Keine Anlageberatung.")
    body = "\n".join(lines) + "\n" + foot
    htmlb = ('<div style="max-width:620px;font-family:Arial,sans-serif">'
             '<div style="font:600 20px/28px Arial;color:#0f171d;margin:0 0 12px">VEGA Kursprognose – Alarm</div>'
             + "".join(html) +
             f'<p style="font:13px/20px Arial;color:#4e5f6b">{" · ".join(ctx)}<br>'
             f'<a href="{P["app_url"]}" style="color:#0b6a99">App öffnen</a><br>Automatischer Hinweis. Keine Anlageberatung.</p></div>')
    return {"to": P["mail_to"], "subject": subject, "body": body, "htmlBody": htmlb, "alert_ids": [a["id"] for a in sel]}
