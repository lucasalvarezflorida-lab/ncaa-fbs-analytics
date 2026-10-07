"""Hot Seat slide written DIRECTLY into the Google Slides file (Slides API, no pptx, no conversion) - Lucas 10/6/2026.
First slide on the direct path; the rest of the deck still goes through make_episode_deck.py + push_deck.py.

    python slides_hotseat.py --week 6 --file-id <Ep file id>            # replaces the existing Hot Seat slide in place
    python slides_hotseat.py --week 6 --file-id <id> --dry-run          # builds the requests, writes nothing

Finds the deck's Hot Seat slide by its kicker text ("THE SEAT BOARD"), inserts the new slide at the same position, deletes
the old one. Every other slide - and anything Lucas hand-edited on them - is untouched. Layout mirrors the pptx slide
(inches -> EMU); logos come from the cached ESPN URLs in rosters/data/teams_fbs_2026.json (the API needs a URL).
"""
from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.request
from pathlib import Path

import certifi

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

EMU = 914400
NAVY, NAVY2, ORANGE, WHITE, PALE, UP, DOWN = "0A2851", "123568", "F47321", "FFFFFF", "CADCFC", "5CD68A", "FF7A7A"
KICKER = "THE SEAT BOARD"
_TEAMS = {normalize_name(t["school"]): t for t in json.loads((HERE / "rosters" / "data" / "teams_fbs_2026.json").read_text(encoding="utf-8"))}


def rgb(hexs):
    return {"rgbColor": {"red": int(hexs[0:2], 16) / 255, "green": int(hexs[2:4], 16) / 255, "blue": int(hexs[4:6], 16) / 255}}


class Builder:
    def __init__(self, slide_id):
        self.sid = slide_id; self.req = []; self.n = 0

    def _id(self):
        self.n += 1; return f"{self.sid}_{self.n}"

    def box(self, x, y, w, h, fill, shape="RECTANGLE"):
        oid = self._id()
        self.req.append({"createShape": {"objectId": oid, "shapeType": shape, "elementProperties": {"pageObjectId": self.sid,
                         "size": {"width": {"magnitude": w * EMU, "unit": "EMU"}, "height": {"magnitude": h * EMU, "unit": "EMU"}},
                         "transform": {"scaleX": 1, "scaleY": 1, "translateX": x * EMU, "translateY": y * EMU, "unit": "EMU"}}}})
        self.req.append({"updateShapeProperties": {"objectId": oid, "fields": "shapeBackgroundFill.solidFill.color,outline.propertyState",
                         "shapeProperties": {"shapeBackgroundFill": {"solidFill": {"color": rgb(fill)}}, "outline": {"propertyState": "NOT_RENDERED"}}}})
        return oid

    def text(self, x, y, w, h, s, size, color=WHITE, bold=False, align="START"):
        oid = self._id()
        self.req.append({"createShape": {"objectId": oid, "shapeType": "TEXT_BOX", "elementProperties": {"pageObjectId": self.sid,
                         "size": {"width": {"magnitude": w * EMU, "unit": "EMU"}, "height": {"magnitude": h * EMU, "unit": "EMU"}},
                         "transform": {"scaleX": 1, "scaleY": 1, "translateX": x * EMU, "translateY": y * EMU, "unit": "EMU"}}}})
        self.req.append({"insertText": {"objectId": oid, "text": s}})
        self.req.append({"updateTextStyle": {"objectId": oid, "fields": "fontFamily,fontSize,foregroundColor,bold",
                         "style": {"fontFamily": "Arial", "fontSize": {"magnitude": size, "unit": "PT"}, "foregroundColor": {"opaqueColor": rgb(color)}, "bold": bold}}})
        self.req.append({"updateParagraphStyle": {"objectId": oid, "fields": "alignment", "style": {"alignment": align}}})
        self.req.append({"updateShapeProperties": {"objectId": oid, "fields": "contentAlignment,autofit.autofitType",
                         "shapeProperties": {"contentAlignment": "TOP", "autofit": {"autofitType": "NONE"}}}})
        return oid

    def logo(self, x, y, team):
        t = _TEAMS.get(normalize_name(team))
        if not t or not t.get("logos"):
            return
        self.box(x, y + 0.05, 0.3, 0.3, WHITE, "ELLIPSE")
        oid = self._id()
        self.req.append({"createImage": {"objectId": oid, "url": t["logos"][0].replace("http://", "https://"), "elementProperties": {"pageObjectId": self.sid,
                         "size": {"width": {"magnitude": 0.23 * EMU, "unit": "EMU"}, "height": {"magnitude": 0.23 * EMU, "unit": "EMU"}},
                         "transform": {"scaleX": 1, "scaleY": 1, "translateX": (x + 0.035) * EMU, "translateY": (y + 0.085) * EMU, "unit": "EMU"}}}})


def hot_seat_requests(slide_id, rows, episode, week):
    """The slide, request by request - the same geometry as make_episode_deck's pptx version."""
    b = Builder(slide_id)
    b.text(0.9, 0.42, 11.5, 0.4, f"EPISODE {episode} · WEEK {week} · {KICKER}", 14, ORANGE, True)
    b.text(0.9, 0.76, 11.5, 0.8, "Hot Seat Top 10", 40, WHITE, True)
    b.text(0.9, 1.5, 11.5, 0.3, "40% what six hot-seat lists say + 60% the machine's odds he is gone by next season", 13, PALE, True)
    TOP, RH = 2.08, 0.4
    hdr = [(1.75, 2.8, "COACH · SCHOOL", "START"), (4.6, 1.5, "TENURE", "START"), (6.15, 0.55, "LISTS", "END"), (6.75, 0.55, "RECORD", "END"),
           (7.35, 0.7, "P(GONE)", "END"), (8.1, 0.95, "BUYOUT", "END"), (9.1, 0.5, "Δ", "END"), (9.65, 0.55, "SCORE", "END"), (10.3, 2.1, "LAST RESULT", "START")]
    for x, w, lab, al in hdr:
        b.text(x, TOP - 0.25, w, 0.22, lab, 8, PALE, True, al)
    for i, r in enumerate(rows[:10]):
        y = TOP + i * RH
        if i % 2 == 0:
            b.box(0.9, y, 11.5, RH, NAVY2)
        b.text(0.9, y + 0.06, 0.4, 0.3, str(i + 1), 13, ORANGE, True, "END")
        b.logo(1.35, y, r["team"])
        b.text(1.75, y + 0.06, 2.8, 0.3, f"{r['coach']} · {r['team']}", 12, WHITE, True)
        b.text(4.6, y + 0.09, 1.5, 0.3, r.get("tenure", ""), 8.5, PALE)
        b.text(6.15, y + 0.07, 0.55, 0.3, f"{r['cbs']:.1f}{'*' if r.get('cbs_est') else ''}", 11, WHITE, True, "END")
        b.text(6.75, y + 0.07, 0.55, 0.3, r.get("record", ""), 11, WHITE, False, "END")
        p = r["p_gone"]
        b.text(7.35, y + 0.07, 0.7, 0.3, f"{round(100 * p)}%", 11, DOWN if p >= 0.3 else (UP if p < 0.15 else WHITE), True, "END")
        b.text(8.1, y + 0.07, 0.95, 0.3, f"{r.get('buyout', '—')}{'*' if r.get('buyout_est') else ''}", 10.5, WHITE, True, "END")
        d = r.get("delta") or 0.0
        b.text(9.1, y + 0.09, 0.5, 0.3, f"{d:+.1f}" if d else "0.0", 10, UP if d > 0 else (DOWN if d < 0 else PALE), bool(d), "END")
        b.text(9.65, y + 0.06, 0.55, 0.3, f"{r['score']:.0f}", 12.5, ORANGE, True, "END")
        b.text(10.3, y + 0.09, 2.1, 0.3, (r.get("results") or ["—"])[-1], 8.5, PALE)
    fy = TOP + 10 * RH + 0.12
    b.box(0.9, fy, 11.5, 0.62, NAVY2, "ROUND_RECTANGLE")
    b.text(1.1, fy + 0.06, 11.2, 0.28, "Next three: " + " · ".join(f"{x['coach']} {x['score']:.0f}" for x in rows[10:13]), 11, WHITE, True)
    b.text(1.1, fy + 0.32, 11.2, 0.28, "LISTS = six hot-seat lists (CBS, ESPN, SportsGrid, 2 Stripes, Eh Gap, Coaches Hot Seat), 0–5; * = none names him · "
           "P(GONE) = odds he is gone next season, from 2014–25 · BUYOUT = what the school owes to fire him now; * = estimated, — = undisclosed", 10.5, PALE)
    return b.req


def api(creds, method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, context=ssl.create_default_context(cafile=certifi.where())) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True, help="the upcoming card's week (boards_week{N}.json)")
    ap.add_argument("--file-id", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    import re
    src = (HERE / "make_episode_deck.py").read_text(encoding="utf-8")
    episode = int(re.search(r"^EPISODE, WEEK = (\d+), (\d+)", src, re.M).group(1))
    rows = json.loads((HERE / f"boards_week{a.week}.json").read_text(encoding="utf-8"))["hot_seat"]
    from push_deck import get_credentials
    creds = get_credentials()
    base = f"https://slides.googleapis.com/v1/presentations/{a.file_id}"
    pres = api(creds, "GET", base + "?fields=title,slides(objectId,pageElements(shape(text(textElements(textRun(content))))))")
    old_id, idx = None, None
    for i, s in enumerate(pres["slides"]):
        blob = " ".join(tr["textRun"]["content"] for el in s.get("pageElements", []) for tr in el.get("shape", {}).get("text", {}).get("textElements", []) if "textRun" in tr)
        if KICKER in blob:
            old_id, idx = s["objectId"], i; break
    if old_id is None:
        idx = 1; print("no existing Hot Seat slide found - inserting at position 2")
    new_id = f"hotseat_w{a.week}_{abs(hash(str(rows[:3]))) % 100000}"
    reqs = [{"createSlide": {"objectId": new_id, "insertionIndex": idx, "slideLayoutReference": {"predefinedLayout": "BLANK"}}},
            {"updatePageProperties": {"objectId": new_id, "fields": "pageBackgroundFill.solidFill.color", "pageProperties": {"pageBackgroundFill": {"solidFill": {"color": rgb(NAVY)}}}}}]
    reqs += hot_seat_requests(new_id, rows, episode, a.week)
    if old_id:
        reqs.append({"deleteObject": {"objectId": old_id}})
    print(f"'{pres['title']}': {len(pres['slides'])} slides; Hot Seat slide {'#' + str(idx + 1) + ' (' + old_id + ')' if old_id else 'absent'}; {len(reqs)} requests")
    if a.dry_run:
        (HERE / "internal" / f"slides_hotseat_week{a.week}_requests.json").write_text(json.dumps(reqs, indent=1), encoding="utf-8"); print("dry run - requests written to internal/"); return
    api(creds, "POST", base + ":batchUpdate", {"requests": reqs})
    print(f"written in place: new slide {new_id} at position {idx + 1}" + (f", old slide {old_id} removed" if old_id else ""))


if __name__ == "__main__":
    main()
