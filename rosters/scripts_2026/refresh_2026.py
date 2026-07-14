"""Full 2026 roster re-pull (Windows/local port of the June fetch scripts).

Combines fetch_fb2 (v2/apiroster/rosterxml APIs), fetch_wmt (NUXT scrape),
and fetch_mopup2 (site-specific parsers). Archives the previous raw pull to
raw_official_2026_asof0610/ and fetches everything fresh; any school whose
site fails today falls back to its archived June file with the title marked
so the Coverage sheet shows it.

Also refreshes data/portal_2026.json from CFBD (reads CFBD_API_KEY from the
environment; never printed or logged).
"""

import json
import os
import re
import shutil
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import certifi

HERE = Path(__file__).resolve().parents[1]  # rosters/
D = HERE / "data"
RAW = D / "raw_official_2026"
ARCHIVE = D / "raw_official_2026_asof0610"

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
     "Accept": "application/json"}


class R308(urllib.request.HTTPRedirectHandler):
    def http_error_308(self, req, fp, code, msg, hdrs):
        return self.http_error_301(req, fp, 301, msg, hdrs)


# Python's urllib on Windows misses many sites' CA chains - use certifi's bundle.
CTX = ssl.create_default_context(cafile=certifi.where())
opener = urllib.request.build_opener(R308, urllib.request.HTTPSHandler(context=CTX))


def get(url, timeout=25):
    return opener.open(urllib.request.Request(url, headers=H), timeout=timeout)


def get_text(url, timeout=30):
    return get(url, timeout).read().decode("utf-8", "ignore")


def fname(school):
    return RAW / f"{school.replace('/', '-')}.json"


def has_players(path):
    try:
        return bool(json.load(open(path, encoding="utf-8")).get("players"))
    except Exception:
        return False


# ---------- stage 0: portal refresh ----------

def refresh_portal():
    key = os.environ.get("CFBD_API_KEY")
    if not key:
        print("WARN: CFBD_API_KEY not set - keeping existing portal_2026.json")
        return
    req = urllib.request.Request(
        "https://api.collegefootballdata.com/player/portal?year=2026",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req, timeout=30, context=CTX))
    if not data:
        print("WARN: CFBD portal feed returned 0 rows - keeping existing file")
        return
    dst = D / "portal_2026.json"
    if not (D / "portal_2026_asof0610.json").exists():
        shutil.copy2(dst, D / "portal_2026_asof0610.json")
    json.dump(data, open(dst, "w", encoding="utf-8"))
    print(f"portal_2026.json refreshed: {len(data)} entries (old file archived)")


# ---------- stage 1: official-site APIs (v2 / apiroster / rosterxml) ----------

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


def fetch_api(item):
    school, dom = item
    fn = fname(school)
    if fn.exists() and has_players(fn):
        return None
    for fno in (try_v2, try_apiroster, try_rosterxml):
        try:
            title, ps, src = fno(dom)
            if ps:
                json.dump({"school": school, "title": title, "players": ps,
                           "source": src}, open(fn, "w", encoding="utf-8"))
                return f"OK {school}: {len(ps)} ({title}) [{src}]"
        except Exception:
            continue
    return f"MISS {school} [{dom}]"


# ---------- stage 2: WMT NUXT sites ----------

def res_factory(arr):
    def res(x, depth=0):
        if depth > 16:
            return None
        v = arr[x] if isinstance(x, int) and 0 <= x < len(arr) else x
        if isinstance(v, dict):
            return {k: res(i, depth + 1) for k, i in v.items()}
        if isinstance(v, list):
            return [res(i, depth + 1) for i in v]
        return v
    return res


def fetch_wmt(item):
    school, dom = item
    fn = fname(school)
    if fn.exists() and has_players(fn):
        return None
    try:
        html = get_text(f"https://{dom}/sports/football/roster")
        i = html.find("__NUXT_DATA__")
        if i < 0:
            return f"MISS {school}: no NUXT_DATA"
        j = html.find(">", i) + 1
        k = html.find("</script>", j)
        arr = json.loads(html[j:k])
        res = res_factory(arr)
        players = []
        for v in arr:
            if isinstance(v, dict):
                for kk in v:
                    if re.match(r"roster-\d+-players-list-page-\d+", kk):
                        d = res(v[kk]) or {}
                        for p in d.get("players") or []:
                            pl = p.get("player") or {}
                            cl = p.get("class_level") or {}
                            pos = p.get("player_position") or {}
                            players.append({
                                "firstName": pl.get("first_name"),
                                "lastName": pl.get("last_name"),
                                "jersey": p.get("jersey_number") or pl.get("jersey_number"),
                                "pos": pos.get("abbreviation") or pos.get("name"),
                                "class": cl.get("name"),
                                "hf": p.get("height_feet") or pl.get("height_feet"),
                                "hi": p.get("height_inches") if p.get("height_inches") is not None else pl.get("height_inches"),
                                "weight": p.get("weight") or pl.get("weight"),
                                "hometown": pl.get("hometown"),
                            })
                        break
                else:
                    continue
                break
        seen, uniq = set(), []
        for p in players:
            key = (p["firstName"], p["lastName"])
            if key not in seen:
                seen.add(key)
                uniq.append(p)
        if not uniq:
            return f"MISS {school}: 0 players"
        json.dump({"school": school, "title": "wmt-2026", "players": uniq,
                   "source": "wmt"}, open(fn, "w", encoding="utf-8"))
        return f"OK {school}: {len(uniq)} [wmt]"
    except Exception as e:
        return f"MISS {school}: {type(e).__name__}"


# ---------- stage 3: site-specific parsers ----------

def clean(s):
    s = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()
    return s.replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")


def parse_classic(html):
    players = []
    blocks = re.split(r'<li[^>]*class="[^"]*sidearm-roster-player[" ]', html)[1:]
    for b in blocks:
        b = b[:12000]

        def f(pat):
            m = re.search(pat, b, re.S)
            return clean(m.group(1)) if m else ""

        name = f(r'aria-label="([^"]+?) - View Full Bio"') or f(r"<h3>\s*<a[^>]*>([^<]+)</a>")
        if not name:
            continue
        players.append({
            "firstName": name.split(" ", 1)[0],
            "lastName": name.split(" ", 1)[1] if " " in name else "",
            "jersey": f(r'jersey-number">\s*([0-9]+)'),
            "pos": f(r'hide-on-medium">\s*([A-Z/\-]{1,6})\s*</span>') or f(r'player-position">\s*<span[^>]*>\s*([A-Za-z/\- ]+?)\s*<'),
            "class": f(r'academic-year hide-on-large">([^<]+)<') or f(r'academic-year">([^<]+)<'),
            "height": f(r'player-height">([^<]+)<'),
            "weight": f(r'player-weight">([^<]+)<'),
            "hometown": f(r'player-hometown">([^<]+)<'),
        })
    seen, out = set(), []
    for p in players:
        key = (p["firstName"], p["lastName"])
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def parse_wmt_table(html):
    out = []
    for tm in re.finditer(r'<table[^>]*id="players-table[^"]*"[^>]*>(.*?)</table>', html, re.S):
        tb = tm.group(1)
        heads = [clean(h).lower() for h in re.findall(r"<th[^>]*>(.*?)</th>", tb, re.S)]
        if not heads or "name" not in heads:
            continue
        idx = {h: n for n, h in enumerate(heads)}
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tb, re.S):
            tds = [clean(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(tds) < len(heads) - 2 or not tds:
                continue

            def g(*names):
                for nm in names:
                    if nm in idx and idx[nm] < len(tds):
                        return tds[idx[nm]]
                return ""

            name = g("name")
            if not name:
                continue
            out.append({"firstName": name.split(" ", 1)[0],
                        "lastName": name.split(" ", 1)[1] if " " in name else "",
                        "jersey": g("number", "no.", "#"), "pos": g("position", "pos."),
                        "height": g("height", "ht."), "weight": g("weight", "wt."),
                        "class": g("class", "year", "academic year"),
                        "hometown": g("hometown")})
        if out:
            break
    return out


def parse_table_generic(html):
    best = []
    for tm in re.finditer(r"<table[^>]*>(.*?)</table>", html, re.S):
        tb = tm.group(1)
        heads = [clean(h).lower() for h in re.findall(r"<th[^>]*>(.*?)</th>", tb, re.S)]
        if "name" not in heads or not any(h in heads for h in ("ht.", "ht", "height")):
            continue
        idx = {h: n for n, h in enumerate(heads)}
        rows = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tb, re.S):
            tds = [clean(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if not tds or len(tds) < 5:
                continue

            def g(*names):
                for nm in names:
                    if nm in idx and idx[nm] < len(tds):
                        return tds[idx[nm]]
                return ""

            name = g("name")
            if not name:
                continue
            rows.append({"firstName": name.split(" ", 1)[0],
                         "lastName": name.split(" ", 1)[1] if " " in name else "",
                         "jersey": g("number", "no.", "no", "num", "#"),
                         "pos": g("position", "pos.", "pos"),
                         "height": g("ht.", "ht", "height"),
                         "weight": g("wt.", "wt", "weight"),
                         "class": g("year", "class", "yr"), "hometown": g("hometown")})
        if len(rows) > len(best):
            best = rows
    return best


def parse_jmu_nuxt(html):
    i = html.find("__NUXT_DATA__")
    j = html.find(">", i) + 1
    k = html.find("</script>", j)
    arr = json.loads(html[j:k])
    res = res_factory(arr)
    players, seen = [], set()
    for n, v in enumerate(arr):
        if isinstance(v, dict) and "firstName" in v and "lastName" in v and (
                "positionShort" in v or "academicYearShort" in v):
            p = res(n)
            key = (p.get("firstName"), p.get("lastName"))
            if key in seen or not p.get("firstName"):
                continue
            seen.add(key)
            hf, hi = p.get("heightFeet"), p.get("heightInches")
            players.append({"firstName": p.get("firstName"), "lastName": p.get("lastName"),
                            "jersey": p.get("jerseyNumber"), "pos": p.get("positionShort"),
                            "class": p.get("academicYearShort") or p.get("academicYearLong"),
                            "height": f"{hf}'{hi}\"" if hf else "", "weight": p.get("weight"),
                            "hometown": p.get("hometown")})
    return players


SPECIALTY = [
    ("UL Monroe", "https://ulmwarhawks.com/sports/football/roster", parse_classic),
    ("Kentucky", "https://ukathletics.com/sports/football/roster", parse_wmt_table),
    ("Miami", "https://miamihurricanes.com/sports/football/roster", parse_wmt_table),
    ("Notre Dame", "https://fightingirish.com/sports/football/roster", parse_wmt_table),
    ("South Carolina", "https://gamecocksonline.com/sports/football/roster", parse_wmt_table),
    ("Georgia Tech", "https://ramblinwreck.com/sports/football/roster", parse_wmt_table),
    ("Georgia Tech", "https://ramblinwreck.com/sports/m-footbl/roster/", parse_table_generic),
    ("Arkansas", "https://arkansasrazorbacks.com/sport/m-footbl/roster", parse_wmt_table),
    ("Arkansas", "https://arkansasrazorbacks.com/sport/m-footbl/roster/", parse_table_generic),
    ("James Madison", "https://jmusports.com/sports/football/roster", parse_jmu_nuxt),
    ("Kennesaw State", "https://ksuowls.com/sports/football/roster", parse_classic),
    ("Georgia State", "https://georgiastatesports.com/sports/football/roster", parse_classic),
]


def fetch_specialty(job):
    school, url, fp = job
    fn = fname(school)
    if fn.exists() and has_players(fn):
        return None
    try:
        ps = fp(get_text(url))
        if not ps:
            return f"MISS {school}: 0 players"
        json.dump({"school": school, "title": "official-2026", "players": ps,
                   "source": "scrape"}, open(fn, "w", encoding="utf-8"))
        return f"OK {school}: {len(ps)} [scrape]"
    except Exception as e:
        return f"MISS {school}: {type(e).__name__}"


# ---------- main ----------

def main():
    refresh_portal()

    if RAW.exists() and not ARCHIVE.exists():
        RAW.rename(ARCHIVE)
        print(f"archived June pull -> {ARCHIVE.name}")
    RAW.mkdir(exist_ok=True)

    # drop stale-fallback files from a previous refresh attempt so they re-fetch
    dropped = 0
    for fn in RAW.glob("*.json"):
        try:
            if "[STALE:" in (json.load(open(fn, encoding="utf-8")).get("title") or ""):
                fn.unlink()
                dropped += 1
        except Exception:
            pass
    if dropped:
        print(f"removed {dropped} stale fallback files for re-fetch")

    domains = json.load(open(D / "athletics_domains.json", encoding="utf-8"))

    print("\n-- stage 1: official-site APIs --")
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = [r for r in ex.map(fetch_api, sorted(domains.items())) if r]
    miss = [r for r in results if r.startswith("MISS")]
    print(f"fetched: {len(results) - len(miss)}, missing: {len(miss)}")

    print("\n-- stage 2: WMT NUXT sites --")
    todo = [(s, d) for s, d in sorted(domains.items()) if not (fname(s).exists() and has_players(fname(s)))]
    with ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(fetch_wmt, todo):
            if r and r.startswith("OK"):
                print(r)

    print("\n-- stage 3: site-specific parsers --")
    with ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(fetch_specialty, SPECIALTY):
            if r:
                print(r)

    print("\n-- stage 4: archive fallback for anything still missing --")
    still = [s for s in domains if not (fname(s).exists() and has_players(fname(s)))]
    for s in still:
        old = ARCHIVE / f"{s.replace('/', '-')}.json"
        if old.exists() and has_players(old):
            d = json.load(open(old, encoding="utf-8"))
            d["title"] = (d.get("title") or "") + " [STALE: June 10 pull, site unavailable on refresh]"
            json.dump(d, open(fname(s), "w", encoding="utf-8"))
            print(f"FALLBACK {s}: using archived June roster")
        else:
            print(f"NO DATA {s}: no fresh pull and no archive (build will use 2025 base + portal)")

    fresh = sum(1 for s in domains if fname(s).exists() and has_players(fname(s))
                and "STALE" not in (json.load(open(fname(s), encoding="utf-8")).get("title") or ""))
    print(f"\ndone: {fresh}/{len(domains)} schools with a fresh pull")


if __name__ == "__main__":
    main()
