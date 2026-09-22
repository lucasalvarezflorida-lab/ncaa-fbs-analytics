"""Floating text boxes for the DEEP DIVE panel on every conference tab (Lucas 9/22).

The four deep-dive sections (CAPSULE / ROSTER / IDENTITY / PREDICTION) used to
be wrapped text in merged N:R cells, and their row heights (hundreds of
points for the wordy teams) stretched the schedule and roster rows on the
left. Now build_conference_book puts each section's dropdown formula in a
HIDDEN cell (column AJ, on the section's label row, with the box height in
AK) and this step draws a text box over the panel LINKED to that cell, so
the text still follows the team dropdown while every row keeps its normal
height. openpyxl cannot draw shapes and drops them on every rebuild, so
this runs through Excel automation after each rebuild (refresh_all calls it
before the recalc step).

    python deep_dive_boxes.py            # (re)draw the boxes in NCAA_FBS_Teams.xlsm
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = ("CAPSULE", "ROSTER", "IDENTITY", "PREDICTION")
FORMULA_COL, HEIGHT_COL, PANEL_FIRST, PANEL_LAST = "AJ", "AK", "N", "R"


def add_boxes(book: Path) -> int:
    import win32com.client
    xl = win32com.client.Dispatch("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    n_boxes = 0
    try:
        wb = xl.Workbooks.Open(str(book))
        for ws in wb.Worksheets:
            name = ws.Name
            if name.startswith("_"):
                continue
            # find the DEEP DIVE header in column N
            hdr = None
            for r in range(40, 80):
                v = ws.Range(f"{PANEL_FIRST}{r}").Value
                if isinstance(v, str) and v.startswith("DEEP DIVE"):
                    hdr = r
                    break
            if hdr is None:
                continue
            for shp in list(ws.Shapes):
                if str(shp.Name).startswith("deep_"):
                    shp.Delete()
            width = ws.Range(f"{PANEL_FIRST}1:{PANEL_LAST}1").Width
            r = hdr + 1
            while r < hdr + 400:
                v = ws.Range(f"{PANEL_FIRST}{r}").Value
                if isinstance(v, str) and any(v.startswith(k) for k in LABELS):
                    h = ws.Range(f"{HEIGHT_COL}{r}").Value
                    if not h:
                        r += 1
                        continue
                    anchor = ws.Range(f"{PANEL_FIRST}{r + 1}")
                    shp = ws.Shapes.AddTextbox(1, anchor.Left, anchor.Top, width, float(h))
                    shp.Name = f"deep_{v.split()[0].lower()}"
                    shp.DrawingObject.Formula = f"=${FORMULA_COL}${r}"      # linked text: follows the dropdown
                    tf = shp.TextFrame2
                    tf.WordWrap = -1
                    tf.AutoSize = 0
                    tf.MarginLeft = 4
                    tf.MarginRight = 4
                    tf.MarginTop = 3
                    tf.TextRange.Font.Name = "Arial"
                    tf.TextRange.Font.Size = 10
                    shp.Fill.ForeColor.RGB = 0xFFFFFF
                    shp.Line.ForeColor.RGB = 0xD9D9D9
                    shp.Placement = 1          # move and size with cells
                    n_boxes += 1
                r += 1
        wb.Save()
        wb.Close(False)
    finally:
        xl.Quit()
    print(f"deep-dive text boxes: {n_boxes} drawn")
    return n_boxes


if __name__ == "__main__":
    book = HERE / "NCAA_FBS_Teams.xlsm"
    add_boxes(book)
