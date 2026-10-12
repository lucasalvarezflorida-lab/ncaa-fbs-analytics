"""seat.py - assemble "The Seat and the Trophy": seat_template.html + seat_data_2026.json -> seat/index.html.

Self-contained (data and logos embedded). Rebuild after `python seat_data.py` (sunday.py runs both,
step 16d); republish the artifact from a session (same file path) on Lucas's word. NO MARKET on the page.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "seat_template.html"
DATA = HERE / "seat_data_2026.json"
OUT = HERE / "seat" / "index.html"


def build() -> Path:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8")
    assert "__SEAT_DATA__" in html
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html.replace("__SEAT_DATA__", payload), encoding="utf-8")
    return OUT


if __name__ == "__main__":
    if "--data" in sys.argv:
        import subprocess
        subprocess.run([sys.executable, str(HERE / "seat_data.py")], check=True)
    p = build()
    print(f"wrote {p.relative_to(HERE)} ({p.stat().st_size // 1024} KB)")
