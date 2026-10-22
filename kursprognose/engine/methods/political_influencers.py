"""
Methode: Politische Einfluss-Posts (Trump auf Truth Social, Musk auf X).

Beide Accounts posten oft marktbewegende Nachrichten (Zölle, Politik,
Unternehmensankündigungen). Die Post-Texte werden mit demselben
einfachen Lexikon-Sentiment bewertet wie Methode 2 (siehe
sources/news_source.py::score_headline), um keine zweite Scoring-Logik
zu pflegen.

WICHTIG: Dies ist ein MAKRO-Signal (wie 'geopolitical') - dasselbe
Ergebnis wird pro Lauf für ALLE Assets verwendet (Cache), damit nicht
für jedes der 5 Assets erneut (teilweise kostenpflichtige) API-Aufrufe
ausgelöst werden.

Benötigt in config.yaml -> api_keys:
  x_bearer_token:        Bearer Token aus dem X Developer Portal (pay-per-use,
                          developer.x.com - ca. 0,005 $ pro gelesenem Post)
  truth_social_api_key:  API-Key eines Drittanbieter-Scrapers (z.B. SocialCrawl,
                          ScrapeCreators - je 100 kostenlose Test-Credits)
  truth_social_api_base: Basis-URL dieses Anbieters

Fehlt einer der Keys, wird die jeweilige Quelle einfach übersprungen
(kein Absturz) - liefern beide keine Daten, wirft die Methode einen
Fehler (Lauf wird dann wie gewohnt übersprungen, siehe run_predictions.py).
"""
from config_loader import load_config
from sources import x_source, truth_social_source, news_source, yahoo_source

_cache = {}


def _fetch_and_score(params: dict):
    if "result" in _cache:
        return _cache["result"]

    cfg = load_config()
    keys = cfg.get("api_keys", {})
    max_results = params.get("max_posts_je_account", 10)

    all_posts = []

    x_token = keys.get("x_bearer_token")
    if x_token:
        all_posts += x_source.get_recent_posts("elonmusk", x_token, max_results=max_results)

    ts_key = keys.get("truth_social_api_key")
    ts_base = keys.get("truth_social_api_base")
    if ts_key:
        all_posts += truth_social_source.get_recent_posts(
            ts_key, ts_base, max_results=max_results
        )

    total_score = sum(news_source.score_headline(p) for p in all_posts)
    _cache["result"] = (total_score, len(all_posts))
    return _cache["result"]


def predict(asset_cfg: dict, params: dict) -> dict:
    total_score, post_count = _fetch_and_score(params)

    if post_count == 0:
        raise ValueError(
            "Keine Posts von X/Truth Social erhalten - fehlen die API-Keys "
            "(api_keys.x_bearer_token / truth_social_api_key in config.yaml) "
            "oder war die Anfrage erfolglos?"
        )

    signal = "LONG" if total_score >= 0 else "SHORT"

    try:
        price = yahoo_source.get_last_price(asset_cfg["yahoo_ticker"])
    except Exception:
        price = None

    return {
        "signal": signal,
        "score": float(total_score),
        "price": price,
        "details": f"{post_count} Posts (Musk/Trump) analysiert, Score-Summe={total_score}",
    }
