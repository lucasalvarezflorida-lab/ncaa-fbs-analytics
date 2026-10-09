# Append ONE outline (a short block of text) to the bottom of an existing page in the personal
# OneNote notebook "Podcast" - the sanctioned way to add to a page Lucas has hand-formatted
# (never re-push such a page; onenote_push.ps1 guards it). The page is fetched, the new
# outline is added below the lowest existing one, and the page is updated IN PLACE, so
# nothing already on it is touched.
#
#   powershell -File onenote_append.ps1 -Section "Ep7 Games" -Title "Week 6 - Texas A&M at Missouri" -Heading "The plays (shadow)" -Text "..." [-DryRun]
#
# SAFETY: same as onenote_push.ps1 - the notebook must be "Podcast" on d.docs.live.net;
# anything that looks like a work notebook stops the script.
param(
  [Parameter(Mandatory = $true)][string]$Section,
  [Parameter(Mandatory = $true)][string]$Title,
  [string]$Heading = "",
  [Parameter(Mandatory = $true)][string]$Text,
  [switch]$DryRun,
  [string]$Notebook = "Podcast"
)
$ErrorActionPreference = 'Stop'
$on = New-Object -ComObject OneNote.Application
$x = ''; $on.GetHierarchy('', 2, [ref]$x)
$doc = [xml]$x
$ns = New-Object System.Xml.XmlNamespaceManager($doc.NameTable); $ns.AddNamespace('one', $doc.DocumentElement.NamespaceURI)
$nb = $doc.SelectNodes('//one:Notebook', $ns) | Where-Object { $_.name -eq $Notebook -and $_.path -match 'd\.docs\.live\.net' }
if (-not $nb) { throw "Personal notebook '$Notebook' (d.docs.live.net) not found - refusing to touch anything else." }
if ($nb.path -match 'sharepoint|carnival') { throw "Target looks like a work notebook - stopping." }

$sx = ''; $on.GetHierarchy($nb.ID, 4, [ref]$sx); $sd = [xml]$sx
$sec = $sd.SelectNodes("//one:Section[@name='$Section']", $ns) | Where-Object { $_.ParentNode.name -ne 'OneNote_RecycleBin' } | Select-Object -First 1
if (-not $sec) { throw "Section '$Section' not found in '$Notebook'." }
$pages = @($sec.SelectNodes('one:Page', $ns))
"pages in '$Section': " + (($pages | ForEach-Object { $_.name }) -join ' | ')
$page = $pages | Where-Object { $_.name -eq $Title } | Select-Object -First 1
if (-not $page) { throw "Page '$Title' not found in '$Section'." }

$px = ''; $on.GetPageContent($page.ID, [ref]$px, 0)
$pd = [xml]$px
$pns = New-Object System.Xml.XmlNamespaceManager($pd.NameTable); $pns.AddNamespace('one', $pd.DocumentElement.NamespaceURI)
$outlines = @($pd.SelectNodes('//one:Page/one:Outline', $pns))
$bottom = 100.0; $left = 36.0; $width = 624.0
foreach ($o in $outlines) {
  $pos = $o.SelectSingleNode('one:Position', $pns); $size = $o.SelectSingleNode('one:Size', $pns)
  if ($pos -and $size) {
    $b = [double]$pos.y + [double]$size.height
    if ($b -gt $bottom) { $bottom = $b; $left = [double]$pos.x; $width = [double]$size.width }
  }
}
"page '$Title': $($outlines.Count) outlines, lowest edge at y=$bottom (last modified $($page.lastModifiedTime))"
if ($DryRun) { "dry run - nothing written"; exit 0 }

$esc = [System.Security.SecurityElement]::Escape($Text)
$body = ''
if ($Heading) { $body += '<one:OE><one:T><![CDATA[<span style="font-weight:bold">' + [System.Security.SecurityElement]::Escape($Heading) + '</span>]]></one:T></one:OE>' }
$body += '<one:OE><one:T><![CDATA[' + $esc + ']]></one:T></one:OE>'
$y = [math]::Round($bottom + 18, 1)
$frag = '<one:Outline xmlns:one="' + $pd.DocumentElement.NamespaceURI + '"><one:Position x="' + $left + '" y="' + $y + '" z="0"/><one:Size width="' + $width + '" height="40" isSetByUser="false"/><one:OEChildren>' + $body + '</one:OEChildren></one:Outline>'
$node = $pd.ImportNode(([xml]$frag).DocumentElement, $true)
[void]$pd.DocumentElement.AppendChild($node)
$on.UpdatePageContent($pd.OuterXml)
$on.SyncHierarchy($nb.ID)
"appended one outline to '$Title' (y=$y) in $Notebook / $Section"
