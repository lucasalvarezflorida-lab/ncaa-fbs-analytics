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
    lines nested under it, then "The number" with its children
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

    for ln in md.splitlines():
        if ln.startswith("|"):
            flush_para(); stack.clear()
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                tbl.append(cells)
            continue
        flush_tbl()
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
    flush_para(); flush_tbl()
    return title, body


# ---------------- tree -> OneNote XML ----------------

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<span style='font-weight:bold'>\1</span>", t)
    t = re.sub(r"`(.+?)`", r"<span style='font-family:Consolas'>\1</span>", t)
    t = re.sub(r"\[(.+?)\]\((https?://[^)]+)\)", r"<a href='\2'>\1</a>", t)
    return t.replace("]]>", "]]&gt;")


def T(t):
    return f"<one:T><![CDATA[{inline(t)}]]></one:T>"


def render(nodes):
    out = []
    for n in nodes:
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
    if not m:
        return
    head, tail = t[:m.start()].rstrip(), t[m.end():].strip()
    if len(tail) < 12:
        return
    node["text"] = head
    node["kids"] = [dict(text=tail[0].upper() + tail[1:], bullet=True, kids=[])]


def game_layout(game):
    """game = the top-level md node for one game -> (title, xml) in Lucas's layout."""
    header = game["text"].strip("*")
    title = header.split(" — ")[0].strip()
    read = number = corey = None
    keys = []
    for k in game["kids"]:
        t = k["text"]
        if t == "The read":
            read = k
        elif t.startswith("The number"):
            number = k
        elif t.startswith("Corey"):
            corey = k
        elif t.endswith(" keys"):
            keys.append(k)
    for kb in keys:
        for key in kb["kids"]:
            for why in key["kids"]:
                for ev in why["kids"]:
                    split_evidence(ev)
    recap = dict(text="Recap", bullet=True, kids=[])
    if read and read["kids"]:
        first = dict(read["kids"][0], kids=[dict(x, kids=[]) for x in read["kids"][1:]])
        recap["kids"].append(first)
    if number:
        recap["kids"].append(number)
    top = dict(text="**" + header + "**", bullet=True, kids=keys + [recap])
    if corey:
        top["kids"].append(dict(text=corey["text"], bullet=False, kids=[]))
    return title, page_xml(title, render([top]))


def game_pages(md):
    _, body = parse(md)
    return [game_layout(v) for kind, v in body if kind == "oe" and v["bullet"] and " — " in v["text"] and v["kids"]]


if __name__ == "__main__":
    if sys.argv[1] == "--games":
        src, outdir = sys.argv[2], sys.argv[3]
        os.makedirs(outdir, exist_ok=True)
        for title, xml in game_pages(open(src, encoding="utf-8").read()):
            fn = os.path.join(outdir, re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_") + ".xml")
            open(fn, "w", encoding="utf-8").write(xml)
            print(f"{title}\t{fn}")
    else:
        src, dst = sys.argv[1], sys.argv[2]
        title, xml = convert(open(src, encoding="utf-8").read())
        open(dst, "w", encoding="utf-8").write(xml)
        print(title)
