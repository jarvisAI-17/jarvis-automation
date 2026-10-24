# Morgenbriefing

- Aufgabe: „Morgenbriefing“ – trig_01Vqdjv2MDGaAwkZtWJh7wUu
- Zeitplan: Mo–Fr 09:10 (Europe/Berlin), Push-Benachrichtigung an
- Ziel-Artefakt: https://claude.ai/artifact/MLQMR9a6oBFxRdWswcuxbv
- Stand: 22.10.2026

---

```text
/morning
Erstelle mein Morning Brief. Sprache des Briefs: Deutsch. Zeitzone: Europe/Berlin.
Meine Rolle: Consultant – gewichte Kundentermine, Abstimmungen und offene Rückfragen von Kunden/Projektbeteiligten entsprechend.

WICHTIG – immer dasselbe Artefakt aktualisieren, nie ein neues anlegen:
- Ziel-Artefakt: https://claude.ai/artifact/MLQMR9a6oBFxRdWswcuxbv
- Zuerst mit dem Artifact-Tool action "read" (url wie oben, OHNE path) den aktuellen Stand lesen. Danach mit action "read" und path "index.html" die Seite als Datei speichern.
- Diese Datei als Vorlage nehmen: HTML-Struktur, CSS und Design (VEGA-Designsystem: Nacht-/Tag-Theme, Sora / IBM Plex Sans / JetBrains Mono, VEGA-Lockup oben links, Bernstein = Handlung, Blau = Information) unverändert lassen und nur die Inhalte ersetzen: Datum und „Stand“-Uhrzeit, Überschrift (h1), die drei Tagesabschnitte, „Braucht dich“ (mit Anzahl im Badge), „Erledigt“ (mit Anzahl im Badge), Wetter, DAX (Kennzahl + Liste). Leere Abschnitte bei „Braucht dich“/„Erledigt“ mit einem kurzen Satz füllen statt sie zu löschen. Den Assistenten in Texten „VEGA“ nennen.
- Die geänderte Datei mit action "publish", url = https://claude.ai/artifact/MLQMR9a6oBFxRdWswcuxbv und file_path = die geänderte Datei veröffentlichen. KEIN publish ohne url. Wird die Veröffentlichung wegen einer neueren Version abgelehnt: die zurückgegebene Version als Grundlage nehmen, Inhalte erneut einsetzen und noch einmal veröffentlichen.
- Die Design-Vorgaben des /morning-Skills (eigene Schriften, Farben, Layout) gelten hier NICHT; das VEGA-Design der Vorlage hat Vorrang.

Sections:
- Braucht dich / Erledigt: aus Gmail (und Kalender, falls verbunden) – offene Punkte und kürzlich Erledigtes, jeweils mit Link zur Mail.
- Aktuelles Wetter in Körbecke (Möhnesee, NRW): aktuelle Temperatur, Bedingungen und Tagesverlauf (Höchst-/Tiefstwert, Regenrisiko) per Websuche, mit Quellen und Stand-Uhrzeit.
- Aktuelle DAX-Kurse: DAX-Indexstand mit Veränderung zum Vortag sowie die auffälligsten Gewinner und Verlierer im DAX, per Websuche mit Zeitstempel der Daten.
```
