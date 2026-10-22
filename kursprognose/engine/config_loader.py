"""Konfiguration (Cloud-Version). API-Keys kommen aus Umgebungsvariablen
KP_FRED, KP_FINNHUB, KP_ALPHA_VANTAGE - nie aus der Datei."""
import os, yaml
_P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
_c = None
_ENV = {"fred": "KP_FRED", "finnhub": "KP_FINNHUB", "alpha_vantage": "KP_ALPHA_VANTAGE"}

def load_config(path=None):
    global _c
    if _c is not None and path is None:
        return _c
    with open(path or _P, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    keys = cfg.setdefault("api_keys", {})
    for k, env in _ENV.items():
        if os.environ.get(env):
            keys[k] = os.environ[env]
    if path is None:
        _c = cfg
    return cfg

def get_assets(cfg=None):
    return (cfg or load_config())["assets"]

def get_methods(cfg=None, enabled_only=True):
    ms = (cfg or load_config())["methods"]
    return [m for m in ms if m.get("enabled", True)] if enabled_only else ms
