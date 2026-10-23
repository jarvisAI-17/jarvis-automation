# jarvis-automation

Code und Prompts der JARVIS-Automatisierungen. Alles läuft in der Cloud (geplante Aufgaben in Claude), kein lokaler Rechner nötig.

## Struktur

```
kursprognose/engine/   Rechenkern der Kursprognose (Python): run.py, alerts.py, methods/, sources/
mail/                  JARVIS-Mail-Template (HTML), Logo und PowerShell-Funktionen zum Versand
prompts/               Sicherung der Prompts aller geplanten Aufgaben (Stand je Datei)
```

## Geplante Aufgaben (Europe/Berlin)

| Aufgabe | Zeitplan | Prompt |
|---|---|---|
| Immobilien-Radar täglich | täglich 06:50 | [immobilien-radar-taeglich.md](prompts/immobilien-radar-taeglich.md) |
| Guten-Morgen-Mail an Kathleen | täglich 07:20 | [guten-morgen-mail-kathleen.md](prompts/guten-morgen-mail-kathleen.md) |
| Kursprognose morning / afternoon / evening | Mo–Fr 09:07, 15:35, 22:07 | [kursprognose-lauf.md](prompts/kursprognose-lauf.md) |
| Morgenbriefing | Mo–Fr 09:10 | [morgenbriefing.md](prompts/morgenbriefing.md) |
| Kursprognose Alarm-Kurzcheck | Mo–Fr 10–14, 16, 17 Uhr (:07) | [kursprognose-alarm-kurzcheck.md](prompts/kursprognose-alarm-kurzcheck.md) |
| Trink-Erinnerung | täglich 11:44 | [trink-erinnerung.md](prompts/trink-erinnerung.md) |
| Immobilien-Radar: Details nachladen | nur manuell | [immobilien-radar-nachladen.md](prompts/immobilien-radar-nachladen.md) |

## Regeln

- **Keine Secrets im Repo.** API-Keys stehen nur in den Aufgaben bzw. als Umgebungsvariablen (`KP_FRED`, `KP_FINNHUB`, `KP_ALPHA_VANTAGE`). In `prompts/` sind sie durch Platzhalter ersetzt. `config.yaml` enthält leere Key-Felder.
- Die Aufgaben laden den Code derzeit noch aus dem Artefakt „JARVIS Kursprognose“ (`engine.zip.b64.txt`). Das Repo ist bis zur Umstellung die Referenz bzw. Sicherung.
