# Reorder pages inside a section of the personal "Podcast" notebook (Lucas 10/7/2026: "reorder the OneNote to match" the card).
#   & .\onenote_reorder.ps1 -Section "Ep7 Games" -Order "Week 6 - Indiana at Nebraska","Week 6 - Texas A&M at Missouri",...
# Pages named in -Order are placed, in that order, where the FIRST of them currently sits; every other page keeps its place.
# Nothing is edited on any page: only the section's page order changes (UpdateHierarchy on the section XML).
param(
  [Parameter(Mandatory = $true)][string]$Section,
  [Parameter(Mandatory = $true)][string[]]$Order,
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
$ns2 = New-Object System.Xml.XmlNamespaceManager($sd.NameTable); $ns2.AddNamespace('one', $sd.DocumentElement.NamespaceURI)
$sec = $sd.SelectNodes("//one:Section[@name='$Section']", $ns2) | Where-Object { $_.ParentNode.name -ne 'OneNote_RecycleBin' } | Select-Object -First 1
if (-not $sec) { throw "section '$Section' not found" }
$pages = @($sec.SelectNodes('one:Page', $ns2))
"before: " + (($pages | ForEach-Object { $_.name }) -join ' | ')
$byName = @{}; foreach ($p in $pages) { $byName[$p.name] = $p }
foreach ($t in $Order) { if (-not $byName.ContainsKey($t)) { throw "page not in section: $t" } }
$wanted = @($Order | ForEach-Object { $byName[$_] })
$others = @($pages | Where-Object { $Order -notcontains $_.name })
# insertion point = the current position of the first page in the wanted set
$firstIdx = [array]::IndexOf($pages, ($pages | Where-Object { $Order -contains $_.name } | Select-Object -First 1))
$before = @($others | Where-Object { [array]::IndexOf($pages, $_) -lt $firstIdx })
$after  = @($others | Where-Object { [array]::IndexOf($pages, $_) -ge $firstIdx })
$new = @($before + $wanted + $after)
foreach ($p in $pages) { [void]$sec.RemoveChild($p) }
foreach ($p in $new) { [void]$sec.AppendChild($p) }
$on.UpdateHierarchy($sec.OuterXml)
$cx = ''; $on.GetHierarchy($sec.ID, 4, [ref]$cx); $cd = [xml]$cx
$ns3 = New-Object System.Xml.XmlNamespaceManager($cd.NameTable); $ns3.AddNamespace('one', $cd.DocumentElement.NamespaceURI)
"after:  " + ((@($cd.SelectNodes('//one:Page', $ns3)) | ForEach-Object { $_.name }) -join ' | ')
