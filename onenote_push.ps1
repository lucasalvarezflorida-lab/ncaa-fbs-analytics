# Push notes into the PERSONAL OneNote notebook "Podcast" as reading copies.
#
#   powershell -File onenote_push.ps1 -Section "Boards" -Files notes\week4_ep5_boards.md      # one page per file
#   powershell -File onenote_push.ps1 -Section "Games"  -GamesFile notes\week4_ep5_games.md   # one page PER GAME (Lucas's layout)
#   powershell -File onenote_push.ps1 -Section "Games"  -PageXml a.xml,b.xml                   # ready-made page XML (in-place edits)
#
# SAFETY: the target must be a notebook named "Podcast" whose path is on
# d.docs.live.net (personal OneDrive). Work notebooks (SharePoint / Carnival)
# are never opened, read or written - the script stops if the personal
# notebook is not found. The section is looked up by name ANYWHERE in the
# notebook (section groups included) and created at the root if missing. A
# page with the same title in that section is REPLACED (old one -> notebook
# recycle bin); page XML that already carries a real page ID is updated in
# place instead. The .md files are the master copy.
param(
  [Parameter(Mandatory = $true)][string]$Section,
  [string[]]$Files = @(),
  [string]$GamesFile = "",
  [string[]]$PageXml = @(),
  [string]$Notebook = "Podcast",
  [string]$Python = "python"
)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$on = New-Object -ComObject OneNote.Application
$x = ''; $on.GetHierarchy('', 2, [ref]$x)
$doc = [xml]$x
$ns = New-Object System.Xml.XmlNamespaceManager($doc.NameTable); $ns.AddNamespace('one', $doc.DocumentElement.NamespaceURI)
$nb = $doc.SelectNodes('//one:Notebook', $ns) | Where-Object { $_.name -eq $Notebook -and $_.path -match 'd\.docs\.live\.net' }
if (-not $nb) { throw "Personal notebook '$Notebook' (d.docs.live.net) not found - refusing to touch anything else." }
if ($nb.path -match 'sharepoint|carnival') { throw "Target looks like a work notebook - stopping." }

$sx = ''; $on.GetHierarchy($nb.ID, 4, [ref]$sx); $sd = [xml]$sx
$sec = $sd.SelectNodes("//one:Section[@name='$Section']", $ns) | Where-Object { $_.ParentNode.name -ne 'OneNote_RecycleBin' } | Select-Object -First 1
if ($sec) { $secId = $sec.ID } else { $secId = ''; $on.OpenHierarchy("$Section.one", $nb.ID, [ref]$secId, 3); "created section '$Section'" }

function Push-Page([string]$title, [string]$xmlPath) {
  $sx2 = ''; $on.GetHierarchy($secId, 4, [ref]$sx2)
  ([xml]$sx2).SelectNodes('//one:Page', $ns) | Where-Object { $_.name -eq $title } | ForEach-Object { $on.DeleteHierarchy($_.ID) }
  $pageId = ''; $on.CreateNewPage($secId, [ref]$pageId, 0)
  $page = (Get-Content $xmlPath -Raw -Encoding UTF8).Replace('{PAGE_ID}', $pageId)
  $on.UpdatePageContent($page)
  "pushed: $title  ->  $Notebook / $Section"
}

foreach ($f in $Files) {
  $src = Join-Path $here $f
  $tmp = Join-Path $env:TEMP ("onenote_" + [IO.Path]::GetFileNameWithoutExtension($f) + ".xml")
  $title = (& $Python (Join-Path $here 'md_to_onenote.py') $src $tmp | Select-Object -Last 1).Trim()
  Push-Page $title $tmp
}
if ($GamesFile) {
  $outdir = Join-Path $env:TEMP 'onenote_games'
  $lines = & $Python (Join-Path $here 'md_to_onenote.py') --games (Join-Path $here $GamesFile) $outdir
  foreach ($ln in $lines) { $t, $p = $ln -split "`t", 2; Push-Page $t.Trim() $p.Trim() }
}
foreach ($p in $PageXml) {
  $page = Get-Content $p -Raw -Encoding UTF8
  if ($page -match 'ID="\{[0-9A-F-]+\}\{') { $on.UpdatePageContent($page); "updated in place: $p" }
  else { throw "$p has no real page ID - use -Files / -GamesFile for new pages" }
}
$on.SyncHierarchy($nb.ID)
