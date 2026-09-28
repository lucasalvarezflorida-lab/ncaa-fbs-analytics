"""Shared runner for the weekly orchestrators (sunday.py, tuesday.py,
recording.py): runs each step as a subprocess, keeps going on failure, logs
everything, and writes one summary file the session reads instead of twenty
tool calls. Nothing here reaches the show: push / merge / share stay manual.
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTERNAL = HERE / "internal"


class Runner:
    def __init__(self, name: str, week: int):
        self.name, self.week = name, week
        self.log = INTERNAL / f"{name}_week{week}_run.log"
        self.summary = INTERNAL / f"{name}_week{week}.md"
        INTERNAL.mkdir(exist_ok=True)
        self.lines = [f"# {name} — week {week} — {dt.datetime.now().isoformat(timespec='minutes')}", ""]
        self.failed = []
        self.log.write_text("", encoding="utf-8")

    def step(self, label: str, cmd: list[str], tail: int = 12, timeout: int = 1800) -> str:
        print(f"== {label}")
        with open(self.log, "a", encoding="utf-8") as f:
            f.write(f"\n\n===== {label}: {' '.join(cmd)}\n")
        try:
            r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
            out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr and r.stderr.strip() else "")
            ok = r.returncode == 0
        except subprocess.TimeoutExpired:
            out, ok = f"TIMEOUT after {timeout}s", False
        with open(self.log, "a", encoding="utf-8") as f:
            f.write(out)
        last = "\n".join([ln for ln in out.strip().splitlines() if ln.strip()][-tail:])
        self.lines.append(f"## {label} — {'ok' if ok else 'FAILED'}")
        self.lines.append("```\n" + last + "\n```")
        if not ok:
            self.failed.append(label)
        return out

    def note(self, text: str):
        self.lines.append(text)

    def py(self, label: str, code: str, tail: int = 20):
        return self.step(label, [sys.executable, "-c", code], tail=tail)

    def finish(self):
        self.lines.insert(2, ("All steps ok." if not self.failed else "FAILED: " + ", ".join(self.failed)) + f" Full log: {self.log.name}")
        self.summary.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        print(f"\nsummary -> {self.summary.relative_to(HERE)}" + ("" if not self.failed else f"   FAILED: {', '.join(self.failed)}"))
        return self.summary


def card_teams_from_deck() -> tuple[list[tuple[str, str]], int, int]:
    """(away, home) pairs of the CURRENT card from make_episode_deck.py's GAMES
    block (cfbd=("Away", "Home") tuples), plus EPISODE and WEEK."""
    import re
    s = (HERE / "make_episode_deck.py").read_text(encoding="utf-8")
    m = re.search(r"^EPISODE, WEEK = (\d+), (\d+)", s, re.M)
    ep, wk = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    i = s.index("\nGAMES = [")
    j = s.index("\n]\n", i)
    pairs = re.findall(r'cfbd=\("([^"]+)", "([^"]+)"\)', s[i:j])
    return pairs, ep, wk


def ap_check(week: int) -> str:
    """Has CFBD ingested this week's AP poll? Falls back to internal/ap_week{N}.json."""
    try:
        sys.path.insert(0, str(HERE / "fpi-decomposition"))
        from refresh_all import load_env_key
        load_env_key()
        import cfbd_client as cfbd
        d = cfbd.get("/rankings", {"year": 2026, "week": week, "seasonType": "regular"}, True)
        for wk in d or []:
            for poll in wk.get("polls", []):
                if poll.get("poll") == "AP Top 25":
                    top = [(r["rank"], r["school"]) for r in poll["ranks"]][:5]
                    return f"AP Week {week} on CFBD: yes — {top} ..."
    except Exception as e:  # noqa: BLE001
        return f"AP check failed: {e}"
    f = INTERNAL / f"ap_week{week}.json"
    return f"AP Week {week} on CFBD: not yet" + (f" (internal/ap_week{week}.json exists)" if f.exists() else " (no internal copy either — paste it or wait for Tuesday)")
