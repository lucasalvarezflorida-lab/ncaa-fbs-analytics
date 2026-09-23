"""Merge Corey's deck with ours on the SHOW'S FLOW (built 9/23 for Ep5).

merge_deck.py matches slides by shared text, which goes wrong once Corey
builds his new week on top of last week's merged file: our stale Week-N-1
slides sit in his file at last week's positions and get "matched". This
merges by the flow instead, the order the show has used since Ep4:

    his title
    our RECEIPTS
    his Winners and Losers
    our HEISMAN          his Heisman
    our TOP 25           his Top 25 slides
    our HOT SEAT         his Hot Seat
    our CARD
    per game (his order): his divider, his "<A> Keys", OUR A team slide,
                          his "<B> Keys", OUR B team slide, his score slide,
                          OUR number slide
    his Superdog slides
    our CLOSER (predictions)

Every stale copy of one of our slides in his file is deleted first (any
slide carrying "the receipts", "EPISODE N ·", "What it takes to win",
"THE NUMBER", "Five Games, One Card" or "Our predictions"). His own slides
are never edited and keep their order. His Google file is never touched:
this works on a read-only export.

    python merge_flow.py --his decks\\corey_1UpeONbb_export.pptx --ours decks\\2026_Week4_Episode5.pptx
                         [--out decks\\X_merged.pptx]
Then push_deck.py --pptx <out> --file-id <merged file id> (Lucas's word)."""
from __future__ import annotations

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STALE = ("the receipts", "What it takes to win", "THE NUMBER", "Five Games, One Card", "Our predictions",
         "THE MACHINE'S TOP 25", "OUR HEISMAN BOARD", "THE SEAT BOARD")


def texts(slide):
    out = []
    for sh in slide.Shapes:
        try:
            if sh.HasTextFrame and sh.TextFrame.HasText:
                out.append(sh.TextFrame.TextRange.Text.replace("\r", "\n").strip())
        except Exception:
            continue
    return out


def classify_ours(slide):
    t = texts(slide)
    joined = "\n".join(t)
    if "the receipts" in joined:
        return ("receipts", None)
    if "TOP 25" in joined and "Our Top 25" in joined:
        return ("top25", None)
    if "SEAT BOARD" in joined:
        return ("hotseat", None)
    if "HEISMAN BOARD" in joined:
        return ("heisman", None)
    if "Five Games, One Card" in joined:
        return ("card", None)
    if "Our predictions" in joined:
        return ("closer", None)
    if "What it takes to win" in joined:
        name = next((x for x in t if "What it takes to win" not in x and len(x) < 30), t[0])
        return ("team", name.strip().split("\n")[0])   # the team-name shape
    if "THE NUMBER" in joined:
        game = next((x for x in t if " at " in x and "\n" not in x and len(x) < 60), "")
        return ("number", game)
    return ("other", None)


def is_score_slide(slide):
    t = [x for x in texts(slide) if x]
    nums = [x for x in t if re.fullmatch(r"\d{1,2}", x)]
    return len(nums) >= 2 and len(t) <= 6


def merge(his_pptx, ours_pptx, out_pptx):
    import win32com.client
    app = win32com.client.Dispatch("PowerPoint.Application")
    dst = app.Presentations.Open(os.path.abspath(his_pptx), False, False, False)
    src = app.Presentations.Open(os.path.abspath(ours_pptx), True, False, False)
    ours = []
    for i in range(1, src.Slides.Count + 1):
        kind, key = classify_ours(src.Slides(i))
        ours.append(dict(i=i, kind=kind, key=key, rgb=src.Slides(i).Background.Fill.ForeColor.RGB))
    src.Close()
    log = []
    # 1. delete stale copies of our slides in his file
    j = 1
    removed = 0
    while j <= dst.Slides.Count:
        joined = "\n".join(texts(dst.Slides(j)))
        if any(m in joined for m in STALE):
            dst.Slides(j).Delete(); removed += 1
        else:
            j += 1
    log.append(f"removed {removed} stale copies of our slides from his deck ({dst.Slides.Count} of his own slides kept)")

    def his(pred):
        for k in range(1, dst.Slides.Count + 1):
            if pred("\n".join(texts(dst.Slides(k))), dst.Slides(k)):
                return k
        return None

    def insert_after(k, o, why):
        dst.Slides.InsertFromFile(os.path.abspath(ours_pptx), k, o["i"], o["i"])
        s = dst.Slides(k + 1)
        s.FollowMasterBackground = False
        s.Background.Fill.Solid()
        s.Background.Fill.ForeColor.RGB = o["rgb"]
        log.append(f"ours {o['i']:2} ({o['kind']}{' ' + o['key'] if o['key'] else ''}) -> after his slide {k} ({why})")

    by = {o["kind"]: o for o in ours if o["kind"] in ("receipts", "top25", "hotseat", "heisman", "card", "closer")}
    # 2. boards: receipts after the title; ours before each of his boards
    if "receipts" in by:
        insert_after(1, by["receipts"], "title")
    for kind, marker in (("heisman", "Heisman Rankings"), ("top25", "Top 25 Rankings"), ("hotseat", "Hot Seat")):
        k = his(lambda txt, s, m=marker: m in txt)
        if k and kind in by:
            insert_after(k - 1, by[kind], f"before his '{marker}'")
    # card: after his LAST Hot Seat slide (before the first game block)
    k = None
    for kk in range(1, dst.Slides.Count + 1):
        if "Hot Seat" in "\n".join(texts(dst.Slides(kk))):
            k = kk
    if k and "card" in by:
        insert_after(k, by["card"], "after his Hot Seat")
    # 3. games: team slides after his "<Team> Keys to the Game"; number slide after that game's score slide
    for o in [o for o in ours if o["kind"] == "team"]:
        k = his(lambda txt, s, t=o["key"]: txt.startswith(f"{t} Keys to the Game"))
        if k:
            insert_after(k, o, f"'{o['key']} Keys to the Game'")
        else:
            log.append(f"NO ANCHOR for our team slide {o['key']} - left out")
    for o in [o for o in ours if o["kind"] == "number"]:
        a, _, b = o["key"].partition(" at ")
        kb = his(lambda txt, s, t=b: txt.startswith(f"{t} Keys to the Game"))
        if not kb:
            log.append(f"NO ANCHOR for our number slide {o['key']} - left out"); continue
        ks = next((kk for kk in range(kb + 1, min(kb + 5, dst.Slides.Count + 1)) if is_score_slide(dst.Slides(kk))), None)
        insert_after(ks or (kb + 1), o, f"after his score slide for {o['key']}" if ks else f"after '{b} Keys' (+1, no score slide found)")
    # 4. closer last
    if "closer" in by:
        insert_after(dst.Slides.Count, by["closer"], "end")
    dst.SaveAs(os.path.abspath(out_pptx))
    n = dst.Slides.Count
    dst.Close()
    return log, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--his", required=True)
    ap.add_argument("--ours", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    out = a.out or os.path.splitext(a.ours)[0] + "_merged.pptx"
    log, n = merge(a.his, a.ours, out)
    print("\n".join(log))
    print(f"merged deck: {out} ({n} slides)")


if __name__ == "__main__":
    main()
