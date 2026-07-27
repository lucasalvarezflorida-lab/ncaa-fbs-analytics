"""Freeze Lucas's per-conference podcast boards into lucas_board_2026.json:
within-group ranks, disagreement flags vs ESPN preseason FPI, and TIERS.

Ranks/flags (unchanged from the 2026-07-25 freeze): |lucas_rank -
fpi_group_rank| >= 3 within the group flags a team "over"/"under" for the
LUCAS_CALL paper rule. Adding tiers must NOT change these flags.

Tiers say where Lucas's board asserts real separation vs where it's a blob.
They are derived from the numeric columns LUCAS PUT IN THE BOARDS, with the
break rules declared here (auditable, hand-editable — rerun after edits,
before week 1 only):
  * boards with an SP+ "natl rk / avg W" column: new tier when a team's
    avg W falls >= 1.0 wins below the current tier's minimum;
  * Mountain West (title-odds column): new tier when decimal odds reach
    2x the tier's best; the odds-less NDSU row joins the tier at its
    board position;
  * CUSA (Athlon national-rank column): new tier when the rank gap from
    the tier's best reaches 8;
  * MAC: Lucas's board is NATIVELY tiered ("The Cluster", "Tier 2", ...) —
    used verbatim, which brings the MAC into the sim (tiers only, no
    within-tier order, so no LUCAS_CALL flags for MAC teams).
Independents stay excluded (n<4).
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
GAP = 3          # flag threshold, within-group spots
AVGW_BREAK = 1.0  # SP+ avg-wins drop that starts a new tier
ODDS_RATIO = 2.0  # MWC: decimal-odds multiple that starts a new tier
RANK_BREAK = 8    # CUSA: Athlon natl-rank gap that starts a new tier

ALIASES = {"SDSU": "San Diego State", "ECU": "East Carolina",
           "Hawai'i": "Hawai'i", "NDSU": "North Dakota State",
           "USF": "South Florida", "FAU": "Florida Atlantic",
           "ULM": "UL Monroe", "Sacramento State": "Sacramento State"}

BOARDS = {  # group -> (file, section anchor, tier metric)
    "SEC": ("2026-sec-deep-dive-podcast-prep.md", None, "avgw"),
    "ACC": ("2026-acc-deep-dive-podcast-prep.md", None, "avgw"),
    "Big 12": ("2026-big-12-deep-dive-podcast-prep.md", None, "avgw"),
    "Big Ten": ("2026-big-ten-deep-dive-podcast-prep.md", None, "avgw"),
    "American": ("files/2026-american-deep-dive-podcast-prep.md", None, "avgw"),
    "Pac-12": ("2026-g6-finisher-pac12-mwc-cusa-mac-podcast-prep.md", 0, "avgw"),
    "Mountain West": ("2026-g6-finisher-pac12-mwc-cusa-mac-podcast-prep.md", 1, "odds"),
    "CUSA": ("2026-g6-finisher-pac12-mwc-cusa-mac-podcast-prep.md", 2, "athlon"),
    "Sun Belt EAST": ("files/2026-sun-belt-deep-dive-podcast-prep.md", "EAST", "avgw"),
    "Sun Belt WEST": ("files/2026-sun-belt-deep-dive-podcast-prep.md", "WEST", "avgw"),
}
MAC_FILE = "2026-g6-finisher-pac12-mwc-cusa-mac-podcast-prep.md"
MAC_SECTION = 3  # fourth Big Board in the G6 file, the tier table

ROW = re.compile(r"^\|(?:\s*\|)?\s*(\d+)\s*\|\s*\*\*(.+?)\*+\s*\|")


def board_rows(path: Path, anchor) -> list[tuple[str, str]]:
    """(team, full-row-text) in Lucas order."""
    text = path.read_text(encoding="utf-8")
    sections = re.split(r"^## The Big Board.*$", text, flags=re.M)[1:]
    if anchor is None:
        block = sections[0]
    elif isinstance(anchor, int):
        block = sections[anchor]
    else:
        div = re.split(r"^\*\*(EAST|WEST)\*\*$", sections[0], flags=re.M)
        block = div[div.index(anchor) + 1]
    block = block.split("\n## ")[0]
    out = []
    for line in block.splitlines():
        m = ROW.match(line)
        if m:
            name = re.sub(r"\*+", "", m.group(2)).strip()
            out.append((ALIASES.get(name, name), line))
    return out


def metric_value(row: str, kind: str):
    if kind == "avgw":
        m = re.search(r"#\d+\s*/\s*([\d.]+)", row)
        return float(m.group(1)) if m else None
    if kind == "odds":
        m = re.search(r"\+(\d+)\b(?!\d*\s*/)", row.rsplit("|", 2)[-2])
        return 1 + int(m.group(1)) / 100 if m else None  # decimal odds
    if kind == "athlon":
        cells = [c.strip() for c in row.split("|")]
        for c in cells[4:5]:
            if c.isdigit():
                return int(c)
    return None


def assign_tiers(rows: list[tuple[str, str]], kind: str) -> list[int]:
    """Tier number per row (1-based), breaks per the declared rules."""
    tiers, tier, ref = [], 1, None  # ref = tier's best/min metric
    for _, row in rows:
        v = metric_value(row, kind)
        if v is None:                # no metric: stay in current tier
            tiers.append(tier)
            continue
        if ref is None:
            ref = v
        elif ((kind == "avgw" and ref - v >= AVGW_BREAK)
              or (kind == "odds" and v >= ODDS_RATIO * ref)
              or (kind == "athlon" and v - ref >= RANK_BREAK)):
            tier += 1
            ref = v
        else:
            # avgw tiers track the tier MINIMUM; odds/athlon track the best
            if kind == "avgw":
                ref = min(ref, v)
        tiers.append(tier)
    return tiers


def mac_tiers(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8")
    block = re.split(r"^## The Big Board.*$", text, flags=re.M)[1:][MAC_SECTION]
    block = block.split("\n## ")[0]
    out, tier = {}, 0
    for line in block.splitlines():
        if not line.startswith("|") or line.startswith("| Tier |") \
                or line.startswith("|---") or line.startswith("|-"):
            continue
        cells = line.split("|")
        if len(cells) < 3 or not cells[2].strip():
            continue
        teams = re.findall(r"\*\*(.+?)\*\*", cells[2])
        if not teams:
            continue
        tier += 1
        for t in teams:
            name = re.sub(r"\*+", "", t).strip()
            out[ALIASES.get(name, name)] = tier
    return out


def main():
    snap = {norm(r["team"]): r["fpi"]
            for r in json.load(open(SNAP, encoding="utf-8"))}
    out, misses = {}, []

    for group, (fname, anchor, kind) in BOARDS.items():
        rows = board_rows(HERE / fname, anchor)
        if not rows:
            raise SystemExit(f"ERROR: no teams parsed for {group}")
        tiers = assign_tiers(rows, kind)
        fpis = {}
        for t, _ in rows:
            v = snap.get(norm(t))
            if v is None:
                misses.append(f"{group}: {t}")
            else:
                fpis[t] = v
        by_fpi = sorted(fpis, key=lambda t: -fpis[t])
        for i, ((t, _), tier) in enumerate(zip(rows, tiers), 1):
            if t not in fpis:
                continue
            fr = by_fpi.index(t) + 1
            gap = fr - i
            out[norm(t)] = dict(
                team=t, group=group, lucas_rank=i, fpi_group_rank=fr,
                gap=gap, tier=tier,
                flag=("over" if gap >= GAP else
                      "under" if gap <= -GAP else ""))
        n_tiers = max(tiers)
        print(f"{group}: {len(rows)} teams, {n_tiers} tiers "
              f"({' | '.join(','.join(t for (t, _), ti in zip(rows, tiers) if ti == k) for k in range(1, n_tiers + 1))})")

    for t, tier in mac_tiers(HERE / MAC_FILE).items():
        v = snap.get(norm(t))
        if v is None:
            misses.append(f"MAC: {t}")
            continue
        out[norm(t)] = dict(team=t, group="MAC", lucas_rank=None,
                            fpi_group_rank=None, gap=None, tier=tier,
                            flag="")
    mac_n = sum(1 for v in out.values() if v["group"] == "MAC")
    print(f"MAC: {mac_n} teams via native tiers (no order, no flags)")

    meta = dict(
        frozen="2026-07-25", gap_threshold=GAP,
        tier_rules=dict(avgw_break=AVGW_BREAK, mwc_odds_ratio=ODDS_RATIO,
                        cusa_rank_break=RANK_BREAK, mac="native tiers"),
        excluded="Independents (n<4); MAC has tiers only (no order)",
        provenance="CUSA board is Athlon-shaped per the source file",
        note="2026 is the first sample; no backtest of these boards exists")
    json.dump(dict(meta=meta, teams=out),
              open(OUT, "w", encoding="utf-8"), indent=1)
    flags = [v for v in out.values() if v["flag"]]
    print(f"\n{len(out)} teams frozen; {len(flags)} flagged (unchanged rule)")
    if misses:
        print("UNMATCHED (fix aliases!):", misses)


if __name__ == "__main__":
    main()
