# -*- coding: utf-8 -*-
"""Capture OurLads NCAAF depth charts (server-rendered HTML) into a LOCAL
data file for the workbook. One polite pass, throttled; data stays
gitignored — OurLads' curated charts are their product."""

import json
import re
import sys
import time
import datetime

import requests

sys.path.insert(0, r"C:\Users\lucas\Fun Projects\Sports Data Analysis\ncaa-fbs-model\fpi-decomposition")
from name_mapping import normalize_name as norm

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
BASE = "https://www.ourlads.com/ncaa-football-depth-charts/"

idx = requests.get(BASE, headers=H, timeout=30).text
# slug may contain a literal space (OurLads quirk: "s=utah state" July 2026)
links = sorted(set(re.findall(r'depth-chart\.aspx\?s=([a-z0-9 -]+?)&(?:amp;)?id=(\d+)', idx)))
print("team pages:", len(links))

# map slugs to our workbook team names
import openpyxl
wb = openpyxl.load_workbook(r"C:\Users\lucas\Fun Projects\Sports Data Analysis\ncaa-fbs-model\NCAA_FBS_Teams.xlsm", read_only=True, data_only=True)
ours = {norm(r[0]): r[0] for r in wb["_Teams"].iter_rows(min_row=2, values_only=True) if r[0]}
wb.close()
SLUG_FIX = {"appalacian-state": "App State", "wku": "Western Kentucky",
            "miami-fl": "Miami", "miami-oh": "Miami (OH)", "ole-miss": "Ole Miss",
            "texas-am": "Texas A&M", "hawaii": "Hawai'i", "uconn": "UConn",
            "connecticut": "UConn", "san-jose-state": "San José State",
            "ul-monroe": "UL Monroe", "louisiana-monroe": "UL Monroe",
            "southern-mississippi": "Southern Miss", "massachusetts": "Massachusetts",
            "central-florida": "UCF", "ucf": "UCF", "smu": "SMU", "usc": "USC",
            "lsu": "LSU", "tcu": "TCU", "byu": "BYU", "utep": "UTEP", "utsa": "UTSA",
            "uab": "UAB", "unlv": "UNLV", "fiu": "Florida International",
            "florida-intl": "Florida International", "nc-state": "NC State",
            "north-carolina-state": "NC State", "brigham-young": "BYU",
            "florida-international": "Florida International",
            "miami-university": "Miami (OH)"}

def slug_to_team(slug):
    if slug in SLUG_FIX:
        return SLUG_FIX[slug]
    return ours.get(norm(slug.replace("-", " ")))

unmapped = [s for s, _ in links if not slug_to_team(s)]
print("unmapped slugs:", unmapped)

CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
TAG = re.compile(r"<[^>]+>")
ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)

def clean(s):
    s = TAG.sub("", s or "")
    return re.sub(r"\s+", " ", s).replace("&amp;", "&").replace("&#39;", "'").strip()

def parse_page(html):
    m = re.search(r"Updated:\s*</?[^>]*>?\s*([\d/apmAPM: ]+)", html) or \
        re.search(r"Updated:\s*([\d/]+)", clean(html))
    updated = m.group(1).strip() if m else ""
    # section scheme labels e.g. "Offense Spread Option", "Defense 4-2-5"
    text = clean(html)
    off_m = re.search(r"OFFENSE\s+([A-Z0-9 &\-']{3,30}?)\s+Pos", text, re.I)
    def_m = re.search(r"DEFENSE\s+([A-Z0-9\- ]{3,20}?)\s+Pos", text, re.I)
    tbodies = re.findall(r"<tbody[^>]*>(.*?)</tbody>", html, re.S)
    if not tbodies:
        return None
    rows = []
    for tr in ROW.findall("".join(tbodies)):
        tds = [clean(td) for td in CELL.findall(tr)]
        if not tds or not tds[0]:
            continue
        pos = tds[0]
        players = []
        for j in range(2, len(tds), 2):
            if j < len(tds) and tds[j]:
                players.append(tds[j])
        if players:
            rows.append({"pos": pos, "players": players[:4]})
    return {"updated": updated,
            "off_scheme": off_m.group(1).title().strip() if off_m else "",
            "def_scheme": def_m.group(1).strip() if def_m else "",
            "rows": rows}

out, failed = {}, []
for slug, tid in links:
    team = slug_to_team(slug)
    if not team:
        continue
    try:
        html = requests.get(f"{BASE}depth-chart.aspx?s={requests.utils.quote(slug)}&id={tid}",
                            headers=H, timeout=30).text
        parsed = parse_page(html)
        if parsed and len(parsed["rows"]) >= 20:
            out[team] = parsed
        else:
            failed.append(f"{team} ({len(parsed['rows']) if parsed else 'no tbody'} rows)")
    except Exception as e:
        failed.append(f"{team}: {type(e).__name__}")
    time.sleep(0.7)

path = r"C:\Users\lucas\Fun Projects\Sports Data Analysis\ncaa-fbs-model\ourlads_depth.json"
json.dump({"captured": f"{datetime.date.today():%Y-%m-%d}",
           "source": "OurLads.com NCAAF depth charts (personal use; not for redistribution)",
           "teams": out}, open(path, "w", encoding="utf-8"), indent=0, ensure_ascii=False)
print(f"captured {len(out)} teams -> ourlads_depth.json")
print("failed/skipped:", failed[:12])
o = out.get("Ohio State", {})
print("OSU:", o.get("updated"), "|", o.get("off_scheme"), "|", o.get("def_scheme"),
      "| rows:", len(o.get("rows", [])))
print("OSU QB row:", next((r for r in o.get("rows", []) if r["pos"] == "QB"), None))
