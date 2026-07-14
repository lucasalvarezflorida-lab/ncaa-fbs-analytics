import json, os, urllib.request
from concurrent.futures import ThreadPoolExecutor
D = "/sessions/focused-laughing-planck/mnt/Fun Projects/Sports Data Analysis/ncaa-fbs-model/rosters/data"
raw = f"{D}/raw_official_2026"
domains = json.load(open(f"{D}/athletics_domains.json"))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "application/json"}

class R308(urllib.request.HTTPRedirectHandler):
    def http_error_308(self, req, fp, code, msg, hdrs):
        return self.http_error_301(req, fp, 301, msg, hdrs)
opener = urllib.request.build_opener(R308)
def get(url): return opener.open(urllib.request.Request(url, headers=H), timeout=20)

def try_v2(dom):
    d = json.load(get(f"https://{dom}/api/v2/Rosters/bySport/football"))
    return d.get("displayTitle") or "", d.get("players") or [], "v2"
def try_apiroster(dom):
    d = json.load(get(f"https://{dom}/api/roster?sport=football"))
    r = (d.get("data") or [{}])[0]
    return r.get("roster_display_title") or "", r.get("players") or [], "apiroster"
def try_rosterxml(dom):
    d = json.load(get(f"https://{dom}/services/roster_xml.aspx?format=json&path=football"))
    return d.get("title") or "", d.get("roster") or [], "rosterxml"

def fetch(item):
    school, dom = item
    fn = f"{raw}/{school.replace('/','-')}.json"
    if os.path.exists(fn) and json.load(open(fn)).get("players"):
        return None
    for fno in (try_v2, try_apiroster, try_rosterxml):
        try:
            title, ps, src = fno(dom)
            if ps:
                json.dump({"school": school, "title": title, "players": ps, "source": src}, open(fn, "w"))
                return f"OK {school}: {len(ps)} ({title}) [{src}]"
        except Exception:
            continue
    return f"FAIL {school} [{dom}]"

with ThreadPoolExecutor(max_workers=8) as ex:
    res = [r for r in ex.map(fetch, sorted(domains.items())) if r]
ok = [r for r in res if r.startswith("OK")]
fail = [r for r in res if r.startswith("FAIL")]
print(f"newly fetched: {len(ok)}, failures: {len(fail)}")
print("\n".join(fail))
