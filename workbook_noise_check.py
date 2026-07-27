"""Post-refresh guard: discard no-op workbook rewrites.

Excel COM recalc rewrites xlsx/xlsm binaries (docProps timestamps,
calcChain order) even when no cell changed, so the weekly loops leave
phantom modifications in git status. For every git-modified workbook,
compare the working copy against HEAD cell-by-cell: byte-different but
cell-identical -> git restore; any real difference (sheets, dimensions,
values) -> leave in place for review and say what moved.

Conservative by design: if either copy fails to load, the file is left
untouched. Always exits 0 so it can't fail the scheduled loop.
"""
import subprocess
import sys
import tempfile
from itertools import zip_longest
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=HERE, capture_output=True)


def sheet_values(path: str | Path):
    """{sheet title: [row tuples]} of cached cell values."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        return {ws.title: [row for row in ws.iter_rows(values_only=True)]
                for ws in wb.worksheets}
    finally:
        wb.close()


def first_diff(work: dict, head: dict) -> str | None:
    """None if cell-identical, else a one-line description of a change."""
    if set(work) != set(head):
        return f"sheet set changed: {sorted(set(work) ^ set(head))}"
    for title in work:
        for i, (rw, rh) in enumerate(zip_longest(work[title], head[title]), 1):
            if rw != rh:
                return f"'{title}' row {i}: {rw and rw[:4]} vs {rh and rh[:4]}"
    return None


def main() -> None:
    status = git("status", "--porcelain").stdout.decode()
    books = [line[3:].strip().strip('"') for line in status.splitlines()
             if line[:2] == " M"
             and line.strip().lower().endswith((".xlsx", ".xlsm"))]
    if not books:
        print("noise check: no modified workbooks")
        return
    for rel in books:
        show = git("show", f"HEAD:{rel}")
        if show.returncode != 0:
            print(f"noise check: {rel} — no HEAD version, left alone")
            continue
        with tempfile.NamedTemporaryFile(suffix=Path(rel).suffix,
                                         delete=False) as tf:
            tf.write(show.stdout)
            head_copy = tf.name
        try:
            diff = first_diff(sheet_values(HERE / rel), sheet_values(head_copy))
        except Exception as e:  # unreadable/locked: never touch it
            print(f"noise check: {rel} — compare failed ({e}), left alone")
            continue
        finally:
            Path(head_copy).unlink(missing_ok=True)
        if diff is None:
            git("restore", rel)
            print(f"noise check: {rel} — cell-identical to HEAD, restored")
        else:
            print(f"noise check: {rel} — REAL change, left for review "
                  f"({diff})")


if __name__ == "__main__":
    main()
    sys.exit(0)
