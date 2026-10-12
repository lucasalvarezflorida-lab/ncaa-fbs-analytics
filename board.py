"""board.py - assemble "The Board": board_template.html + board_data_2026.json -> board/index.html.

Self-contained (data and logos embedded; the artifact sandbox blocks every external load). Rebuild
after `python board_data.py` (sunday.py runs both, step 16b); republish the artifact from a session
(same file path) on Lucas's word.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "board_template.html"
DATA = HERE / "board_data_2026.json"
OUT = HERE / "board" / "index.html"


def build() -> Path:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8")
    assert "__BOARD_DATA__" in html
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html.replace("__BOARD_DATA__", payload), encoding="utf-8")
    return OUT


if __name__ == "__main__":
    if "--data" in sys.argv:
        import subprocess
        subprocess.run([sys.executable, str(HERE / "board_data.py")], check=True)
    p = build()
    print(f"wrote {p.relative_to(HERE)} ({p.stat().st_size // 1024} KB)")
