"""seat_data.py - the data file behind "The Seat and the Trophy" (seat/index.html): the hot seat board and
the Heisman boards with their week-by-week history.

Built from the saved weekly boards (boards_weekN.json, written by hot_seat_heisman.py every Sunday):
  * hot_seat      coach, team, composite score (40% six-list human prior + 60% P(gone) model since the
                  10/4 rule; weeks 2-5 files carry the old CBS-based rule), record, projected wins and the
                  10th / 90th percentile, bowl chance, buyout, the machine's rank / rating / delta, results
  * heisman_all   the slide board: points added per game x team factor, all positions (weeks 5+)
  * heisman       the QB efficiency index (every week)
  * heisman_non_qb  the receiver / back watch
  * logos and colours from tape_data_2026.json

EVERY MARKET FIELD IS STRIPPED (DraftKings prices, the upset board with its lines) - the page is a
presentable thing. Nothing here changes a board.

    python seat_data.py            # -> seat_data_2026.json
    python seat.py                 # -> seat/index.html (template + data)
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

OUT = HERE / "seat_data_2026.json"
RULE_WEEK = 6          # first boards file under the 10/4 hot-seat rule (40% human / 60% P(gone))
MARKET_KEYS = {"market", "market_p", "upset_board", "market_date"}


def strip(d: dict) -> dict:
    return {k: v for k, v in d.items() if k not in MARKET_KEYS}


def build() -> dict:
    files = sorted(glob.glob(str(HERE / "boards_week*.json")), key=lambda p: int(p.rsplit("week", 1)[1].split(".")[0]))
    weeks = []
    boards = {}
    for f in files:
        b = json.loads(Path(f).read_text(encoding="utf-8"))
        w = int(b["week"])
        weeks.append(w)
        boards[w] = b
    latest = boards[weeks[-1]]
    tape = json.loads((HERE / "tape_data_2026.json").read_text(encoding="utf-8"))["teams"] if (HERE / "tape_data_2026.json").exists() else {}

    def team_bits(team: str) -> dict:
        t = tape.get(normalize_name(team), {})
        return dict(color=t.get("color"), logo=t.get("logo"), abbr=t.get("abbr"))

    # hot seat: latest board + history of score and rank by week
    hist_score: dict[str, dict] = {}
    for w in weeks:
        rows = sorted(boards[w]["hot_seat"], key=lambda r: -r["score"])
        for i, r in enumerate(rows, 1):
            hist_score.setdefault(r["coach"], {})[w] = dict(score=r["score"], rank=i)
    hot = []
    for i, r in enumerate(sorted(latest["hot_seat"], key=lambda r: -r["score"]), 1):
        h = hist_score.get(r["coach"], {})
        hot.append(dict(strip(r), rank=i, prev_rank=(h.get(weeks[-2], {}).get("rank") if len(weeks) > 1 else None),
                        prev_score=(h.get(weeks[-2], {}).get("score") if len(weeks) > 1 else None),
                        hist=[h.get(w, {}).get("score") for w in weeks], hist_rank=[h.get(w, {}).get("rank") for w in weeks],
                        **team_bits(r["team"])))

    # heisman all positions (weeks 5+): history of index and rank
    hw = [w for w in weeks if boards[w].get("heisman_all")]
    hist_all: dict[str, dict] = {}
    for w in hw:
        rows = sorted(boards[w]["heisman_all"], key=lambda r: -r["index"])
        for i, r in enumerate(rows, 1):
            hist_all.setdefault(r["name"], {})[w] = dict(index=r["index"], rank=i)
    allpos = []
    for i, r in enumerate(sorted(latest.get("heisman_all", []), key=lambda r: -r["index"]), 1):
        h = hist_all.get(r["name"], {})
        allpos.append(dict(strip(r), rank=i, prev_rank=(h.get(hw[-2], {}).get("rank") if len(hw) > 1 else None),
                           hist=[h.get(w, {}).get("index") for w in hw], **team_bits(r["team"])))

    # QB index (every week)
    hist_qb: dict[str, dict] = {}
    for w in weeks:
        rows = sorted(boards[w]["heisman"], key=lambda r: -r["index"])
        for i, r in enumerate(rows, 1):
            hist_qb.setdefault(r["name"], {})[w] = dict(index=r["index"], rank=i)
    qb = []
    for i, r in enumerate(sorted(latest["heisman"], key=lambda r: -r["index"]), 1):
        h = hist_qb.get(r["name"], {})
        qb.append(dict(strip(r), rank=i, prev_rank=(h.get(weeks[-2], {}).get("rank") if len(weeks) > 1 else None),
                       hist=[h.get(w, {}).get("index") for w in weeks], **team_bits(r["team"])))
    nonqb = [dict(strip(r), **team_bits(r["team"])) for r in latest.get("heisman_non_qb", [])]

    out = dict(as_of=dt.datetime.now().isoformat(timespec="minutes"), season=2026, week=weeks[-1], weeks=weeks, heisman_weeks=hw,
               rule_week=RULE_WEEK, generated=latest.get("generated"), games_used=latest.get("games_used"),
               hot_seat=hot, heisman_all=allpos, heisman_qb=qb, heisman_non_qb=nonqb)
    txt = json.dumps(out, separators=(",", ":"), ensure_ascii=False)
    assert "market" not in txt.lower() or '"market' not in txt, "market field leaked"
    OUT.write_text(txt, encoding="utf-8")
    return out


if __name__ == "__main__":
    d = build()
    print(f"wrote {OUT.name}: week {d['week']} (boards weeks {d['weeks']}), {len(d['hot_seat'])} coaches, {len(d['heisman_all'])} on the all-positions board, {len(d['heisman_qb'])} QBs")
    for r in d["hot_seat"][:5]:
        print(f"  seat {r['rank']:2d} {r['coach']:18s} {r['team']:16s} {r['score']:5.1f}  hist {r['hist']}")
    for r in d["heisman_all"][:5]:
        print(f"  heis {r['rank']:2d} {r['name']:18s} {r['team']:16s} {r['index']:5.1f}  hist {r['hist']}")
