"""Append-only market-line history, CLV and edge-decay flags (review item A).

Every REAL CFBD /lines pull (refresh_all's Tuesday task, `edge_report
--refresh`, `edge_report --publish`) calls `record()`, which appends to
lines_history.jsonl:

  {"kind": "pull", "ts": ..., "games": N}                       one per pull
  {"kind": "line", "ts", "game_id", "wk", "home", "away", "book",
   "spread", "spread_open", "ou", "home_ml", "away_ml"}          one per game
                                                                  per book, only
                                                                  when something
                                                                  changed since
                                                                  that book's
                                                                  last row

So the file stays small (a row is a change, not a poll) while `pulls` keeps the
honest "lines as of" timestamp. Nothing is ever rewritten.

Per game, `series()` collapses the books into one consensus line per pull
using the same DraftKings > Bovada > ESPN Bet preference as
build_conference_book.fetch_lines, so first-seen / current are comparable to
what the workbook shows. `assess()` turns first-seen + current + the model
margin into CLV (signed to the model's side, same formula the Upset Board
uses) and flags:

  EDGE_GONE   stated edge (>= EDGE_MIN at first sight) decayed below EDGE_DECAY
  EDGE_FLIP   the model's side changed between first sight and now
  CLV+ / CLV- line moved >= CLV_MOVE toward / against the model's side

Seeding (one-time, `seed_from_cache` / `seed_from_alerts_log`) backfills the
pre-ledger history so Week 0's first-seen is Aug 18 (the cached pull) and
alert games keep their July first-seen dates.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "lines_history.jsonl"

BOOK_PREF = ["DraftKings", "Bovada", "ESPN Bet"]
EDGE_MIN = 3.0     # first-seen |edge| that counts as a stated edge
EDGE_DECAY = 1.5   # current |edge| below this => EDGE_GONE
CLV_MOVE = 2.0     # |clv| >= this => CLV+ / CLV-

LINE_FIELDS = ("spread", "spread_open", "ou", "home_ml", "away_ml")


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _rows():
    if not LEDGER.exists():
        return
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def _append(rows: list[dict]) -> None:
    with open(LEDGER, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _last_by_book() -> dict[tuple, dict]:
    last = {}
    for r in _rows():
        if r.get("kind") == "line":
            last[(str(r["game_id"]), r["book"])] = r
    return last


def record(raw_records: list[dict], ts: str | None = None,
           source: str = "cfbd") -> tuple[int, int]:
    """Append a pull marker plus one row per (game, book) whose line changed.
    `raw_records` is the CFBD /lines payload. Returns (games, rows_written)."""
    ts = ts or _now()
    last = _last_by_book()
    rows, games = [], 0
    for g in raw_records:
        lines = g.get("lines") or []
        if not lines:
            continue
        games += 1
        gid = str(g.get("id"))
        for ln in lines:
            book = ln.get("provider") or "?"
            row = dict(kind="line", ts=ts, game_id=gid, wk=g.get("week"),
                       home=g.get("homeTeam"), away=g.get("awayTeam"),
                       book=book, spread=ln.get("spread"),
                       spread_open=ln.get("spreadOpen"), ou=ln.get("overUnder"),
                       home_ml=ln.get("homeMoneyline"),
                       away_ml=ln.get("awayMoneyline"), source=source)
            prev = last.get((gid, book))
            if prev and all(prev.get(k) == row.get(k) for k in LINE_FIELDS):
                continue
            rows.append(row)
            last[(gid, book)] = row
    _append([dict(kind="pull", ts=ts, games=games, rows=len(rows),
                  source=source)] + rows)
    return games, len(rows)


def pulls() -> list[dict]:
    return [r for r in _rows() if r.get("kind") == "pull"]


def history(game_id) -> list[dict]:
    gid = str(game_id)
    return [r for r in _rows() if r.get("kind") == "line" and r["game_id"] == gid]


def series(game_id) -> list[dict]:
    """Consensus line per pull: for each pull ts, the latest row per book up to
    that ts, merged per field by BOOK_PREF (same rule as fetch_lines)."""
    hist = history(game_id)
    if not hist:
        return []
    ts_list = sorted({r["ts"] for r in hist})
    out, state = [], {}
    for ts in ts_list:
        for r in hist:
            if r["ts"] == ts:
                state[r["book"]] = r
        ranked = sorted(state.values(), key=lambda r: (
            BOOK_PREF.index(r["book"]) if r["book"] in BOOK_PREF else 99))
        merged = dict(ts=ts)
        for k in LINE_FIELDS:
            src = next((r for r in ranked if r.get(k) is not None), None)
            merged[k] = src.get(k) if src else None
            merged[k + "_book"] = src["book"] if src else None
        merged["books"] = {r["book"]: {k: r.get(k) for k in LINE_FIELDS}
                           for r in ranked}
        out.append(merged)
    return out


def assess(game_id, model_margin: float | None, home: str, away: str) -> dict:
    """first-seen vs current line, CLV signed to the model's side, flags."""
    s = series(game_id)
    pts = [p for p in s if p.get("spread") is not None]
    if not pts:
        return dict(first_ts=None, first_spread=None, now_ts=None,
                    now_spread=None, opener=None, clv=None, first_edge=None,
                    now_edge=None, flags=[], n_pulls=0)
    first, now = pts[0], pts[-1]
    opener = next((p["spread_open"] for p in pts if p.get("spread_open")
                   is not None), None)
    out = dict(first_ts=first["ts"], first_spread=float(first["spread"]),
               now_ts=now["ts"], now_spread=float(now["spread"]),
               opener=(float(opener) if opener is not None else None),
               clv=None, first_edge=None, now_edge=None, flags=[],
               n_pulls=len(pts), spread_book=now.get("spread_book"),
               ml_book=now.get("home_ml_book"))
    if model_margin is None:
        return out
    # edge from the home perspective: model margin minus market margin
    first_edge = round(model_margin + out["first_spread"], 1)
    now_edge = round(model_margin + out["now_spread"], 1)
    model_side = home if first_edge > 0 else away
    moved = out["first_spread"] - out["now_spread"]
    clv = round(moved if model_side == home else -moved, 1)
    flags = []
    if first_edge * now_edge < 0 and abs(first_edge) >= EDGE_MIN:
        flags.append("EDGE_FLIP")
    elif abs(first_edge) >= EDGE_MIN and abs(now_edge) < EDGE_DECAY:
        flags.append("EDGE_GONE")
    if clv >= CLV_MOVE:
        flags.append(f"CLV+{clv:g}")
    elif clv <= -CLV_MOVE:
        flags.append(f"CLV{clv:g}")
    out.update(first_edge=first_edge, now_edge=now_edge, clv=clv,
               model_side=model_side, flags=flags)
    return out


# ---------------- one-time seeding of pre-ledger history ----------------

def seed_from_alerts_log(path: Path) -> int:
    """Alert games' first-seen spreads (RED/YEL only, book unknown) as the
    earliest points. Idempotent: skipped if the ledger already has any
    'alerts_log'-sourced rows."""
    if any(r.get("source") == "alerts_log" for r in _rows()):
        return 0
    if not path.exists():
        return 0
    log = json.load(open(path, encoding="utf-8"))
    by_ts: dict[str, list[dict]] = {}
    for gid, e in log.items():
        if e.get("spread") is None:
            continue
        ts = f"{e['first_seen']}T12:00:00+00:00"
        by_ts.setdefault(ts, []).append(dict(
            id=gid, week=e.get("wk"), homeTeam=e.get("home"),
            awayTeam=e.get("away"),
            lines=[dict(provider="alerts_log", spread=e["spread"])]))
    n = 0
    for ts in sorted(by_ts):
        n += record(by_ts[ts], ts=ts, source="alerts_log")[1]
    return n


def seed_from_cache(cache_path: Path) -> int:
    """The on-disk CFBD /lines cache as it stands BEFORE the next refresh,
    stamped with the file's mtime. Idempotent on 'cache'-sourced rows."""
    if any(r.get("source") == "cache" for r in _rows()):
        return 0
    if not cache_path.exists():
        return 0
    mtime = _dt.datetime.fromtimestamp(cache_path.stat().st_mtime,
                                       _dt.timezone.utc)
    records = json.load(open(cache_path, encoding="utf-8"))
    return record(records, ts=mtime.isoformat(timespec="seconds"),
                  source="cache")[1]


if __name__ == "__main__":
    ps = pulls()
    print(f"{LEDGER.name}: {len(ps)} pulls, "
          f"{sum(1 for _ in _rows()) - len(ps)} line rows")
    for p in ps[-5:]:
        print(f"  {p['ts']}  games={p['games']}  changed={p['rows']}  "
              f"source={p.get('source')}")
