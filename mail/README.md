# JARVIS-Mail-Template

HTML-Mail-Vorlage im JARVIS-Design (Nachtkopf mit Logo, orange Akzentlinie, heller Inhalt) plus PowerShell-Funktionen zum Befüllen, Vorschauen und Versenden.

| Datei | Zweck |
|---|---|
| `jarvis-mail-template.html` | Vorlage mit `{{PLATZHALTERN}}`, Tabellen-Layout + Inline-CSS, Outlook-Fallbacks (VML-Button, feste 600 px) |
| `jarvis-logo.png` | Lockup 260×64 in 2× (520×128), wird als Inline-Anhang `cid:jarvis-logo.png` eingebettet |
| `JarvisMail.ps1` | `New-JarvisMailHtml`, `Save-JarvisMailPreview`, `Send-JarvisMail` (Microsoft Graph) |

## Platzhalter

`BETREFF`, `VORSCHAU` (Vorschauzeile im Posteingang), `KATEGORIE` (rechts im Kopf), `TITEL`, `ANREDE`, `TEXT`, `FAKTEN_ZEILEN`, `INFO`, `CODE`, `BUTTON_TEXT`, `BUTTON_URL`, `GRUSS`, `ABSENDER_NAME`, `ABSENDER_ROLLE`, `FUSSZEILE`.

Optionale Blöcke stehen zwischen `<!-- BLOCK:NAME -->` und `<!-- /BLOCK:NAME -->` (`FAKTEN`, `INFO`, `CODE`, `BUTTON`) und werden entfernt, wenn sie leer bleiben.

## Nutzung (PowerShell)

```powershell
. .\JarvisMail.ps1
$html = New-JarvisMailHtml -Betreff 'Statusbericht KW 43' -Kategorie 'Status-Update' `
        -Titel 'Migration abgeschlossen' -Anrede 'Hallo Herr Müller,' `
        -Text "Die Migration ist durch.`n`nAlle Dienste laufen stabil." `
        -Fakten ([ordered]@{ 'Dauer' = '3 h 12 min'; 'Postfächer' = '412' }) `
        -AbsenderName 'S. Grewing' -AbsenderRolle 'Consultant'

Save-JarvisMailPreview -Html $html -Path .\vorschau.html   # Browser-Vorschau, Logo als data:-URI

Connect-MgGraph -Scopes Mail.Send
Send-JarvisMail -From 'ich@firma.de' -To 'kunde@firma.de' -Betreff 'Statusbericht KW 43' -Html $html -WhatIf
```

`Send-JarvisMail` hat `ConfirmImpact = 'High'`, fragt also vor dem Senden nach; `-WhatIf` zeigt nur, was passieren würde. Getestet mit PowerShell 7.4.

## Nutzung über Claude / Gmail

Template befüllen, Logo als Inline-Anhang (`inline: true`, Dateiname `jarvis-logo.png`) mitgeben, zusätzlich eine Plain-Text-Fassung als `body`. Standardmäßig erst als Entwurf anlegen.

## Designentscheidung

Inhalt hell statt Nacht-Theme: dunkle Mails werden von Outlook/Gmail im Dark Mode unzuverlässig umgefärbt und drucken schlecht. Die Marke trägt der dunkle Kopf. Farben aus den JARVIS-Tokens (Tag-Theme): `orange` #b84a08 für den Button, `sky` #0b6a99 für Links/Labels, `ink` #0f171d, `ink-muted` #4e5f6b.
