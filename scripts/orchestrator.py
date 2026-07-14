"""
NCAA FBS Model — Weekly orchestrator (revised pipeline)

Runs the six-phase pipeline in sequence. Each phase is a subprocess —
same pattern as the NHL model — so a failure in one phase logs cleanly
and preserves the previous week's JSON for the workbook to keep showing.

Pipeline phases (post-revision):
    1. fetch_sp_plus.py           — SP+ base + unit splits (replaces old
                                    fetch_team_ratings + fetch_advanced_stats)
    2. fetch_returning_production — returning EPA % per team
    3. fetch_qb_modifiers         — regression-weighted QB modifier
    4. compute_rest_modifier      — schedule-derived rest modifier
                                    (form modifier dropped)
    5. compute_ratings            — consolidates everything into the
                                    five sub-ratings + composite
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
PHASES = [
    "fetch_sp_plus.py",
    "fetch_returning_production.py",
    "fetch_qb_modifiers.py",
    "compute_rest_modifier.py",
    "compute_ratings.py",
]


def run_phase(script: str) -> bool:
    print(f"\n=== {script} ===")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script)],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"PHASE FAILED: {script}")
        print(result.stderr)
        return False
    return True


def main() -> int:
    print(f"NCAA FBS pipeline start: {datetime.now().isoformat()}")
    for phase in PHASES:
        if not run_phase(phase):
            print("Aborting — previous week's JSON remains in place")
            return 1
    print(f"\nPipeline complete: {datetime.now().isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
