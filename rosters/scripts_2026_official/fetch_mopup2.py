import json, os, re, urllib.request
from concurrent.futures import ThreadPoolExecutor
D = "/sessions/focused-laughing-planck/mnt/Fun Projects/Sports Data Analysis/ncaa-fbs-model/rosters/data"
raw = f"{D}/raw_official_2026"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read().decode("utf-8","ignore")
def clean(s): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip().replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")

def parse_classic(html):
    players = []
    blocks = re.split(r'<li[^>]*class="[^"]*sidearm-roster-player[" ]', html)[1:]
    for b in blocks:
        b = b[:12000]
        def f(pat):
            m = re.search(pat, b, re.S)
            return clean(m.group(1)) if m else ""
        name = f(r'aria-label="([^"]+?) - View Full Bio"') or f(r'<h3>\s*<a[^>]*>([^<]+)</a>')
        if not name: continue
        players.append({
            "firstName": name.split(" ", 1)[0], "lastName": name.split(" ", 1)[1] if " " in name else "",
            "jersey": f(r'jersey-number">\s*([0-9]+)'),
            "pos": f(r'hide-on-medium">\s*([A-Z/\-]{1,6})\s*</span>') or f(r'player-position">\s*<span[^>]*>\s*([A-Za-z/\- ]+?)\s*<'),
            "class": f(r'academic-year hide-on-large">([^<]+)<') or f(r'academic-year">([^<]+)<'),
            "height": f(r'player-height">([^<]+)<'), "weight": f(r'player-weight">([^<]+)<'),
            "hometown": f(r'player-hometown">([^<]+)<'),
        })
    # dedupe (mobile+desktop duplication)
    seen, out = set(), []
    for p in players:
        key = (p["firstName"], p["lastName"])
        if key not in seen: seen.add(key); out.append(p)
    return out

def parse_wmt_table(html):
    out = []
    for tm in re.finditer(r'<table[^>]*id="players-table[^"]*"[^>]*>(.*?)</table>', html, re.S):
        tb = tm.group(1)
        heads = [clean(h).lower() for h in re.findall(r"<th[^>]*>(.*?)</th>", tb, re.S)]
        if not heads or "name" not in heads: continue
        idx = {h: n for n, h in enumerate(heads)}
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tb, re.S):
            tds = [clean(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(tds) < len(heads) - 2 or not tds: continue
            def g(*names):
                for nm in names:
                    if nm in idx and idx[nm] < len(tds): return tds[idx[nm]]
                return ""
            name = g("name")
            if not name: continue
            out.append({"firstName": name.split(" ", 1)[0], "lastName": name.split(" ", 1)[1] if " " in name else "",
                "jersey": g("number", "no.", "#"), "pos": g("position", "pos."),
                "height": g("height", "ht."), "weight": g("weight", "wt."),
                "class": g("class", "year", "academic year"), "hometown": g("hometown")})
        if out: break
    return out

def parse_jmu_nuxt(html):
    i = html.find("__NUXT_DATA__")
    j = html.find(">", i)+1; k = html.find("</script>", j)
    arr = json.loads(html[j:k])
    def res(x, d=0):
        if d > 18: return None
        v = arr[x] if isinstance(x, int) and 0 <= x < len(arr) else x
        if isinstance(v, dict): return {kk: res(ix, d+1) for kk, ix in v.items()}
        if isinstance(v, list): return [res(ix, d+1) for ix in v]
        return v
    # any dict with firstName+lastName+positionShort = player record
    players, seen = [], set()
    for n, v in enumerate(arr):
        if isinstance(v, dict) and "firstName" in v and "lastName" in v and ("positionShort" in v or "academicYearShort" in v):
            p = res(n)
            key = (p.get("firstName"), p.get("lastName"))
            if key in seen or not p.get("firstName"): continue
            seen.add(key)
            hf, hi = p.get("heightFeet"), p.get("heightInches")
            players.append({"firstName": p.get("firstName"), "lastName": p.get("lastName"),
                "jersey": p.get("jerseyNumber"), "pos": p.get("positionShort"),
                "class": p.get("academicYearShort") or p.get("academicYearLong"),
                "height": f"{hf}'{hi}\"" if hf else "", "weight": p.get("weight"),
                "hometown": p.get("hometown")})
    return players

JOBS = [
 ("UL Monroe", "https://ulmwarhawks.com/sports/football/roster", parse_classic),
 ("Kentucky", "https://ukathletics.com/sports/football/roster", parse_wmt_table),
 ("Miami", "https://miamihurricanes.com/sports/football/roster", parse_wmt_table),
 ("Notre Dame", "https://fightingirish.com/sports/football/roster", parse_wmt_table),
 ("South Carolina", "https://gamecocksonline.com/sports/football/roster", parse_wmt_table),
 ("Georgia Tech", "https://ramblinwreck.com/sports/football/roster", parse_wmt_table),
 ("Arkansas", "https://arkansasrazorbacks.com/sport/m-footbl/roster", parse_wmt_table),
 ("James Madison", "https://jmusports.com/sports/football/roster", parse_jmu_nuxt),
]
def run(job):
    school, url, fp = job
    fn = f"{raw}/{school}.json"
    if os.path.exists(fn) and json.load(open(fn)).get("players"): return None
    try:
        ps = fp(get(url))
        if not ps: return f"FAIL {school}: 0 players"
        json.dump({"school": school, "title": "official-2026", "players": ps, "source": "scrape"}, open(fn, "w"))
        return f"OK {school}: {len(ps)}"
    except Exception as e:
        return f"FAIL {school}: {type(e).__name__} {e}"
with ThreadPoolExecutor(max_workers=6) as ex:
    for r in ex.map(run, JOBS):
        if r: print(r)
