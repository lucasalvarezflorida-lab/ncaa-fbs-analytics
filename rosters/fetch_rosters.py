"""Fetch 2026 FBS rosters from CollegeFootballData.com (CFBD).

Usage:
    CFBD_API_KEY=<key> python fetch_rosters.py [--year 2026]

The API key is read from the CFBD_API_KEY environment variable only.
Never hardcode it or commit it to this folder.

Output (in ./data/):
    teams_fbs_<year>.json    raw /teams/fbs response (team -> conference map)
    rosters_<year>.json      all players, each annotated with conference
    fetch_report.txt         call count, per-team player counts, anomalies

API budget: 1 call for /teams/fbs + 1 call per FBS team (~134) = ~135 calls,
well under the free tier's 1,000/month.
"""

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://apinext.collegefootballdata.com"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def api_get(path: str, key: str, **params) -> object:
    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{BASE}{path}" + (f"?{qs}" if qs else "")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--budget", type=int, default=30, help="seconds before exiting (resumable)")
    args = ap.parse_args()

    key = os.environ.get("CFBD_API_KEY")
    if not key:
        print("ERROR: CFBD_API_KEY env var not set.", file=sys.stderr)
        return 1

    os.makedirs(DATA_DIR, exist_ok=True)
    calls = 0

    teams = api_get("/teams/fbs", key, year=args.year)
    calls += 1
    with open(os.path.join(DATA_DIR, f"teams_fbs_{args.year}.json"), "w") as f:
        json.dump(teams, f, indent=1)

    conf_by_school = {t["school"]: t.get("conference") for t in teams}
    conferences = sorted({c for c in conf_by_school.values() if c})
    print(f"{len(teams)} FBS teams across {len(conferences)} conferences:")
    for c in conferences:
        n = sum(1 for v in conf_by_school.values() if v == c)
        print(f"  {c}: {n} teams")

    # Resumable: one file per team in data/raw/, skip teams already fetched.
    raw_dir = os.path.join(DATA_DIR, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    deadline = time.time() + args.budget
    for i, t in enumerate(sorted(conf_by_school), 1):
        fname = os.path.join(raw_dir, t.replace("/", "-") + ".json")
        if os.path.exists(fname):
            continue
        if time.time() > deadline:
            print("BUDGET_REACHED")
            return 0
        try:
            roster = api_get("/roster", key, year=args.year, team=t)
            calls += 1
        except Exception as e:  # noqa: BLE001 - record and continue
            print(f"[{i}] {t}: FAILED ({e})", file=sys.stderr)
            time.sleep(1)
            continue
        with open(fname, "w") as f:
            json.dump(roster, f)
        print(f"[{i}/{len(conf_by_school)}] {t}: {len(roster)}")
        time.sleep(0.15)  # be polite

    # All teams present -> merge.
    all_players, report = [], []
    missing = []
    for t in sorted(conf_by_school):
        fname = os.path.join(raw_dir, t.replace("/", "-") + ".json")
        if not os.path.exists(fname):
            missing.append(t)
            continue
        with open(fname) as f:
            roster = json.load(f)
        for p in roster:
            p["conference"] = conf_by_school[t]
        all_players.extend(roster)
        report.append(f"{t}: {len(roster)} players")
        if len(roster) < 50:
            report.append(f"  WARNING: {t} roster looks thin ({len(roster)})")
    if missing:
        print(f"MISSING ({len(missing)}): {missing}")
        return 2

    with open(os.path.join(DATA_DIR, f"rosters_{args.year}.json"), "w") as f:
        json.dump(all_players, f, indent=1)
    with open(os.path.join(DATA_DIR, "fetch_report.txt"), "w") as f:
        f.write(f"year={args.year} players={len(all_players)}\n")
        f.write("\n".join(report) + "\n")

    print(f"\nDone: {len(all_players)} players from {len(conf_by_school)} teams.")
    print("MERGED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
