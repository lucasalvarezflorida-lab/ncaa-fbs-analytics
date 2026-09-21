"""Freeze the card at recording.

  python freeze_card.py --week 4            -> freeze (refuses if already frozen)
  python freeze_card.py --week 4 --dry-run  -> show what would be frozen
  python freeze_card.py --week 4 --force    -> re-freeze (only before the episode airs)

Run it right after the pre-record pull (edge_report.py --week N --view ml
--publish). It
  1. copies card_data_week{N}.json -> card_data_week{N}_frozen.json; from then
     on make_episode_deck.py reads ONLY the frozen file, so the Friday / Sunday
     scheduled pulls cannot change a number that was said on air;
  2. writes the frozen machine score calls into score_tracker.json (week N rows);
  3. INTERNAL: saves every card game's full line history (first seen -> each
     pull -> frozen) to internal/line_moves_week{N}.json and appends a summary
     to internal/LINE_MOVES_2026.md for the end-of-season deep dive. Line
     movement never goes on a slide.
The card = the week-N rows of score_tracker.json (away / home)."""
import argparse, datetime as dt, json, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)
import line_ledger  # noqa: E402


def score_call(margin, total):
    """(away_pts, home_pts): the machine margin laid over the total; never a tie."""
    hp, ap = (total + margin) / 2, (total - margin) / 2
    h, a = int(hp + 0.5), int(ap + 0.5)
    if h == a and margin:
        h, a = (h + 1, a) if margin > 0 else (h, a + 1)
    return [a, h]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    src, dst = f"card_data_week{a.week}.json", f"card_data_week{a.week}_frozen.json"
    if os.path.exists(dst) and not (a.force or a.dry_run):
        sys.exit(f"{dst} already exists - the card is frozen. Use --force only if the episode has not aired.")
    card = json.load(open(src, encoding="utf-8"))
    by = {(g["away"], g["home"]): g for g in card["games"]}
    tracker = json.load(open("score_tracker.json", encoding="utf-8"))
    rows = [r for r in tracker if r["week"] == a.week]
    if not rows:
        sys.exit(f"no week {a.week} rows in score_tracker.json - add the card there first")
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    moves, lines = [], [f"\n## Week {a.week} — frozen {now} (lines as of {card.get('lines_as_of')})\n",
                        "| Game | Machine | Market at recording | First seen | Pulls | Path (home team's spread) |", "|---|---|---|---|---|---|"]
    print(f"week {a.week} card, lines as of {card.get('lines_as_of')}:")
    for r in rows:
        g = by.get((r["away"], r["home"]))
        if not g:
            print("  NOT IN CARD DATA:", r["game"]); continue
        b = g["books"].get("DraftKings") or g["books"].get("Bovada") or {}
        call = score_call(g["model_margin"], float(g["ou"])) if g.get("ou") is not None else None
        ser = line_ledger.series(g["game_id"])
        path = [(x["ts"][:16], x.get("spread")) for x in ser if x.get("spread") is not None]
        dedup = [p for i, p in enumerate(path) if i == 0 or p[1] != path[i - 1][1]]
        moves.append(dict(game=r["game"], game_id=g["game_id"], model_margin=g["model_margin"], model_p_home=g["model_p_home"],
                          frozen_spread=b.get("spread"), frozen_total=g.get("ou"), mkt_p_home=g.get("mkt_p_home"),
                          first_seen=path[0] if path else None, path=dedup, machine_call=call))
        print(f"  {r['game']:24s} machine {g['model_spread']:18s} market {g['mkt_spread']:16s} total {g.get('ou')}  call (away-home) {call}  | {len(dedup)} line changes since {path[0][0] if path else '-'}")
        lines.append(f"| {r['game']} | {g['model_spread']} | {g['mkt_spread']} | {path[0][1] if path else ''} ({path[0][0][:10] if path else ''}) | {len(path)} | " + " → ".join(f"{p[1]:+g}" for p in dedup) + " |")
        if call and not a.dry_run:
            r["machine"] = call
    if a.dry_run:
        print("dry run - nothing written"); return
    card["frozen_at"] = now
    json.dump(card, open(dst, "w", encoding="utf-8"), indent=1)
    json.dump(tracker, open("score_tracker.json", "w", encoding="utf-8"), indent=1)
    os.makedirs("internal", exist_ok=True)
    json.dump(dict(week=a.week, frozen_at=now, lines_as_of=card.get("lines_as_of"), games=moves),
              open(os.path.join("internal", f"line_moves_week{a.week}.json"), "w", encoding="utf-8"), indent=1)
    md = os.path.join("internal", "LINE_MOVES_2026.md")
    head = "" if os.path.exists(md) else ("# Line movement on the podcast card — INTERNAL, for the end-of-season deep dive\n\n"
           "One block per week, written by freeze_card.py at recording. Spreads are the HOME team's (negative = home favored).\n"
           "Questions for the season review: does the market move toward or away from the machine between first-seen and recording,\n"
           "and between recording and the close? Do the games that moved most grade differently?\n")
    open(md, "a", encoding="utf-8").write(head + "\n".join(lines) + "\n")
    print(f"\nFROZEN -> {dst}; score_tracker.json updated; internal/line_moves_week{a.week}.json + LINE_MOVES_2026.md written.")
    print("Next: python make_episode_deck.py -> deck_lint.py -> push_deck.py; then internal\\backup.bat")


if __name__ == "__main__":
    main()
