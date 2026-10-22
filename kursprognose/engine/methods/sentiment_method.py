"""
Methode 2: News- & Stimmungsdaten (RSS-Feeds, siehe config.yaml -> news_sources).

Schnittstelle: predict(asset_cfg, params) -> dict (siehe technical_method.py)

Logik: Schlagzeilen zum Asset werden gesammelt (gefiltert über
asset_cfg["news_keywords"]) und mit einem einfachen Lexikon-Sentiment
bewertet (sources/news_source.py::score_headline). Summe der Scores > 0
-> LONG, sonst SHORT. Zusätzlich wird der aktuelle Kurs (für die
Auswertung am Folgetag) über Yahoo Finance nachgeladen.

NEU: für Einzelaktien mit gültigem Alpha-Vantage-Ticker (aktuell SAP,
AAPL) wird zusätzlich der Alpha Vantage NEWS_SENTIMENT-Score eingeholt
und additiv in die Gesamtbewertung eingerechnet (skaliert, damit er in
ähnlicher Größenordnung wie die RSS-Wortliste liegt). Für Indizes/
Rohstoffe (DAX/MDAX/OEL) wird Alpha Vantage bewusst NICHT aufgerufen -
zum einen gibt es dafür keinen sinnvollen Ticker, zum anderen ist das
Tageskontingent mit 25 Anfragen/Tag knapp bemessen.
"""
from config_loader import load_config
from sources import news_source, yahoo_source, alpha_vantage_source

# Nur fuer diese Symbole hat Alpha Vantage einen sinnvollen Ticker UND es
# lohnt sich angesichts des knappen Tageskontingents (25 Anfragen/Tag).
ALPHA_VANTAGE_FAEHIGE_ASSETS = {"SAP", "AAPL"}


def predict(asset_cfg: dict, params: dict) -> dict:
    cfg = load_config()
    rss_feeds = cfg.get("news_sources", [])
    max_headlines = params.get("max_headlines", 40)
    lookback_hours = params.get("lookback_hours", 36)

    headlines = news_source.fetch_headlines(
        rss_feeds=rss_feeds,
        keywords=asset_cfg.get("news_keywords", []),
        lookback_hours=lookback_hours,
        max_headlines=max_headlines,
    )

    total_score = 0
    scored_count = 0
    for headline in headlines:
        s = news_source.score_headline(headline)
        total_score += s
        if s != 0:
            scored_count += 1

    av_detail = ""
    symbol = asset_cfg["symbol"]
    av_key = cfg.get("api_keys", {}).get("alpha_vantage")
    if av_key and symbol in ALPHA_VANTAGE_FAEHIGE_ASSETS:
        av_sentiment = alpha_vantage_source.get_average_sentiment(symbol, av_key)
        if av_sentiment is not None:
            # av_sentiment liegt zwischen -1 und +1 -> auf RSS-Groessenordnung skalieren
            av_beitrag = av_sentiment * 10
            total_score += av_beitrag
            av_detail = f", Alpha-Vantage-Sentiment={av_sentiment:+.2f} (Beitrag={av_beitrag:+.1f})"

    # Kein relevanter Treffer -> neutral leicht positiv gewertet (LONG als
    # Default-Bias vermeiden wir; stattdessen dokumentieren wir das im Detail-Text)
    signal = "LONG" if total_score >= 0 else "SHORT"

    try:
        last_price = yahoo_source.get_last_price(asset_cfg["yahoo_ticker"])
    except Exception:
        last_price = None

    details = (
        f"{len(headlines)} Schlagzeilen analysiert, {scored_count} mit "
        f"Sentiment-Treffer, Score-Summe={total_score:.1f}{av_detail}"
    )

    return {
        "signal": signal,
        "score": float(total_score),
        "price": last_price,
        "details": details,
    }
