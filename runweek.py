"""runweek.py - the run folder behind `/run-week N` (Lucas 10/14): one folder per week under
internal/runs/, one subfolder per step, one status.json the orchestrator and the agents share.

    python runweek.py init  --week 7 [--phase sunday|midweek|record|full]   # create internal/runs/2026-wk07/
    python runweek.py mark  --week 7 --step 03-model --status ok --note "..."  # record a step's outcome
    python runweek.py reset --week 7 --step 02-research                      # rename the folder to *.prev-<ts> before a rerun
    python runweek.py show  --week 7                                         # print status.json as a table

Status values: pending | running | ok | warn | fail | proposal (model-updater wants to change the model - stop
and ask Lucas) | ask (an agent wants to delete or overwrite something - stop and ask). Nothing here deletes a file.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE / "internal" / "runs"
SEASON = 2026
STEPS = ["01-data", "02-research", "03-model", "04-slides", "05-notes"]
PHASES = {   # which steps a phase runs, in order (the three real-time moments of the week + the full Sunday form)
    "full": STEPS,
    "sunday": ["01-data", "03-model"],
    "midweek": ["01-data", "02-research", "03-model", "04-slides", "05-notes"],
    "record": ["01-data", "03-model", "04-slides", "05-notes"],
}
STATUSES = ("pending", "running", "ok", "warn", "fail", "proposal", "ask", "skipped")


def week_id(week: int) -> str:
    return f"{SEASON}-wk{week:02d}"


def run_dir(week: int) -> Path:
    return RUNS / week_id(week)


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def load(week: int) -> dict:
    p = run_dir(week) / "status.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save(week: int, st: dict) -> None:
    (run_dir(week) / "status.json").write_text(json.dumps(st, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def cmd_init(a) -> None:
    d = run_dir(a.week)
    d.mkdir(parents=True, exist_ok=True)
    for s in STEPS:
        (d / s).mkdir(exist_ok=True)
        for pkg in ("package-a", "package-b"):
            if s in ("04-slides", "05-notes"):
                (d / s / pkg).mkdir(exist_ok=True)
    st = load(a.week) or dict(week=a.week, week_id=week_id(a.week), created=_now(), runs=[], steps={})
    st["runs"].append(dict(phase=a.phase, started=_now(), steps=PHASES[a.phase]))
    for s in STEPS:
        st["steps"].setdefault(s, dict(status="pending", history=[]))
    for s in PHASES[a.phase]:
        st["steps"][s]["status"] = "pending"
    save(a.week, st)
    print(d)
    print("phase", a.phase, "->", " -> ".join(PHASES[a.phase]))


def cmd_mark(a) -> None:
    st = load(a.week)
    if not st:
        sys.exit("no run folder - run `init` first")
    if a.status not in STATUSES:
        sys.exit(f"status must be one of {STATUSES}")
    rec = st["steps"].setdefault(a.step, dict(status="pending", history=[]))
    rec["status"] = a.status
    rec["updated"] = _now()
    if a.agent:
        rec["agent"] = a.agent
    if a.note:
        rec["note"] = a.note
    rec["history"].append(dict(ts=_now(), status=a.status, note=a.note or "", agent=a.agent or ""))
    save(a.week, st)
    print(f"{week_id(a.week)} {a.step}: {a.status}" + (f" - {a.note}" if a.note else ""))


def cmd_reset(a) -> None:
    d = run_dir(a.week) / a.step
    if not d.exists():
        sys.exit(f"{d} does not exist")
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    prev = d.with_name(f"{a.step}.prev-{stamp}")
    d.rename(prev)                       # never deleted - renamed aside
    d.mkdir()
    if a.step in ("04-slides", "05-notes"):
        for pkg in ("package-a", "package-b"):
            (d / pkg).mkdir()
    st = load(a.week)
    if st:
        rec = st["steps"].setdefault(a.step, dict(status="pending", history=[]))
        rec["status"] = "pending"
        rec["history"].append(dict(ts=_now(), status="reset", note=f"previous output kept as {prev.name}", agent=""))
        save(a.week, st)
    print(f"{a.step} reset; previous output in {prev.name}")


def cmd_show(a) -> None:
    st = load(a.week)
    if not st:
        sys.exit(f"no run folder for week {a.week} ({run_dir(a.week)})")
    print(f"{st['week_id']}  created {st['created']}  runs: " + "; ".join(f"{r['phase']} @ {r['started']}" for r in st["runs"]))
    for s in STEPS:
        rec = st["steps"].get(s, {})
        print(f"  {s:12s} {rec.get('status', '-'):9s} {rec.get('updated', ''):20s} {rec.get('agent', ''):18s} {rec.get('note', '')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("--week", type=int, required=True); p.add_argument("--phase", choices=list(PHASES), default="full"); p.set_defaults(fn=cmd_init)
    p = sub.add_parser("mark"); p.add_argument("--week", type=int, required=True); p.add_argument("--step", choices=STEPS, required=True)
    p.add_argument("--status", required=True); p.add_argument("--note", default=""); p.add_argument("--agent", default=""); p.set_defaults(fn=cmd_mark)
    p = sub.add_parser("reset"); p.add_argument("--week", type=int, required=True); p.add_argument("--step", choices=STEPS, required=True); p.set_defaults(fn=cmd_reset)
    p = sub.add_parser("show"); p.add_argument("--week", type=int, required=True); p.set_defaults(fn=cmd_show)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
