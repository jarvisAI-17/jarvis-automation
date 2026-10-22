"""
Methode: Makro-Ueberraschungsindex (aehnlich Citi Economic Surprise Index).

TODO: kein kostenloses offizielles API bekannt; Alternativen waeren
eigene Berechnung aus mehreren Einzelindikatoren (ifo, ZEW, PMI, US
Non-Farm Payrolls) via FRED-API (kostenlos, https://fred.stlouisfed.org/docs/api/fred/)
oder ein kostenpflichtiger Datenanbieter. Noch nicht implementiert.
"""


def predict(asset_cfg: dict, params: dict) -> dict:
    raise NotImplementedError(
        "macro_surprise_index: benoetigt FRED-API-Anbindung o.ae. - noch nicht implementiert"
    )
