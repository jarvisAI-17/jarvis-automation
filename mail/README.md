# VEGA-Mail-Template

HTML-Mail-Vorlage im VEGA-Design (Nachtkopf mit Logo, Bernstein-Akzentlinie, heller Inhalt) plus PowerShell-Funktionen zum Befüllen, Vorschauen und Versenden.

| Datei | Zweck |
|---|---|
| `vega-mail-template.html` | Vorlage mit `{{PLATZHALTERN}}`, Tabellen-Layout + Inline-CSS, Outlook-Fallbacks (VML-Button, feste 600 px) |
| `vega-logo.png` | Lockup (Variante on-dark) 202×64, als PNG in 2× für 101×32 (404×128), wird als Inline-Anhang `cid:vega-logo.png` eingebettet |
| `VegaMail.ps1` | `New-VegaMailHtml`, `Save-VegaMailPreview`, `Send-VegaMail` (Microsoft Graph) |

## Platzhalter

`BETREFF`, `VORSCHAU` (Vorschauzeile im Posteingang), `KATEGORIE` (rechts im Kopf), `TITEL`, `ANREDE`, `TEXT`, `FAKTEN_ZEILEN`, `INFO`, `CODE`, `BUTTON_TEXT`, `BUTTON_URL`, `GRUSS`, `ABSENDER_NAME`, `ABSENDER_ROLLE`, `FUSSZEILE`.

Optionale Blöcke stehen zwischen `<!-- BLOCK:NAME -->` und `<!-- /BLOCK:NAME -->` (`FAKTEN`, `INFO`, `CODE`, `BUTTON`) und werden entfernt, wenn sie leer bleiben.

## Nutzung (PowerShell)

```powershell
. .\VegaMail.ps1
$html = New-VegaMailHtml -Betreff 'Statusbericht KW 43' -Kategorie 'Status-Update' `
        -Titel 'Migration abgeschlossen' -Anrede 'Hallo Herr Müller,' `
        -Text "Die Migration ist durch.`n`nAlle Dienste laufen stabil." `
        -Fakten ([ordered]@{ 'Dauer' = '3 h 12 min'; 'Postfächer' = '412' }) `
        -AbsenderName 'S. Grewing' -AbsenderRolle 'Consultant'

Save-VegaMailPreview -Html $html -Path .\vorschau.html   # Browser-Vorschau, Logo als data:-URI

Connect-MgGraph -Scopes Mail.Send
Send-VegaMail -From 'ich@firma.de' -To 'kunde@firma.de' -Betreff 'Statusbericht KW 43' -Html $html -WhatIf
```

`Send-VegaMail` hat `ConfirmImpact = 'High'`, fragt also vor dem Senden nach; `-WhatIf` zeigt nur, was passieren würde. Getestet mit PowerShell 7.4.

## Nutzung über Claude / Gmail

Template befüllen, Logo als Inline-Anhang (`inline: true`, Dateiname `vega-logo.png`) mitgeben, zusätzlich eine Plain-Text-Fassung als `body`. Standardmäßig erst als Entwurf anlegen.

## Designentscheidung

Inhalt hell statt Nacht-Theme: dunkle Mails werden von Outlook/Gmail im Dark Mode unzuverlässig umgefärbt und drucken schlecht. Die Marke trägt der dunkle Kopf. Farben aus den VEGA-Tokens (Tag-Theme): `amber` #9a5b00 für den Button, `blue` #2856b8 für Links/Labels, `ink` #0e1526, `ink-muted` #535e73; Kopf `vega-night` #0a0f1c, Akzentlinie `vega-amber` #ffb547.
