#Requires -Version 5.1
<#
.SYNOPSIS
    VEGA-Mail: HTML-Template befüllen, lokal vorschauen und per Microsoft Graph senden.

.DESCRIPTION
    Dateien im selben Ordner erwartet:
      vega-mail-template.html   – Template mit {{PLATZHALTERN}}
      vega-logo.png             – Logo, wird als Inline-Anhang (cid:vega-logo.png) eingebettet

    Optionale Blöcke (FAKTEN, INFO, CODE, BUTTON) werden automatisch entfernt,
    wenn die zugehörigen Parameter leer bleiben.

.EXAMPLE
    . .\VegaMail.ps1
    $html = New-VegaMailHtml -Betreff 'Statusbericht KW 43' -Kategorie 'Status-Update' `
            -Titel 'Migration abgeschlossen' -Anrede 'Hallo Herr Müller,' `
            -Text "Die Migration ist durch.`n`nAlle Dienste laufen stabil." `
            -Fakten ([ordered]@{ 'Dauer' = '3 h 12 min'; 'Postfächer' = '412' }) `
            -AbsenderName 'S. Grewing' -AbsenderRolle 'Consultant'
    Save-VegaMailPreview -Html $html -Path .\vorschau.html
    Send-VegaMail -From 'ich@firma.de' -To 'kunde@firma.de' -Betreff 'Statusbericht KW 43' -Html $html -WhatIf
#>

$script:VegaRoot = $PSScriptRoot
if (-not $script:VegaRoot) { $script:VegaRoot = (Get-Location).Path }

function ConvertTo-VegaHtmlText {
    param([string]$Text)
    [System.Net.WebUtility]::HtmlEncode($Text)
}

function New-VegaMailHtml {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Betreff,
        [Parameter(Mandatory)][string]$Titel,
        [Parameter(Mandatory)][string]$Text,
        [string]$Kategorie      = '',
        [string]$Vorschau       = '',
        [string]$Anrede         = 'Hallo,',
        [System.Collections.IDictionary]$Fakten,
        [string]$Info           = '',
        [string]$Code           = '',
        [string]$ButtonText     = '',
        [string]$ButtonUrl      = '',
        [string]$Gruss          = 'Viele Grüße',
        [string]$AbsenderName   = '',
        [string]$AbsenderRolle  = '',
        [string]$Fusszeile      = 'Diese Nachricht wurde mit dem VEGA-Mail-Template erstellt.',
        [switch]$TextIsHtml,
        [string]$TemplatePath   = (Join-Path $script:VegaRoot 'vega-mail-template.html')
    )

    $tpl = Get-Content -Path $TemplatePath -Raw -Encoding UTF8
    $e   = { param($s) ConvertTo-VegaHtmlText $s }

    # Fließtext: Leerzeilen = Absatz, einfache Umbrüche = <br>
    if ($TextIsHtml) {
        $body = $Text
    } else {
        $paras = ($Text -replace "`r", '') -split "`n\s*`n" | Where-Object { $_.Trim() }
        $body  = ($paras | ForEach-Object {
            '<p style="margin:0 0 16px 0;">' + ((& $e $_.Trim()) -replace "`n", '<br>') + '</p>'
        }) -join "`n"
    }

    # Optionale Blöcke entfernen, wenn leer
    $drop = @()
    if (-not $Fakten -or $Fakten.Count -eq 0)          { $drop += 'FAKTEN' }
    if (-not $Info)                                     { $drop += 'INFO' }
    if (-not $Code)                                     { $drop += 'CODE' }
    if (-not ($ButtonText -and $ButtonUrl))             { $drop += 'BUTTON' }
    foreach ($b in $drop) {
        $tpl = [regex]::Replace($tpl, "(?s)\s*<!-- BLOCK:$b\b.*?<!-- /BLOCK:$b -->", '')
    }

    $faktenRows = ''
    if ($Fakten) {
        $faktenRows = ($Fakten.GetEnumerator() | ForEach-Object {
@"
          <tr>
            <td style="padding:10px 12px 10px 0; border-bottom:1px solid #d3dde4; width:40%; font-family:'IBM Plex Sans',Segoe UI,Arial,sans-serif; font-size:12px; line-height:16px; font-weight:500; letter-spacing:0.08em; text-transform:uppercase; color:#4e5f6b;">$(& $e $_.Key)</td>
            <td style="padding:10px 0; border-bottom:1px solid #d3dde4; font-family:'IBM Plex Sans',Segoe UI,Arial,sans-serif; font-size:15px; line-height:24px; font-weight:600; color:#0f171d;">$(& $e ([string]$_.Value))</td>
          </tr>
"@
        }) -join "`n"
    }

    $map = [ordered]@{
        BETREFF        = & $e $Betreff
        VORSCHAU       = & $e $Vorschau
        KATEGORIE      = & $e $Kategorie
        TITEL          = & $e $Titel
        ANREDE         = & $e $Anrede
        TEXT           = $body
        FAKTEN_ZEILEN  = $faktenRows
        INFO           = & $e $Info
        CODE           = & $e $Code
        BUTTON_TEXT    = & $e $ButtonText
        BUTTON_URL     = & $e $ButtonUrl
        GRUSS          = & $e $Gruss
        ABSENDER_NAME  = & $e $AbsenderName
        ABSENDER_ROLLE = & $e $AbsenderRolle
        FUSSZEILE      = & $e $Fusszeile
    }
    foreach ($k in $map.Keys) { $tpl = $tpl.Replace("{{$k}}", [string]$map[$k]) }

    if ($tpl -match '\{\{[A-Z_]+\}\}') { Write-Warning "Unbefüllte Platzhalter: $($Matches[0])" }
    $tpl
}

function Save-VegaMailPreview {
    <# Schreibt eine Browser-Vorschau; das cid-Logo wird dafür als data:-URI eingebettet. #>
    param(
        [Parameter(Mandatory)][string]$Html,
        [Parameter(Mandatory)][string]$Path,
        [string]$LogoPath = (Join-Path $script:VegaRoot 'vega-logo.png')
    )
    $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($LogoPath))
    $Html.Replace('cid:vega-logo.png', "data:image/png;base64,$b64") |
        Set-Content -Path $Path -Encoding UTF8
    Get-Item $Path
}

function Send-VegaMail {
    <#
    .SYNOPSIS  Sendet die Mail über Microsoft Graph (Modul Microsoft.Graph.Users.Actions).
    .NOTES     Vorher: Connect-MgGraph -Scopes Mail.Send
    #>
    [CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'High')]
    param(
        [Parameter(Mandatory)][string]$From,
        [Parameter(Mandatory)][string[]]$To,
        [string[]]$Cc,
        [Parameter(Mandatory)][string]$Betreff,
        [Parameter(Mandatory)][string]$Html,
        [string]$LogoPath = (Join-Path $script:VegaRoot 'vega-logo.png'),
        [switch]$NoSaveToSentItems
    )

    $toRcpt = @($To | ForEach-Object { @{ EmailAddress = @{ Address = $_ } } })
    $ccRcpt = @($Cc | Where-Object { $_ } | ForEach-Object { @{ EmailAddress = @{ Address = $_ } } })

    $params = @{
        Message = @{
            Subject       = $Betreff
            Body          = @{ ContentType = 'HTML'; Content = $Html }
            ToRecipients  = $toRcpt
            CcRecipients  = $ccRcpt
            Attachments   = @(@{
                '@odata.type' = '#microsoft.graph.fileAttachment'
                Name          = 'vega-logo.png'
                ContentType   = 'image/png'
                ContentId     = 'vega-logo.png'
                IsInline      = $true
                ContentBytes  = [Convert]::ToBase64String([IO.File]::ReadAllBytes($LogoPath))
            })
        }
        SaveToSentItems = -not $NoSaveToSentItems
    }

    if ($PSCmdlet.ShouldProcess(($To -join ', '), "VEGA-Mail '$Betreff' senden")) {
        Send-MgUserMail -UserId $From -BodyParameter $params
    }
}
