"""tape.py - assemble "Tale of the Tape": tape_template.html + tape_data_2026.json -> tape/index.html.

The page is self-contained (data and logos embedded) because the artifact sandbox blocks every
external load. Rebuild after `python tape_data.py` (sunday.py runs both); republish the artifact
on Lucas's word.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "tape_template.html"
DATA = HERE / "tape_data_2026.json"
OUT = HERE / "tape" / "index.html"


def build() -> Path:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8")
    assert "__TAPE_DATA__" in html
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html.replace("__TAPE_DATA__", payload), encoding="utf-8")
    return OUT


if __name__ == "__main__":
    if "--data" in sys.argv:
        import subprocess
        subprocess.run([sys.executable, str(HERE / "tape_data.py")], check=True)
    p = build()
    print(f"wrote {p.relative_to(HERE)} ({p.stat().st_size // 1024} KB)")
