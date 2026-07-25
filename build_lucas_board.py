"""Freeze Lucas's per-conference podcast boards into lucas_board_2026.json
and flag disagreements vs ESPN 2026 preseason FPI.

Sources: the Big Board tables in 2026-*-deep-dive-podcast-prep.md (+ files/).
Ranks are WITHIN each board group (Sun Belt splits into EAST/WEST divisions;
both teams' FPI ranks are computed within the same group's team set, so
conference-membership edge cases can't skew the comparison).

Excluded, declared up front:
  * MAC — the board is tiers, not an ordered list; converting tiers to ranks
    would invent an order Lucas never published.
  * Independents — 2-3 teams, no meaningful within-group order.
  * CUSA + MAC boards are Athlon/CFN-shaped per the file itself — they're
    still what the podcast uses, but the provenance is recorded here.

Disagreement rule (pre-registered): |lucas_rank - fpi_rank| >= 3 spots
within the group. Lucas higher => direction "over" (paper-bet their side);
Lucas lower => "under" (paper-bet their opponents). 2026 is the FIRST
sample — there is no backtest of these boards, by construction.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name as norm

SNAP = HERE / "fpi-decomposition" / "data" / "fpi_2026_preseason_snapshot_20260714.json"
OUT = HERE / "lucas_board_2026.json"
GAP = 3  # within-group spots

# board name -> CFBD name, where norm() alone can't bridge it
ALIASES = {"SDSU": "San Diego State", "ECU": "East Carolina",
           "Hawai'i": "Hawai'i", "NDSU": "North Dakota State",
           "USF": "South Florida", "FAU": "Florida Atlantic",
           "ULM": "UL Monroe"}

BOARDS = {  # group -> (file, section line-anchor regex)
    "SEC": ("2026-sec-deep-dive-podcast-prep.md", None),
    "ACC": ("2026-acc-deep-dive-podcast-prep.md", None),
    "Big 12": ("2026-big-12-deep-dive-podcast-prep.md", None),
    "Big Ten": ("2026-big-ten-deep-dive-podcast-prep.md", None),
    "American": ("files/2026-american-deep-dive-podcast-prep.md", None),
    "Pac-12": ("2026-g6-finisher-pac12-mwc-cusa-mac-podcast-prep.md", 0),
    "Mountain West": ("2026-g6-finisher-pac12-mwc-cusa-mac-podcast-prep.md", 1),
    "CUSA": ("2026-g6-finisher-pac12-mwc-cusa-mac-podcast-prep.md", 2),
    "Sun Belt EAST": ("files/2026-sun-belt-deep-dive-podcast-prep.md", "EAST"),
    "Sun Belt WEST": ("files/2026-sun-belt-deep-dive-podcast-prep.md", "WEST"),
}
ROW = re.compile(r"^\|(?:\s*\|)?\s*(\d+)\s*\|\s*\*\*(.+?)\*+\s*\|")


def board_teams(path: Path, anchor) -> list[str]:
    text = path.read_text(encoding="utf-8")
    sections = re.split(r"^## The Big Board.*$", text, flags=re.M)[1:]
    if anchor is None:
        block = sections[0]
    elif isinstance(anchor, int):
        block = sections[anchor]
    else:  # division heading inside the (single) board section
        div = re.split(r"^\*\*(EAST|WEST)\*\*$", sections[0], flags=re.M)
        block = div[div.index(anchor) + 1]
    # stop at the next section header
    block = block.split("\n## ")[0]
    teams = []
    for line in block.splitlines():
        m = ROW.match(line)
        if m:
            name = re.sub(r"\*+", "", m.group(2)).strip()
            teams.append(ALIASES.get(name, name))
    return teams


def main():
    snap = {norm(r["team"]): r["fpi"]
            for r in json.load(open(SNAP, encoding="utf-8"))}
    out, misses = {}, []
    for group, (fname, anchor) in BOARDS.items():
        teams = board_teams(HERE / fname, anchor)
        if not teams:
            raise SystemExit(f"ERROR: no teams parsed for {group}")
        fpis = {}
        for t in teams:
            v = snap.get(norm(t))
            if v is None:
                misses.append(f"{group}: {t}")
            else:
                fpis[t] = v
        by_fpi = sorted(fpis, key=lambda t: -fpis[t])
        for i, t in enumerate(teams, 1):
            if t not in fpis:
                continue
            fr = by_fpi.index(t) + 1
            gap = fr - i          # positive: Lucas higher than FPI
            out[norm(t)] = dict(
                team=t, group=group, lucas_rank=i, fpi_group_rank=fr,
                gap=gap,
                flag=("over" if gap >= GAP else
                      "under" if gap <= -GAP else ""))
        print(f"{group}: {len(teams)} teams parsed, "
              f"{sum(1 for t in teams if t in fpis)} matched to FPI")
    meta = dict(
        frozen="2026-07-25", gap_threshold=GAP,
        excluded="MAC (tier board, no order), Independents (n<4)",
        provenance="CUSA board is Athlon-shaped per the source file",
        note="2026 is the first sample; no backtest of these boards exists")
    json.dump(dict(meta=meta, teams=out),
              open(OUT, "w", encoding="utf-8"), indent=1)
    flags = [v for v in out.values() if v["flag"]]
    print(f"\n{len(out)} teams frozen; {len(flags)} flagged (|gap| >= {GAP}):")
    for v in sorted(flags, key=lambda v: -abs(v["gap"])):
        print(f"  {v['team']:<22} {v['group']:<14} Lucas #{v['lucas_rank']:<3}"
              f" FPI #{v['fpi_group_rank']:<3} gap {v['gap']:+d}  -> {v['flag'].upper()}")
    if misses:
        print("\nUNMATCHED (fix aliases!):", misses)


if __name__ == "__main__":
    main()
