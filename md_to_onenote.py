"""Convert the outline notes (.md) into OneNote page XML.

  python md_to_onenote.py notes/week4_ep5_boards.md out.xml          # one page, as written
  python md_to_onenote.py --games notes/week4_ep5_games.md outdir/    # one page PER GAME, Lucas's layout

GAME LAYOUT (how Lucas formats a game page in OneNote, 2026-09-21):
  * header line bold, everything nested under it
  * the keys FIRST (away keys, then home keys); each key -> its Why line ->
    the evidence bullets; the "What X brings" / "The catch" / "Reserve" lines
    stay whole
  * an evidence line whose second clause is commentary ("... — the second-
    least explosive ...") or a breakdown ("...; 0-for-6 against Ohio State")
    is split: the second clause becomes its own sub-bullet, capitalised
  * the read moves to the END as "Recap": first read line, the other read
    lines nested under it, then "The number" with its children, then the
    "Availability" block when the notes carry one
  * (Lucas 9/29, copied from his hand-formatted Pitt page) a "Why:" / "What X
    brings:" line with several ';' clauses = headline + one sub-bullet per
    clause; an evidence line splits at ", <number>" too; the "Reserve" key and
    the "X as a team:" line are struck through
  * "Corey: ..." last, no bullet
Each XML has a {PAGE_ID} placeholder; onenote_push.ps1 fills it in. The .md
files stay the master copy - OneNote is a reading copy."""
import html, os, re, sys

NS = "http://schemas.microsoft.com/office/onenote/2013/onenote"


# ---------------- markdown -> tree ----------------

def parse(md):
    """-> (title, blocks); block = ("h", text) | ("table", rows) | ("oe", node);
    node = dict(text, bullet, kids)."""
    title, body, stack, tbl, para = "Notes", [], [], [], []

    def flush_para():
        if para:
            body.append(("oe", dict(text=" ".join(para), bullet=False, kids=[]))); para.clear()

    def flush_tbl():
        if tbl:
            body.append(("table", list(tbl))); tbl.clear()

    ntbl = []                      # an INDENTED table sits under the current bullet (dossiers, 9/25)

    def flush_ntbl():
        if ntbl:
            (stack[-1]["kids"] if stack else body).append(
                dict(text="", bullet=False, kids=[], table=list(ntbl)) if stack else ("table", list(ntbl)))
            ntbl.clear()

    for ln in md.splitlines():
        if ln.startswith("|"):
            flush_para(); flush_ntbl(); stack.clear()
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                tbl.append(cells)
            continue
        if ln.lstrip().startswith("|") and stack:
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                ntbl.append(cells)
            continue
        flush_tbl(); flush_ntbl()
        m = re.match(r"^(\s*)- (.*)$", ln)
        if m:
            flush_para()
            depth = len(m.group(1)) // 2
            node = dict(text=m.group(2), bullet=True, kids=[])
            while len(stack) > depth:
                stack.pop()
            (stack[-1]["kids"] if stack else body).append(node if stack else ("oe", node))
            stack.append(node)
            continue
        if ln.startswith("# "):
            title = ln[2:].strip(); continue
        if ln.startswith("## "):
            flush_para(); stack.clear(); body.append(("h", ln[3:].strip())); continue
        if not ln.strip():          # blank / spacing line: ends a paragraph, never the outline
            flush_para(); continue
        if stack and ln.startswith(" "):
            stack[-1]["text"] += " " + ln.strip(); continue
        stack.clear(); para.append(ln.strip())
    flush_para(); flush_tbl(); flush_ntbl()
    return title, body


# ---------------- tree -> OneNote XML ----------------

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<span style='font-weight:bold'>\1</span>", t)
    t = re.sub(r"~~(.+?)~~", r"<span style='text-decoration:line-through'>\1</span>", t)
    t = re.sub(r"`(.+?)`", r"<span style='font-family:Consolas'>\1</span>", t)
    t = re.sub(r"\[(.+?)\]\((https?://[^)]+)\)", r"<a href='\2'>\1</a>", t)
    return t.replace("]]>", "]]&gt;")


def T(t):
    return f"<one:T><![CDATA[{inline(t)}]]></one:T>"


def render(nodes):
    out = []
    for n in nodes:
        if n.get("table"):
            out.append(table(n["table"])); continue
        kids = f"<one:OEChildren>{render(n['kids'])}</one:OEChildren>" if n["kids"] else ""
        lst = '<one:List><one:Bullet bullet="2" fontSize="11.0"/></one:List>' if n["bullet"] else ""
        out.append(f"<one:OE>{lst}{T(n['text'])}{kids}</one:OE>")
    return "".join(out)


def table(rows):
    cols = max(len(r) for r in rows)
    x = ['<one:OE><one:Table bordersVisible="true"><one:Columns>'
         + "".join(f'<one:Column index="{i}" width="90"/>' for i in range(cols)) + "</one:Columns>"]
    for ri, r in enumerate(rows):
        x.append("<one:Row>" + "".join(
            f"<one:Cell><one:OEChildren><one:OE>{T(('**' + c + '**') if ri == 0 and c else c)}</one:OE></one:OEChildren></one:Cell>"
            for c in (r + [""] * (cols - len(r)))) + "</one:Row>")
    x.append("</one:Table></one:OE>")
    return "".join(x)


def page_xml(title, body_xml):
    title = os.environ.get("ONENOTE_TITLE_PREFIX", "") + title   # e.g. "Week 5 - " so pages accumulate week by week (Lucas 9/27)
    return (f'<?xml version="1.0"?><one:Page xmlns:one="{NS}" ID="{{PAGE_ID}}">'
            f"<one:Title><one:OE>{T(title)}</one:OE></one:Title>"
            f'<one:Outline><one:Size width="900" height="400"/><one:OEChildren>{body_xml}</one:OEChildren></one:Outline></one:Page>')


def convert(md):
    title, body = parse(md)
    parts = []
    for kind, v in body:
        if kind == "h":
            parts.append("<one:OE><one:T><![CDATA[<span style='font-weight:bold;font-size:14.0pt'>"
                         + html.escape(v, quote=False) + "</span>]]></one:T></one:OE>")
        elif kind == "table":
            parts.append(table(v))
        else:
            parts.append(render([v]))
    return title, page_xml(title, "".join(parts))


# ---------------- Lucas's game layout ----------------

LABEL = re.compile(r"^(Why|What .+? brings|What it faces|What he faces|What they face|The catch|The point|Reserve|How|Honesty|Series|Foreshadow)", re.I)


def split_evidence(node):
    """An evidence bullet: second clause after ' — ' (commentary) or '; <digit>'
    (a breakdown) becomes its own sub-bullet, capitalised. Labelled lines stay whole."""
    t = node["text"]
    if LABEL.match(t) or node["kids"]:
        return
    m = re.search(r" — (?=[a-z0-9])", t) or re.search(r"; (?=\d)", t)
    if not m and ":" not in t.split(",")[0] and len(t.split(",")[0].split()) >= 4:
        m = re.search(r", (?=\d)", t)
    if not m:
        return
    head, tail = t[:m.start()].rstrip(), t[m.end():].strip()
    if len(tail) < 12:
        return
    node["text"] = head
    node["kids"] = [dict(text=tail[0].upper() + tail[1:], bullet=True, kids=[])]


def split_label(node):
    """Lucas 9/29: a 'Why:' or 'What X brings:' line with several clauses is a headline
    plus one sub-bullet per further clause (split on '; '), ahead of the evidence."""
    t = node["text"]
    if not re.match(r"^(Why|What .+? brings)", t, re.I) or "; " not in t:
        return
    parts = [x.strip() for x in t.split("; ") if x.strip()]
    if len(parts) < 2 or any(len(x) < 12 for x in parts[1:]):
        return
    node["text"] = parts[0]
    node["kids"] = [dict(text=x[0].upper() + x[1:], bullet=True, kids=[]) for x in parts[1:]] + node["kids"]


STRIKE = re.compile(r"^(Reserve\b|[A-Z][\w.'()& -]+ as a team: )")


def strike_deemphasised(node):
    """Lucas 9/29: the 'Reserve' key and the 'X as a team:' line under a passer are struck through."""
    if STRIKE.match(node["text"]) and not node["text"].startswith("~~"):
        node["text"] = "~~" + node["text"] + "~~"
    for k in node["kids"]:
        strike_deemphasised(k)


def game_layout(game):
    """game = the top-level md node for one game -> (title, xml) in Lucas's layout."""
    header = game["text"].strip("*")
    title = header.split(" — ")[0].strip()
    read = number = corey = avail = None
    keys = []
    for k in game["kids"]:
        t = k["text"]
        if t == "The read":
            read = k
        elif t.startswith("The number"):
            number = k
        elif t.startswith("Availability"):
            avail = k
        elif t.startswith("Corey"):
            corey = k
        elif t.endswith(" keys"):
            keys.append(k)
    for kb in keys:
        for key in kb["kids"]:
            for why in key["kids"]:
                for ev in why["kids"]:
                    split_evidence(ev)
                split_label(why)
        strike_deemphasised(kb)
    recap = dict(text="Recap", bullet=True, kids=[])
    if read and read["kids"]:
        first = dict(read["kids"][0], kids=[dict(x, kids=[]) for x in read["kids"][1:]])
        recap["kids"].append(first)
    if number:
        recap["kids"].append(number)
    if avail:
        recap["kids"].append(avail)
    top = dict(text="**" + header + "**", bullet=True, kids=keys + [recap])
    if corey:
        top["kids"].append(dict(text=corey["text"], bullet=False, kids=[]))
    return title, page_xml(title, render([top]))


def game_pages(md):
    _, body = parse(md)
    return [game_layout(v) for kind, v in body if kind == "oe" and v["bullet"] and " — " in v["text"] and v["kids"]]


BOARD_PAGES = [   # Lucas 9/23: boards as ONE PAGE PER TOPIC; superdogs sit on the Recap page (as he did in Week 4)
    ("Recap", ("Receipts", "Superdog")),
    ("Top 25", ("Top 25", "The rating rule")),
    ("Heisman", ("Heisman",)),
    ("Hot Seat", ("Hot Seat",)),
]


def board_pages(md):
    """Split the boards file on its top-level topics into the four pages."""
    title, body = parse(md)
    pages = []
    for name, keys in BOARD_PAGES:
        parts = []
        for kind, v in body:
            if kind == "oe" and v["bullet"] and any(v["text"].lstrip("*").startswith(k) or ("**" + k) in v["text"][:len(k) + 3] for k in keys):
                parts.append(render([v]))
        if parts:
            pages.append((name, page_xml(name, "".join(parts))))
    return pages


if __name__ == "__main__":
    if sys.argv[1] == "--boards":
        src, outdir = sys.argv[2], sys.argv[3]
        os.makedirs(outdir, exist_ok=True)
        for title, xml in board_pages(open(src, encoding="utf-8").read()):
            fn = os.path.join(outdir, re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_") + ".xml")
            open(fn, "w", encoding="utf-8").write(xml)
            print(os.environ.get("ONENOTE_TITLE_PREFIX", "") + f"{title}	{fn}")
    elif sys.argv[1] == "--games":
        src, outdir = sys.argv[2], sys.argv[3]
        os.makedirs(outdir, exist_ok=True)
        for title, xml in game_pages(open(src, encoding="utf-8").read()):
            fn = os.path.join(outdir, re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_") + ".xml")
            open(fn, "w", encoding="utf-8").write(xml)
            print(os.environ.get("ONENOTE_TITLE_PREFIX", "") + f"{title}\t{fn}")
    else:
        src, dst = sys.argv[1], sys.argv[2]
        title, xml = convert(open(src, encoding="utf-8").read())
        open(dst, "w", encoding="utf-8").write(xml)
        print(os.environ.get("ONENOTE_TITLE_PREFIX", "") + title)
