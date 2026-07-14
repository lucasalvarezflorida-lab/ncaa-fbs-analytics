import json, os, re, urllib.request
from concurrent.futures import ThreadPoolExecutor
D = "/sessions/focused-laughing-planck/mnt/Fun Projects/Sports Data Analysis/ncaa-fbs-model/rosters/data"
raw = f"{D}/raw_official_2026"
domains = json.load(open(f"{D}/athletics_domains.json"))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def res_factory(arr):
    def res(x, depth=0):
        if depth > 16: return None
        v = arr[x] if isinstance(x, int) and 0 <= x < len(arr) else x
        if isinstance(v, dict): return {k: res(i, depth+1) for k, i in v.items()}
        if isinstance(v, list): return [res(i, depth+1) for i in v]
        return v
    return res

def fetch(item):
    school, dom = item
    fn = f"{raw}/{school.replace('/','-')}.json"
    if os.path.exists(fn) and json.load(open(fn)).get("players"):
        return None
    try:
        html = urllib.request.urlopen(urllib.request.Request(f"https://{dom}/sports/football/roster", headers=H), timeout=25).read().decode("utf-8","ignore")
        i = html.find('__NUXT_DATA__')
        if i < 0: return f"FAIL {school}: no NUXT_DATA"
        j = html.find('>', i)+1; k = html.find('</script>', j)
        arr = json.loads(html[j:k])
        res = res_factory(arr)
        players = []
        for n, v in enumerate(arr):
            if isinstance(v, dict):
                for kk in v:
                    if re.match(r'roster-\d+-players-list-page-\d+', kk):
                        d = res(v[kk]) or {}
                        for p in (d.get('players') or []):
                            pl = p.get('player') or {}
                            cl = p.get('class_level') or {}
                            pos = p.get('player_position') or {}
                            players.append({
                                "firstName": pl.get('first_name'), "lastName": pl.get('last_name'),
                                "jersey": p.get('jersey_number') or pl.get('jersey_number'),
                                "pos": pos.get('abbreviation') or pos.get('name'),
                                "class": cl.get('name'),
                                "hf": p.get('height_feet') or pl.get('height_feet'),
                                "hi": p.get('height_inches') if p.get('height_inches') is not None else pl.get('height_inches'),
                                "weight": p.get('weight') or pl.get('weight'),
                                "hometown": pl.get('hometown'),
                            })
                        break
                else:
                    continue
                break
        # dedupe by name
        seen, uniq = set(), []
        for p in players:
            key = (p["firstName"], p["lastName"])
            if key not in seen:
                seen.add(key); uniq.append(p)
        if not uniq: return f"FAIL {school}: 0 players"
        json.dump({"school": school, "title": "wmt-2026", "players": uniq, "source": "wmt"}, open(fn, "w"))
        return f"OK {school}: {len(uniq)}"
    except Exception as e:
        return f"FAIL {school}: {type(e).__name__} {e}"

todo = [(s, d) for s, d in sorted(domains.items()) if not (os.path.exists(f"{raw}/{s.replace('/','-')}.json") and json.load(open(f"{raw}/{s.replace('/','-')}.json")).get("players"))]
print("todo:", len(todo))
with ThreadPoolExecutor(max_workers=6) as ex:
    for r in ex.map(fetch, todo):
        if r: print(r)
