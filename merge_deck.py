"""Merge Corey's Slides deck with our current episode slides — without
touching his file.

1. Export his Google Slides file to .pptx (Drive export, read-only on his
   side; uses the push_deck.py token).
2. Open the export and our pptx in PowerPoint (COM). For each of our
   slides, find the stale copy in his deck (the slide sharing the most text
   lines) and replace it in place; a slide of ours with no copy in his deck
   (e.g. a missing team slide) is inserted right after his "<Team> Keys to
   the Game" slide. His own slides are untouched and keep their order.
3. Save decks/<name>_merged.pptx and, with --create, upload it as a NEW
   Google Slides file in Lucas's Drive (share separately with share_deck.py).

    python merge_deck.py --his-id <fileId> --ours decks\\2026_Week3_Episode4.pptx
    python merge_deck.py --his-id <fileId> --ours decks\\X.pptx --create "Man vs Machine - Ep4 - Week 3 (merged)"
"""

import argparse
import os
import ssl
import sys
import urllib.request

import certifi

from push_deck import HERE, PPTX_MIME, create, get_credentials

MIN_OVERLAP = 2          # shared distinctive lines needed to call a slide "the same slide"
MIN_LINE = 12            # ignore short lines (numbers, labels) when matching


def export_pptx(file_id, creds, out_path):
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export?mimeType={PPTX_MIME}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {creds.token}"})
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(req, context=ctx) as resp, open(out_path, "wb") as f:
        f.write(resp.read())
    return out_path


def slide_lines(slide):
    out = []
    for sh in slide.Shapes:
        try:
            if sh.HasTextFrame and sh.TextFrame.HasText:
                for ln in sh.TextFrame.TextRange.Text.replace("\r", "\n").split("\n"):
                    ln = ln.strip()
                    if len(ln) >= MIN_LINE:
                        out.append(ln)
        except Exception:
            continue
        try:
            if sh.HasTable:
                t = sh.Table
                for r in range(1, t.Rows.Count + 1):
                    for c in range(1, t.Columns.Count + 1):
                        ln = t.Cell(r, c).Shape.TextFrame.TextRange.Text.strip()
                        if len(ln) >= MIN_LINE:
                            out.append(ln)
        except Exception:
            continue
    return set(out)


def first_text(slide):
    for sh in slide.Shapes:
        try:
            if sh.HasTextFrame and sh.TextFrame.HasText:
                return sh.TextFrame.TextRange.Text.strip().split("\r")[0].strip()
        except Exception:
            continue
    return ""


def best_match(lines, dst, used):
    best, best_n = None, 0
    for j in range(1, dst.Slides.Count + 1):
        if j in used:
            continue
        n = len(lines & slide_lines(dst.Slides(j)))
        if n > best_n:
            best, best_n = j, n
    return (best, best_n) if best_n >= MIN_OVERLAP else (None, best_n)


def merge(his_pptx, ours_pptx, out_pptx):
    import win32com.client
    app = win32com.client.Dispatch("PowerPoint.Application")
    dst = app.Presentations.Open(os.path.abspath(his_pptx), False, False, False)
    src = app.Presentations.Open(os.path.abspath(ours_pptx), True, False, False)
    ours = [(i, slide_lines(src.Slides(i)), first_text(src.Slides(i)),
             src.Slides(i).Background.Fill.ForeColor.RGB) for i in range(1, src.Slides.Count + 1)]
    src.Close()

    def keep_background(slide, rgb):
        # InsertFromFile re-themes the slide onto his master (a dark slate);
        # our slides carry their own explicit background, so restore it.
        slide.FollowMasterBackground = False
        slide.Background.Fill.Solid()
        slide.Background.Fill.ForeColor.RGB = rgb

    used, log = set(), []
    for i, lines, head, rgb in ours:
        j, n = best_match(lines, dst, used)
        if j:
            dst.Slides.InsertFromFile(os.path.abspath(ours_pptx), j - 1, i, i)   # ours lands at j
            dst.Slides(j + 1).Delete()                                          # his stale copy
            keep_background(dst.Slides(j), rgb)
            used.add(j)
            log.append(f"replaced his slide {j:2} with ours {i:2} ({n} shared lines): {head[:60]}")
            continue
        # no copy in his deck: a team slide goes after his "<Team> Keys to the Game"
        anchor = None
        for k in range(1, dst.Slides.Count + 1):
            txt = " ".join(slide_lines(dst.Slides(k)) | {first_text(dst.Slides(k))})
            if head and f"{head} Keys to the Game" in txt:
                anchor = k
        if anchor:
            dst.Slides.InsertFromFile(os.path.abspath(ours_pptx), anchor, i, i)
            keep_background(dst.Slides(anchor + 1), rgb)
            used.add(anchor + 1)
            # indices after the insert shifted by one
            used = {u + 1 if u > anchor + 1 else u for u in used}
            log.append(f"inserted ours {i:2} after his slide {anchor:2} ('{head} Keys to the Game')")
        else:
            log.append(f"NO MATCH for ours {i:2} ({head[:60]}) - left out; add by hand if needed")
    dst.SaveAs(os.path.abspath(out_pptx))
    n_total = dst.Slides.Count
    dst.Close()
    return log, n_total


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--his-id", required=True, help="Corey's Slides file id (read-only export)")
    ap.add_argument("--ours", required=True, help="our episode pptx")
    ap.add_argument("--out", default=None, help="merged pptx path (default decks/<his export>_merged.pptx)")
    ap.add_argument("--create", default=None, metavar="NAME",
                    help="also upload the merged pptx as a NEW Slides file with this name (Lucas's Drive, unshared)")
    args = ap.parse_args()
    creds = get_credentials()
    his_pptx = os.path.join(HERE, "decks", f"corey_{args.his_id[:8]}_export.pptx")
    export_pptx(args.his_id, creds, his_pptx)
    print(f"exported Corey's deck (read-only) -> {os.path.relpath(his_pptx, HERE)}")
    out = args.out or os.path.join(HERE, "decks", os.path.basename(args.ours).replace(".pptx", "_merged.pptx"))
    log, n = merge(his_pptx, args.ours, out)
    for line in log:
        print("  " + line)
    print(f"merged deck: {os.path.relpath(out, HERE)} ({n} slides)")
    if args.create:
        meta = create(out, args.create, creds)
        print(f"created NEW Slides file '{meta['name']}' (id {meta['id']}) - unshared\n{meta.get('webViewLink')}")


if __name__ == "__main__":
    main()
