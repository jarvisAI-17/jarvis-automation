"""
Datenquelle: Finanznachrichten via RSS-Feeds (kostenlos, siehe config.yaml
-> news_sources). Enthält einen einfachen, eingebauten Sentiment-Scorer
(Deutsch + Englisch), damit keine kostenpflichtige Sentiment-API benötigt
wird. Kann bei Bedarf leicht gegen eine "echte" NLP-Sentiment-API
ausgetauscht werden (score_headline() ersetzen).

Austauschbar: weitere RSS-Feeds einfach in config.yaml -> news_sources
ergänzen. Andere Quelle (z.B. Twitter/X, Reddit) -> eigenes Modul mit
gleicher Rückgabe-Struktur (Liste von Headline-Strings) anlegen.
"""
import time
from datetime import datetime, timedelta, timezone

import feedparser

POSITIVE_WORDS = {
    "steigt", "steigen", "gewinn", "gewinne", "wachstum", "erholung", "boom",
    "rekordhoch", "aufschwung", "optimismus", "kursgewinn", "kursanstieg",
    "positiv", "erholt", "zuversicht", "stark", "stärker", "rally",
    "surge", "rally", "gains", "growth", "recovery", "optimism", "bullish",
    "record", "rise", "rises", "rising", "upbeat", "strong", "boost",
}

NEGATIVE_WORDS = {
    "fällt", "fallen", "verlust", "verluste", "rezession", "abschwung",
    "krise", "einbruch", "kursverlust", "kursrutsch", "sorge", "sorgen",
    "pessimismus", "schwach", "schwächer", "crash", "risiko", "risiken",
    "warnung", "inflation", "zinserhöhung", "konflikt", "sanktionen",
    "decline", "declines", "falling", "recession", "crisis", "slump",
    "bearish", "warning", "risk", "risks", "sanctions", "conflict", "drop",
    "plunge", "sell-off", "selloff", "tumble",
}


def score_headline(text: str) -> int:
    """Sehr einfacher, lexikonbasierter Sentiment-Score einer Schlagzeile.
    +1 pro positivem Wort, -1 pro negativem Wort. Bewusst simpel gehalten
    und leicht durch eine echte NLP-Bibliothek/-API ersetzbar."""
    text_lower = text.lower()
    score = 0
    for word in POSITIVE_WORDS:
        if word in text_lower:
            score += 1
    for word in NEGATIVE_WORDS:
        if word in text_lower:
            score -= 1
    return score


def fetch_headlines(rss_feeds: list, keywords: list, lookback_hours: int = 36,
                     max_headlines: int = 40) -> list:
    """Lädt Schlagzeilen aus den konfigurierten RSS-Feeds, filtert optional
    nach Keywords (falls angegeben) und begrenzt auf max_headlines."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    headlines = []

    for feed_cfg in rss_feeds:
        url = feed_cfg["rss_url"]
        try:
            parsed = feedparser.parse(url)
        except Exception:
            continue

        for entry in parsed.entries:
            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or ""
            full_text = f"{title} {summary}"

            # Zeitfilter (falls Publish-Datum vorhanden, sonst durchlassen)
            published = getattr(entry, "published_parsed", None)
            if published:
                pub_dt = datetime.fromtimestamp(time.mktime(published), tz=timezone.utc)
                if pub_dt < cutoff:
                    continue

            if keywords:
                if not any(kw.lower() in full_text.lower() for kw in keywords):
                    continue

            headlines.append(full_text.strip())
            if len(headlines) >= max_headlines:
                return headlines

    return headlines
