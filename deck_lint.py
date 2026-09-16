"""Deck lint: which facts appear on more than one slide?

Lucas (9/15, after Ep4): "I repeated a few of the same facts in a few slides
so I want to limit that and streamline it." This reads the episode pptx and
reports (a) text lines that appear on two or more slides and (b) stat
tokens - numbers like 795, 0.335, 41-of-45, 81% - that recur across slides,
with the slide numbers, so each fact can be given ONE slot before the deck
is pushed.

    python deck_lint.py                          # decks/2026_Week{WEEK}_Episode{EP}.pptx
    python deck_lint.py decks\\X.pptx --min 2
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

from pptx import Presentation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# boilerplate that legitimately repeats (labels, headers, footers)
BOILER = {
    "why it matters", "the number", "score prediction", "win probability (machine)",
    "machine · market", "coach", "qb", "roster", "rating", "δ pre", "voters",
    "our predictions", "★ superdog", "★ giant killer", "machine line · fair odds, no vig",
}
STAT = re.compile(r"(?<![\w.])(\d{1,3}(?:[.,]\d+)?%?|\d+-of-\d+|\d+–\d+|[+-]\d+(?:\.\d+)?)(?![\w.])")
SKIP_TOKENS = {"2026", "4", "3", "1", "2", "5", "10", "25"}   # episode/week/rank noise


def slide_texts(pptx):
    prs = Presentation(pptx)
    out = []
    for i, slide in enumerate(prs.slides, 1):
        lines = []
        for sh in slide.shapes:
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    t = "".join(r.text for r in p.runs).strip()
                    if t:
                        lines.append(t)
            if getattr(sh, "has_table", False) and sh.has_table:
                for row in sh.table.rows:
                    for cell in row.cells:
                        t = cell.text.strip()
                        if t:
                            lines.append(t)
        out.append((i, lines))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pptx", nargs="?", default=None)
    ap.add_argument("--min", type=int, default=2, help="report lines/tokens on >= this many slides")
    args = ap.parse_args()
    if args.pptx is None:
        from make_episode_deck import EPISODE, WEEK  # noqa - builds the deck on import; fine
        args.pptx = HERE / "decks" / f"2026_Week{WEEK}_Episode{EPISODE}.pptx"
    slides = slide_texts(args.pptx)

    # (a) whole lines repeated across slides
    where = defaultdict(set)
    for i, lines in slides:
        for t in lines:
            key = re.sub(r"\s+", " ", t).strip().lower()
            if len(key) < 12 or key in BOILER or key.startswith(("ep ", "episode ", "machine = our")):
                continue
            where[key].add(i)
    rep = sorted(((k, v) for k, v in where.items() if len(v) >= args.min), key=lambda kv: (-len(kv[1]), kv[0]))
    print(f"== lines on {args.min}+ slides ({len(rep)}) ==")
    for k, v in rep:
        print(f"  slides {sorted(v)}: {k[:100]}")

    # (b) stat tokens repeated across slides, with the line they sit in
    tok_where = defaultdict(lambda: defaultdict(set))
    for i, lines in slides:
        for t in lines:
            for m in STAT.findall(t):
                if m in SKIP_TOKENS or re.fullmatch(r"\d{1,2}", m):
                    continue
                tok_where[m][i].add(t[:80])
    reps = sorted(((tok, d) for tok, d in tok_where.items() if len(d) >= args.min),
                  key=lambda kv: (-len(kv[1]), kv[0]))
    print(f"\n== stat tokens on {args.min}+ slides ({len(reps)}) ==")
    for tok, d in reps:
        print(f"  {tok!s:>10}  slides {sorted(d)}")
        for i in sorted(d):
            for line in sorted(d[i])[:2]:
                print(f"             {i:2}: {line}")


if __name__ == "__main__":
    main()
