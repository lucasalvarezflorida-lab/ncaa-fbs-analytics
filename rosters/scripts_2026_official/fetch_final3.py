import json, re, urllib.request
D = "/sessions/focused-laughing-planck/mnt/Fun Projects/Sports Data Analysis/ncaa-fbs-model/rosters/data"
raw = f"{D}/raw_official_2026"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read().decode("utf-8","ignore")
def clean(s): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip().replace("&#39;","'").replace("&amp;","&")

def parse_table_generic(html):
    best = []
    for tm in re.finditer(r"<table[^>]*>(.*?)</table>", html, re.S):
        tb = tm.group(1)
        heads = [clean(h).lower() for h in re.findall(r"<th[^>]*>(.*?)</th>", tb, re.S)]
        if "name" not in heads or not any(h in heads for h in ("ht.","height")): continue
        idx = {h: n for n, h in enumerate(heads)}
        rows = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tb, re.S):
            tds = [clean(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if not tds or len(tds) < 5: continue
            def g(*names):
                for nm in names:
                    if nm in idx and idx[nm] < len(tds): return tds[idx[nm]]
                return ""
            name = g("name")
            if not name: continue
            rows.append({"firstName": name.split(" ",1)[0], "lastName": name.split(" ",1)[1] if " " in name else "",
                "jersey": g("number","no.","#"), "pos": g("position","pos."),
                "height": g("ht.","height"), "weight": g("wt.","weight"),
                "class": g("year","class"), "hometown": g("hometown")})
        if len(rows) > len(best): best = rows
    return best

# Georgia Tech
ps = parse_table_generic(get("https://ramblinwreck.com/sports/m-footbl/roster/"))
print("Georgia Tech:", len(ps))
if ps: json.dump({"school":"Georgia Tech","title":"official-2026","players":ps,"source":"scrape"}, open(f"{raw}/Georgia Tech.json","w"))
# Arkansas
ps = parse_table_generic(get("https://arkansasrazorbacks.com/sport/m-footbl/roster"))
print("Arkansas:", len(ps))
if ps: json.dump({"school":"Arkansas","title":"official-2026","players":ps,"source":"scrape"}, open(f"{raw}/Arkansas.json","w"))
