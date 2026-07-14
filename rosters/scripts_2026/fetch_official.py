import json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
D = "/sessions/focused-laughing-planck/mnt/Fun Projects/Sports Data Analysis/ncaa-fbs-model/rosters/data"
raw = f"{D}/raw_official_2026"; os.makedirs(raw, exist_ok=True)
domains = json.load(open(f"{D}/athletics_domains.json"))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "application/json"}

def fetch(item):
    school, dom = item
    fn = f"{raw}/{school.replace('/','-')}.json"
    if os.path.exists(fn): return None
    url = f"https://{dom}/api/v2/Rosters/bySport/football"
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=20))
        players = d.get("players") or []
        title = d.get("displayTitle") or ""
        json.dump({"school": school, "title": title, "players": players}, open(fn, "w"))
        return f"{school}: {len(players)} ({title})"
    except Exception as e:
        return f"FAIL {school} [{dom}]: {type(e).__name__} {e}"

todo = [(s, d) for s, d in sorted(domains.items()) if not os.path.exists(f"{raw}/{s.replace('/','-')}.json")]
print(f"todo: {len(todo)}")
with ThreadPoolExecutor(max_workers=8) as ex:
    for r in ex.map(fetch, todo):
        if r: print(r)
