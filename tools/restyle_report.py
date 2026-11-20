#!/usr/bin/env python3
"""Restyles a Lap CoPilot driver report PDF in the Starman brand hub styling.

Usage: python3 tools/restyle_report.py <report.pdf> [out.pdf]

Nothing is redrawn by hand. Every table value, chart line, map tile and sentence is read from
the source PDF and put back in the same place; only the skin changes (dark pages, hub fonts,
carbon panels, the telemetry line and grid rules, lap colours in the hub's default order).
Build files land in reports/<name>/ next to the hub (not deployed).
"""
import base64, html, io, re, subprocess, sys
from pathlib import Path

import fitz
from PIL import Image

HERE = Path(__file__).resolve().parent
HUB = HERE.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
S = 4 / 3  # pt -> css px

LAP_DEFAULTS = ["#3fe08f", "#ff5a4d", "#f4f3ee", "#5fb4ff", "#46e0e6", "#ff6fb5", "#ffb347", "#b48cff"]
MOON, HAZE, INK, SKY = "#f4f3ee", "#8d8e9b", "#08080c", "#6c8aff"
TRACK = (1.0, 0.83, 0.0)      # reference line on the track map
BEST_ALL = (0.71, 0.1, 1.0)   # purple cell: best of all drivers
BEST_OWN = (0.0, 0.93, 0.0)   # green cell: the driver's own best
HEAD_FILL = (0.64, 0.64, 0.68)


def near(a, b, tol=0.02):
    return a is not None and b is not None and all(abs(x - y) <= tol for x, y in zip(a, b))


def is_gray(c):
    return c is not None and max(c) - min(c) < 0.03


def saturated(c):
    return c is not None and max(c) - min(c) > 0.4


def esc(t):
    return html.escape(t, quote=False)


def px(v):
    return f"{v * S:.2f}px"


class Line:
    def __init__(self, l):
        self.bbox = fitz.Rect(l["bbox"])
        self.rot = abs(l["dir"][0]) < 0.5
        self.spans = [s for s in l["spans"] if s["text"]]
        self.text = "".join(s["text"] for s in self.spans)
        s0 = self.spans[0]
        self.font, self.size, self.color = s0["font"], s0["size"], s0["color"]
        self.bold = all("Bold" in s["font"] or "Black" in s["font"] for s in self.spans if s["text"].strip())
        self.cx, self.cy = (self.bbox.x0 + self.bbox.x1) / 2, (self.bbox.y0 + self.bbox.y1) / 2


def page_lines(page):
    out, blocks = [], []
    for b in page.get_text("dict")["blocks"]:
        if b["type"]:
            continue
        ls = [Line(l) for l in b["lines"] if "".join(s["text"] for s in l["spans"]).strip()]
        ls = [l for l in ls if l.font != "Unnamed-T3"]  # outline copy of the map labels
        if ls:
            blocks.append(ls)
            out += ls
    return out, blocks


def path_d(items):
    d, last = [], None
    f = lambda p: f"{p.x:.2f} {p.y:.2f}"
    for it in items:
        k = it[0]
        if k == "l":
            a, b = it[1], it[2]
            if last is None or abs(a.x - last.x) > 0.01 or abs(a.y - last.y) > 0.01:
                d.append("M" + f(a))
            d.append("L" + f(b)); last = b
        elif k == "c":
            a, b, c, e = it[1:5]
            if last is None or abs(a.x - last.x) > 0.01 or abs(a.y - last.y) > 0.01:
                d.append("M" + f(a))
            d.append(f"C{f(b)} {f(c)} {f(e)}"); last = e
        elif k == "re":
            r = it[1]
            d.append(f"M{r.x0:.2f} {r.y0:.2f}H{r.x1:.2f}V{r.y1:.2f}H{r.x0:.2f}Z"); last = None
        elif k == "qu":
            q = it[1]
            d.append(f"M{f(q.ul)}L{f(q.ur)}L{f(q.lr)}L{f(q.ll)}Z"); last = None
    return "".join(d)


class Report:
    def __init__(self, src, out):
        self.src, self.out = Path(src), Path(out)
        self.doc = fitz.open(src)
        self.work = HUB / "reports" / re.sub(r"[^\w.-]+", "-", self.src.stem).strip("-")
        (self.work / "img").mkdir(parents=True, exist_ok=True)
        self.lapmap = {}
        self.find_laps()

    # ── lap colours: first driver green, second red, … (hub default order) ──
    def find_laps(self):
        found = []
        def add(c):
            if saturated(c) and not near(c, TRACK) and not near(c, BEST_ALL) and not near(c, BEST_OWN) \
               and not near(c, (0.84, 0.0, 0.11)) and not any(near(c, f) for f in found):
                found.append(c)
        tables_first, strokes = [], []
        for page in self.doc:
            for x in page.get_drawings():
                r = x["rect"]
                if x["type"] == "f" and r.height > 15 and r.width > 30 and r.y0 > 60:
                    tables_first.append(x["fill"])      # coloured driver cells, in row order
                elif x.get("color"):
                    strokes.append(x["color"])
        for c in tables_first + strokes:
            add(c)
        for i, c in enumerate(found):
            self.lapmap[tuple(round(v, 2) for v in c)] = LAP_DEFAULTS[i % len(LAP_DEFAULTS)]

    def lap(self, c):
        if c is None:
            return None
        for k, v in self.lapmap.items():
            if near(c, k):
                return v
        return None

    # ── vector panels ──
    def colour(self, c, kind):
        """Map a source colour to the hub. kind: 'stroke' | 'fill'."""
        if c is None:
            return None
        lp = self.lap(c)
        if lp:
            return lp
        if near(c, TRACK):
            return MOON
        if is_gray(c):
            v = c[0]
            if v < 0.05:
                return None if kind == "fill" else INK
            if v < 0.16:
                return "rgba(255,255,255,.07)"
            if v < 0.3:
                return "rgba(255,255,255,.16)"
            if v < 0.6:
                return "rgba(255,255,255,.16)"
            return MOON
        return MOON

    def svg_text(self, lines, drawings):
        out = []
        horiz = [l for l in lines if not l.rot]
        numeric = lambda t: re.fullmatch(r"[-+−]?[\d.,]+(-\d+)?", t.strip()) is not None
        for l in lines:
            t = l.text.strip()
            b = l.bbox
            if l.rot:
                out.append(f'<text class="t-lab" font-size="{l.size * .97:.2f}" text-anchor="middle" '
                           f'transform="translate({b.x1 - l.size * .28:.2f} {l.cy:.2f}) rotate(-90)">{esc(t)}</text>')
                continue
            base = b.y1 - (b.y1 - b.y0) * 0.235
            if numeric(t):
                row = [o for o in horiz if o is not l and numeric(o.text) and abs(o.bbox.y0 - b.y0) < 0.5]
                if row:
                    out.append(f'<text class="t-num" font-size="{l.size * .9:.2f}" text-anchor="middle" x="{l.cx:.2f}" y="{base:.2f}">{esc(t)}</text>')
                else:
                    out.append(f'<text class="t-num" font-size="{l.size * .9:.2f}" text-anchor="end" x="{b.x1:.2f}" y="{base:.2f}">{esc(t)}</text>')
                continue
            cls = "t-b" if l.bold or l.color == 0xFFFFFF else ("t-dim" if l.color == 0x999999 else "t-lab")
            if l.size < 6:
                cls = "t-att"
            swatch = any(self.lap(x.get("color") or x.get("fill")) and x["rect"].height < 4
                         and -1 < b.x0 - x["rect"].x1 < 8 and b.y0 - 2 < (x["rect"].y0 + x["rect"].y1) / 2 < b.y1 + 2
                         for x in drawings)
            others = [o for o in horiz if o is not l and not numeric(o.text)]
            if swatch or any(abs(o.bbox.x0 - b.x0) < 0.3 for o in others):
                anchor, x = "start", b.x0
            elif any(abs(o.cx - l.cx) < 1 and abs(o.cy - l.cy) < 14 for o in others):
                anchor, x = "middle", l.cx
            elif l.bold:
                anchor, x = "start", b.x0
            elif l.size < 6:
                anchor, x = "end", b.x1
            else:
                anchor, x = "middle", l.cx
            out.append(f'<text class="{cls}" font-size="{l.size * .96:.2f}" text-anchor="{anchor}" x="{x:.2f}" y="{base:.2f}">{esc(t)}</text>')
        return "".join(out)

    def svg_paths(self, drawings, rect, on_map=False):
        out = []
        inner = [x["rect"] for x in drawings if x["type"] == "f" and near(x["fill"], (0, 0, 0)) and x["rect"].width > 100
                 and x["rect"].height > 20 and x["rect"] != rect]
        # hairline between stacked channels of one graph
        for r in inner:
            if any(abs(o.y0 - r.y1) < 0.1 and abs(o.x0 - r.x0) < 0.1 for o in inner):
                out.append(f'<path d="M{r.x0:.2f} {r.y1:.2f}H{r.x1:.2f}" stroke="rgba(255,255,255,.1)" stroke-width=".75"/>')
        for x in drawings:
            r = x["rect"]
            fill, col = x.get("fill"), x.get("color")
            if x["type"] == "f" and (near(fill, (0, 0, 0)) or near(fill, (0.13, 0.13, 0.13))) and r.width > 100 and r.height > 20:
                continue  # panel / channel / map backgrounds
            d = path_d(x["items"])
            if not d:
                continue
            a = []
            if on_map and x["type"] == "f" and near(fill, (1, 1, 1)):      # legend box on the map
                out.append(f'<rect x="{r.x0:.2f}" y="{r.y0:.2f}" width="{r.width:.2f}" height="{r.height:.2f}" rx="5" '
                           f'fill="rgba(19,19,24,.86)" stroke="rgba(255,255,255,.2)" stroke-width=".75"/>')
                continue
            if on_map and x["type"] == "fs":                                # split markers
                out.append(f'<path d="{d}" fill="{MOON}" stroke="{INK}" stroke-width="1.1"/>')
                continue
            if fill is not None and x["type"] in ("f", "fs"):
                f = self.colour(fill, "fill")
                if f is None:
                    continue
                a.append(f'fill="{f}"')
            else:
                a.append('fill="none"')
            if col is not None and x["type"] in ("s", "fs"):
                w = x.get("width") or 0.75
                c = self.colour(col, "stroke")
                if self.lap(col) or near(col, TRACK):
                    w = 1.125 if w < 1.2 else w     # 1.5px: the hub's line weight for PDF exports
                    if on_map:
                        w = max(w, 1.5)
                a.append(f'stroke="{c}" stroke-width="{w:.3f}" stroke-linejoin="bevel"')
            out.append(f'<path d="{d}" {" ".join(a)}/>')
        return "".join(out)

    def panel(self, n, rect, drawings, lines):
        dr = [x for x in drawings if rect.contains(x["rect"]) or rect.intersects(x["rect"]) and x["rect"] in rect]
        ls = [l for l in lines if l.bbox.intersects(rect) and rect.contains(fitz.Point(l.cx, l.cy))]
        body = self.svg_paths(dr, rect) + self.svg_text(ls, dr)
        return (f'<svg class="panel" style="left:{px(rect.x0)};top:{px(rect.y0)};width:{px(rect.width)};height:{px(rect.height)}" '
                f'viewBox="{rect.x0:.2f} {rect.y0:.2f} {rect.width:.2f} {rect.height:.2f}">{body}</svg>'), ls

    # ── satellite maps ──
    def mosaic(self, n, k, rect, tiles):
        w = tiles[0]["bbox"][2] - tiles[0]["bbox"][0]
        sc = 256 / w
        im = Image.new("RGB", (round(rect.width * sc), round(rect.height * sc)), (34, 34, 34))
        for t in tiles:
            b = t["bbox"]
            pm = fitz.Pixmap(self.doc, t["xref"])
            if pm.n - pm.alpha > 3:
                pm = fitz.Pixmap(fitz.csRGB, pm)
            tile = Image.open(io.BytesIO(pm.tobytes("png"))).convert("RGB")
            x0, y0 = round((b[0] - rect.x0) * sc), round((b[1] - rect.y0) * sc)
            x1, y1 = round((b[2] - rect.x0) * sc), round((b[3] - rect.y0) * sc)
            if x1 <= 0 or y1 <= 0 or x0 >= im.width or y0 >= im.height:
                continue
            im.paste(tile.resize((x1 - x0, y1 - y0), Image.LANCZOS) if (x1 - x0, y1 - y0) != tile.size else tile, (x0, y0))
        fn = f"img/p{n + 1:02d}-map{k + 1}.jpg"
        im.save(self.work / fn, quality=90)
        return fn

    def tile_groups(self, page):
        groups = []
        for t in page.get_image_info(xrefs=True):
            b = t["bbox"]; w = b[2] - b[0]
            g = groups[-1] if groups else None
            ok = False
            if g:
                b0 = g[0]["bbox"]; w0 = b0[2] - b0[0]
                pitch = g[1]["bbox"][1] - b0[1] if len(g) > 1 and abs(g[1]["bbox"][0] - b0[0]) < 0.5 else w0
                fx, fy = (b[0] - b0[0]) / pitch, (b[1] - b0[1]) / pitch
                ok = abs(w - w0) < 0.3 and abs(fx - round(fx)) < 0.03 and abs(fy - round(fy)) < 0.03
            if ok:
                g.append(t)
            else:
                groups.append([t])
        return groups

    def map_panel(self, n, k, rect, groups, drawings, lines):
        def cover(g):
            u = fitz.Rect(g[0]["bbox"])
            for t in g:
                u |= fitz.Rect(t["bbox"])
            i = u & rect
            return 0 if i.is_empty else i.width * i.height
        g = max(groups, key=cover)
        fn = self.mosaic(n, k, rect, g)
        dr = [x for x in drawings if x["rect"] in rect and not (x["type"] == "f" and x["rect"].width > 300)]
        ls = [l for l in lines if rect.contains(fitz.Point(l.cx, l.cy))]
        cid = f"c{n}-{k}"
        body = (f'<clipPath id="{cid}"><rect x="{rect.x0}" y="{rect.y0}" width="{rect.width}" height="{rect.height}" rx="13.5"/></clipPath>'
                f'<g clip-path="url(#{cid})"><image href="{fn}" x="{rect.x0}" y="{rect.y0}" width="{rect.width}" height="{rect.height}" preserveAspectRatio="none"/>'
                f'<rect x="{rect.x0}" y="{rect.y0}" width="{rect.width}" height="{rect.height}" fill="rgba(8,8,12,.2)"/>'
                + self.svg_paths(dr, rect, on_map=True) + "</g>")
        for l in ls:
            b = l.bbox; t = esc(l.text.strip()); base = b.y1 - (b.y1 - b.y0) * 0.235
            if l.size < 6:
                body += f'<text class="t-att" font-size="{l.size:.2f}" text-anchor="end" x="{b.x1:.2f}" y="{base:.2f}">{t}</text>'
            elif l.bold:
                body += f'<text class="t-pin" font-size="{l.size * .92:.2f}" x="{b.x0:.2f}" y="{base:.2f}">{t}</text>'
            else:
                body += f'<text class="t-b" font-size="{l.size * .96:.2f}" x="{b.x0:.2f}" y="{base:.2f}">{t}</text>'
        body += f'<rect x="{rect.x0 + .375}" y="{rect.y0 + .375}" width="{rect.width - .75}" height="{rect.height - .75}" rx="13.2" fill="none" stroke="rgba(255,255,255,.1)" stroke-width=".75"/>'
        return (f'<svg class="map" style="left:{px(rect.x0)};top:{px(rect.y0)};width:{px(rect.width)};height:{px(rect.height)}" '
                f'viewBox="{rect.x0:.2f} {rect.y0:.2f} {rect.width:.2f} {rect.height:.2f}">{body}</svg>'), ls

    # ── tables ──
    def table(self, drawings, lines, busy):
        thin = [x["rect"] for x in drawings if x["type"] == "f" and near(x["fill"], (0, 0, 0))
                and (x["rect"].width < 1.2 or x["rect"].height < 1.2) and not any(x["rect"] in b for b in busy)]
        if len(thin) < 6:
            return "", [], False
        def edges(vals):
            out = []
            for v in sorted(vals):
                if not out or v - out[-1] > 1.5:
                    out.append(v)
            return out
        xs = edges([r.x0 for r in thin if r.width < 1.2])
        ys = edges([r.y0 for r in thin if r.height < 1.2])
        box = fitz.Rect(xs[0], ys[0], xs[-1] + 0.75, ys[-1] + 0.75)
        nr, nc = len(ys) - 1, len(xs) - 1
        idx = lambda v, e: max(0, min(len(e) - 2, max(i for i in range(len(e)) if e[i] <= v + 0.01)))
        cells = [[{"t": [], "cls": [], "style": ""} for _ in range(nc)] for _ in range(nr)]
        used = []
        for l in lines:
            if box.contains(fitz.Point(l.cx, l.cy)):
                c = cells[idx(l.cy, ys)][idx(l.cx, xs)]
                c["t"].append(l.text.strip()); c["bold"] = l.bold; c["size"] = l.size
                used.append(l)
        legend = set()
        for x in drawings:
            f, r = x.get("fill"), x["rect"]
            if x["type"] != "f" or f is None or r.width < 5 or r.height < 5 or not box.contains(fitz.Point((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)):
                continue
            c = cells[idx((r.y0 + r.y1) / 2, ys)][idx((r.x0 + r.x1) / 2, xs)]
            if near(f, BEST_ALL):
                c["cls"].append("best-all"); legend.add("all")
            elif near(f, BEST_OWN):
                c["cls"].append("best-own"); legend.add("own")
            elif self.lap(f):
                c["lap"] = self.lap(f)
            elif near(f, HEAD_FILL):
                c["head"] = True
        size = max((c.get("size", 0) for row in cells for c in row), default=11)
        out = [f'<div class="tbl" style="left:{px(box.x0)};top:{px(box.y0)};width:{px(box.width)};height:{px(box.height)};'
               f'font-size:{size * S * .9:.2f}px;grid-template-columns:{" ".join(px(xs[i + 1] - xs[i]) for i in range(nc))};'
               f'grid-template-rows:{" ".join(px(ys[i + 1] - ys[i]) for i in range(nr))}">']
        for ri, row in enumerate(cells):
            head = ri == 0 and all(c.get("bold") or c.get("head") for c in row if c["t"])
            ci = 0
            while ci < nc:
                c = row[ci]; span = 1
                if ci == 0 and not c["t"]:                 # label row: merge the empty lead cells
                    while ci + span < nc and not row[ci + span - 1]["t"]:
                        span += 1
                    c = row[ci + span - 1]
                    c["cls"].append("label")
                cls = ["c"] + c["cls"]
                if head:
                    cls.append("hd")
                elif c.get("bold"):
                    cls.append("b")
                if ri:
                    cls.append("line")
                t = esc(" ".join(c["t"]))
                if re.fullmatch(r"[-+−]?[\d.:]+", " ".join(c["t"])) or re.fullmatch(r"[\d, ]+", " ".join(c["t"])):
                    cls.append("num")
                inner = f'<span>{t}</span>'
                if c.get("lap"):
                    inner = f'<span><i style="background:{c["lap"]}"></i>{t}</span>'
                out.append(f'<div class="{" ".join(cls)}" style="grid-column:{ci + 1}/span {span}">{inner}</div>')
                ci += span
        out.append("</div>")
        if legend:
            lg = []
            if "all" in legend:
                lg.append('<span><i class="k-all"></i>Best of all drivers</span>')
            if "own" in legend:
                lg.append('<span><i class="k-own"></i>Driver\'s own best</span>')
            out.append(f'<div class="key" style="left:{px(box.x0 + 3)};top:{px(box.y1 + 9)}">{"".join(lg)}</div>')
        return "".join(out), used, True

    # ── free text ──
    def text_blocks(self, blocks, skip):
        out = []
        for ls in blocks:
            ls = [l for l in ls if l not in skip]
            if not ls:
                continue
            x0, y0 = min(l.bbox.x0 for l in ls), min(l.bbox.y0 for l in ls)
            x1 = max(l.bbox.x1 for l in ls)
            size = ls[0].size
            if len(ls) == 1 and ls[0].bold and size > 11:
                out.append(f'<h3 style="left:{px(x0)};top:{px(y0 - 1.5)}">{esc(ls[0].text.strip())}</h3>')
                continue
            parts = []
            for l in ls:
                for s in l.spans:
                    t = esc(s["text"])
                    parts.append(f"<b>{t}</b>" if "Bold" in s["font"] else t)
                parts.append(" ")
            pitch = (ls[-1].bbox.y0 - ls[0].bbox.y0) / (len(ls) - 1) if len(ls) > 1 else size * 1.4
            note = " note" if ls[0].color == 0x444444 else ""
            width = f"width:{px(x1 - x0 + 4)};" if len(ls) > 1 else "white-space:nowrap;"
            out.append(f'<p class="txt{note}" style="left:{px(x0)};top:{px(y0)};{width}font-size:{size * S * .97:.2f}px;'
                       f'line-height:{pitch * S:.2f}px">{"".join(parts).strip()}</p>')
        return "".join(out)

    # ── page ──
    def page(self, n):
        page = self.doc[n]
        lines, blocks = page_lines(page)
        drawings = page.get_drawings()
        skip, body = [], []
        title = next(l for l in lines if "Black" in l.font and l.size > 20)
        brand = next((l for l in lines if "Black" in l.font and l.size < 20), None)
        foot = [l for l in lines if l.bbox.y0 > 515]
        skip += [title, brand] + foot

        maps = [x["rect"] for x in drawings if x["type"] == "f" and near(x["fill"], (0.13, 0.13, 0.13)) and x["rect"].width > 100]
        blacks = [x["rect"] for x in drawings if x["type"] == "f" and near(x["fill"], (0, 0, 0)) and x["rect"].width > 100 and x["rect"].height > 20]
        panels = [r for r in blacks if not any(o != r and r in o for o in blacks)]
        if maps:
            groups = self.tile_groups(page)
            for k, r in enumerate(maps):
                h, used = self.map_panel(n, k, r, groups, drawings, lines)
                body.append(h); skip += used
        for r in panels:
            h, used = self.panel(n, r, drawings, lines)
            body.append(h); skip += used
        h, used, _ = self.table(drawings, lines, maps + panels)
        body.append(h); skip += used
        body.append(self.text_blocks(blocks, skip))

        parts = [p.strip() for p in title.text.split(" – ")]
        if len(parts) > 1 and re.fullmatch(r"[A-Z]{1,3}\d+", parts[0]):
            head = f'<span class="tag on">{esc(parts[0])}</span><h1>{esc(" – ".join(parts[1:]))}</h1>'
        else:
            head = f'<h1>{esc(parts[0])}</h1>' + "".join(f'<span class="tag">{esc(p)}</span>' for p in parts[1:])
        fl = sorted(foot, key=lambda l: l.bbox.x0)
        left = esc(fl[0].text.strip()) if fl else ""
        num = esc(fl[-1].text.strip()) if len(fl) > 1 else str(n + 1)
        name = esc(re.sub(r"\s+", "", brand.text).replace("LAPCOPILOT", "lap copilot")) if brand else ""
        if brand:
            name = "lap copilot" if re.sub(r"\s+", "", brand.text) == "LAPCOPILOT" else esc(re.sub(r"(?<=\S) (?=\S)", "", brand.text))
        return (f'<section class="page"><header>{head}<div class="brand"><img src="mark.svg" alt="">{name}</div></header>'
                f'{"".join(body)}<footer><span>{left}</span><span>{num}</span></footer></section>')

    def build(self):
        (self.work / "mark.svg").write_text((HUB / "assets/starman-mark-sun.svg").read_text())
        pages = "".join(self.page(n) for n in range(len(self.doc)))
        title = esc(self.doc.metadata.get("title") or self.src.stem)
        fonts = HERE / "report-fonts"
        css = CSS.replace("FONTS", fonts.as_uri()).replace("HUBFONTS", (HUB / "fonts").as_uri())
        doc = f'<!doctype html><html lang="en"><meta charset="utf-8"><title>{title}</title><style>{css}</style><body>{pages}</body></html>'
        (self.work / "report.html").write_text(doc)
        self.out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=20000",
                        f"--print-to-pdf={self.out}", (self.work / "report.html").as_uri()],
                       check=True, capture_output=True)
        return self.out


CSS = """
@font-face { font-family: "Anxler"; src: url("HUBFONTS/anxler.otf") format("opentype"); font-weight: 400; }
@font-face { font-family: "Hanken Grotesk"; src: url("FONTS/HankenGrotesk-300-500.woff2") format("woff2"); font-weight: 300 500; }
@font-face { font-family: "IBM Plex Mono"; src: url("FONTS/IBMPlexMono-400.woff2") format("woff2"); font-weight: 400; }
@font-face { font-family: "IBM Plex Mono"; src: url("FONTS/IBMPlexMono-500.woff2") format("woff2"); font-weight: 500; }
:root { --display: "Anxler", "Hanken Grotesk", sans-serif; --sans: "Hanken Grotesk", "Helvetica Neue", Arial, sans-serif; --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  --void: #08080c; --carbon: #131318; --graphite: #23232c; --haze: #8d8e9b; --moon: #f4f3ee; --electric: #2947ff; --sky: #6c8aff; --line: rgba(255,255,255,.1); }
@page { size: 1280px 720px; margin: 0; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html, body { margin: 0; background: var(--void); }
.page { position: relative; width: 1280px; height: 720px; overflow: hidden; page-break-after: always; break-after: page; color: var(--moon);
  font-family: var(--sans); font-weight: 400; -webkit-font-smoothing: antialiased;
  background: radial-gradient(760px 420px at 92% -12%, rgba(41,71,255,.26), transparent 64%), var(--void); }
.page > * { position: absolute; margin: 0; }
header { left: 24px; right: 24px; top: 22px; height: 52px; display: flex; align-items: center; gap: 14px; }
h1 { margin: 0; font: 400 34px/1 var(--display); letter-spacing: -.02em; text-transform: lowercase; white-space: nowrap; }
.tag { padding: 7px 13px 6px; border-radius: 999px; border: 1px solid rgba(255,255,255,.2); background: rgba(255,255,255,.08);
  font: 500 12px/1 var(--mono); letter-spacing: .12em; text-transform: uppercase; white-space: nowrap; }
.tag.on { background: var(--moon); color: var(--void); border-color: var(--moon); }
.brand { margin-left: auto; display: flex; align-items: center; gap: 4px; font: 400 21px/1 var(--display); letter-spacing: -.01em; text-transform: lowercase; }
.brand img { height: 30px; margin: 0 -2px 0 0; }
footer { left: 24px; right: 24px; bottom: 0; height: 30px; border-top: 1px solid var(--line); display: flex; align-items: center; justify-content: space-between;
  font: 500 10.5px/1 var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--haze); }
footer span:last-child { color: var(--moon); }
svg.panel { background: var(--carbon); border: 1px solid var(--line); border-radius: 18px; overflow: hidden; }
svg.map { overflow: hidden; }
svg text { font-family: var(--sans); fill: #cfcfd4; }
svg .t-num { font-family: var(--mono); fill: var(--haze); }
svg .t-b { fill: var(--moon); font-weight: 500; }
svg .t-dim { fill: var(--haze); }
svg .t-att { fill: rgba(244,243,238,.82); }
svg .t-pin { font-family: var(--mono); font-weight: 500; fill: var(--moon); stroke: var(--void); stroke-width: 2.4px; paint-order: stroke; stroke-linejoin: round; }
.tbl { display: grid; background: var(--carbon); border: 1px solid var(--line); border-radius: 18px; overflow: hidden; font-variant-numeric: tabular-nums; }
.tbl .c { display: flex; align-items: center; justify-content: center; min-width: 0; white-space: nowrap; }
.tbl .c.line { border-top: 1px solid var(--line); }
.tbl .c.num { font-family: var(--mono); font-size: .93em; }
.tbl .c.hd { color: var(--haze); font: 500 .74em/1 var(--sans); letter-spacing: .08em; text-transform: uppercase; }
.tbl .c.b { font-weight: 500; }
.tbl .c.label { justify-content: flex-end; padding-right: 14px; color: var(--haze); font: 400 .78em/1 var(--sans); }
.tbl .c > span { display: inline-flex; align-items: center; gap: .55em; padding: .22em .75em; border-radius: 999px; }
.tbl .c > span > i { width: .62em; height: .62em; border-radius: .16em; flex: none; }
.tbl .best-all > span { background: var(--moon); color: var(--void); font-weight: 500; }
.tbl .best-own > span { box-shadow: inset 0 0 0 1.5px var(--sky); }
.key { display: flex; gap: 22px; font: 500 10.5px/1 var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--haze); }
.key span { display: flex; align-items: center; gap: 8px; }
.key i { width: 22px; height: 11px; border-radius: 999px; }
.key .k-all { background: var(--moon); } .key .k-own { box-shadow: inset 0 0 0 1.5px var(--sky); }
h3 { font: 400 21px/1 var(--display); letter-spacing: -.01em; text-transform: lowercase; white-space: nowrap; }
.txt { color: rgba(244,243,238,.74); font-weight: 400; }
.txt b { color: var(--moon); font-weight: 500; }
.txt.note { color: var(--haze); }
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1]).expanduser()
    out = Path(sys.argv[2]).expanduser() if len(sys.argv) > 2 else src.with_name(src.stem + " (starman).pdf")
    print(Report(src, out).build())
