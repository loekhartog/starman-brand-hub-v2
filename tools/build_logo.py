#!/usr/bin/env python3
"""Single source for the v2 Starman mark: a wide tile with a sharp star cut out of its bottom edge.
The star is never drawn; it is the opening in the tile.

Running it regenerates
  assets/starman-mark.svg         colour mark: blue gradient tile, star cut out
  assets/starman-mark-sun.svg     sun mark: yellow with glow, for dark backgrounds
  assets/starman-mono-white.svg   one colour (white)
  assets/starman-avatar.png       square avatar master, 1024px: sun mark on the night field
  assets/favicon-180.png          the avatar at 180px (touch icon)
  assets/favicon-64.png           the colour mark on a transparent square (browser tab)
and the <symbol id="sm-light"> / <symbol id="sm-sun"> definitions in index.html.
Usage: python3 tools/build_logo.py
"""
import math, os, re
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- geometry, 148 x 100 box, y down ---------------------------------------
W, H = 148, 100
# (x, y, corner radius). One closed outline: the tile, with the star taken out of its bottom edge.
TIP, ARM, PIT, LEG, FOOT, CORNER = 2.6, 2.6, 1.4, 1.4, 3.0, 4.5
MARK = [
    (0, 0, CORNER), (W, 0, CORNER),
    (W, 100, FOOT),              # right foot: the star's leg runs into the corner
    (104.5, 77.5, LEG),
    (128.5, 40.5, ARM),          # right arm
    (86, 55, PIT),
    (74, 14.5, TIP),             # head
    (62, 55, PIT),
    (19.5, 40.5, ARM),           # left arm
    (43.5, 77.5, LEG),
    (0, 100, FOOT),              # left foot
]


def _unit(ax, ay, bx, by):
    d = math.hypot(bx - ax, by - ay)
    return (bx - ax) / d, (by - ay) / d, d


def rounded(pts):
    """-> list of segments ('M'|'L'|'Q', coords) with every corner eased by its radius."""
    n, out = len(pts), []
    for i, (x, y, r) in enumerate(pts):
        px, py, _ = pts[i - 1]
        nx, ny, _ = pts[(i + 1) % n]
        ux, uy, d1 = _unit(x, y, px, py)
        vx, vy, d2 = _unit(x, y, nx, ny)
        if r <= 0:
            out.append(('L', (x, y)))
            continue
        # distance from the corner at which a circle of radius r touches both edges
        half = math.acos(max(-1, min(1, ux * vx + uy * vy))) / 2
        t = min(r / math.tan(half), d1 * .45, d2 * .45)
        out.append(('L', (x + ux * t, y + uy * t)))
        out.append(('Q', (x, y, x + vx * t, y + vy * t)))
    out[0] = ('M', out[0][1])
    return out


def path_d(pts, scale=1.0, dx=0.0, dy=0.0):
    f = lambda v, o: ('%.2f' % (v * scale + o)).rstrip('0').rstrip('.')
    parts = []
    for cmd, c in rounded(pts):
        xy = [f(c[i], dx if i % 2 == 0 else dy) for i in range(len(c))]
        parts.append(cmd + ' '.join(xy))
    return ''.join(parts) + 'Z'


def flatten(pts, scale, dx=0.0, dy=0.0, steps=14):
    out, cur = [], None
    for cmd, c in rounded(pts):
        if cmd in 'ML':
            cur = (c[0], c[1]); out.append(cur)
        else:
            x0, y0 = cur; cx, cy, x1, y1 = c
            for s in range(1, steps + 1):
                t = s / steps
                out.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1,
                            (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1))
            cur = (x1, y1)
    return [(x * scale + dx, y * scale + dy) for x, y in out]


# ---- colours ---------------------------------------------------------------
SUN = [(0, '#fefa54'), (.2, '#fef760'), (.46, '#fff899'), (.75, '#fffbcb'), (1, '#fffcda')]
BLUE = [(0, '#1828d6'), (.5, '#2947ff'), (1, '#6c8aff')]          # colour mark
NIGHT = [(0, '#05061a'), (.62, '#1828d6'), (1, '#6c8aff')]        # avatar field


def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def gradient(size, stops, y0=0.0, y1=1.0):
    """Vertical gradient image; y0..y1 are the fractions of the height the stops span."""
    col = Image.new('RGB', (1, size))
    for y in range(size):
        t = min(1, max(0, (y / (size - 1) - y0) / (y1 - y0)))
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if t <= b:
                k = 0 if b == a else (t - a) / (b - a)
                ca, cb = _rgb(ca), _rgb(cb)
                col.putpixel((0, y), tuple(round(ca[i] + (cb[i] - ca[i]) * k) for i in range(3)))
                break
    return col.resize((size, size))


# ---- SVG -------------------------------------------------------------------
def stops(st):
    return ''.join('<stop offset="%s" stop-color="%s"/>' % (('%g' % o).lstrip('0') or '0', c) for o, c in st)


def lin(gid, st):
    return '<linearGradient id="%s" x1="0" y1="0" x2="0" y2="1">%s</linearGradient>' % (gid, stops(st))


def write_svgs():
    d = path_d(MARK)
    A = os.path.join(HERE, 'assets')
    vb = 'viewBox="0 0 %d %d"' % (W, H)
    open(os.path.join(A, 'starman-mark.svg'), 'w').write(
        '<svg xmlns="http://www.w3.org/2000/svg" %s>%s<path fill="url(#mB)" d="%s"/></svg>\n' % (vb, lin('mB', BLUE), d))
    open(os.path.join(A, 'starman-mono-white.svg'), 'w').write(
        '<svg xmlns="http://www.w3.org/2000/svg" %s><path fill="#fff" d="%s"/></svg>\n' % (vb, d))
    # sun: the glow is part of the file, so the artboard has room around the mark
    open(os.path.join(A, 'starman-mark-sun.svg'), 'w').write(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-36 -36 %d %d">'
        '<filter id="sB1" x="-50%%" y="-50%%" width="200%%" height="200%%"><feGaussianBlur stdDeviation="3.6"/></filter>'
        '<filter id="sB2" x="-50%%" y="-50%%" width="200%%" height="200%%"><feGaussianBlur stdDeviation="11"/></filter>'
        '%s<path fill="#fff45c" opacity=".55" filter="url(#sB2)" d="%s"/>'
        '<path fill="#fff782" opacity=".9" filter="url(#sB1)" d="%s"/>'
        '<path fill="url(#sG)" d="%s"/></svg>\n' % (W + 72, H + 72, lin('sG', SUN), d, d, d))
    return d


def symbols(d):
    vb = 'viewBox="0 0 %d %d"' % (W, H)
    return ('<symbol id="sm-light" %s><path fill="currentColor" d="%s"/></symbol>'
            '<symbol id="sm-sun" %s>%s<path fill="url(#smsG)" d="%s"/></symbol>' % (vb, d, vb, lin('smsG', SUN), d))


def patch_index(d):
    p = os.path.join(HERE, 'index.html')
    s = open(p).read()
    s2, n = re.subn(r'<symbol id="sm-light".*?</symbol><symbol id="sm-sun".*?</symbol>',
                    lambda m: symbols(d), s, count=1, flags=re.S)
    assert n == 1, 'sm-light / sm-sun symbols not found in index.html'
    open(p, 'w').write(s2)


# ---- PNG -------------------------------------------------------------------
MARK_IN_AVATAR = .60     # mark width as a share of the avatar


def mark_mask(S, width, cx, cy):
    """L mask of the mark, `width` px wide, centred on (cx, cy) in an S x S canvas."""
    k = width / W
    m = Image.new('L', (S, S), 0)
    ImageDraw.Draw(m).polygon(flatten(MARK, k, cx - width / 2, cy - H * k / 2), fill=255)
    return m


def avatar(size):
    """Square, full bleed: the sun mark with its glow on the night field. Platforms crop it themselves."""
    S = size * 4
    img = gradient(S, NIGHT).convert('RGBA')
    w = S * MARK_IN_AVATAR
    shape = mark_mask(S, w, S / 2, S / 2)
    for colour, alpha, blur in (('#fff45c', .55, .075), ('#fff782', .9, .024)):
        glow = shape.filter(ImageFilter.GaussianBlur(w * blur)).point(lambda v: int(v * alpha))
        layer = Image.new('RGBA', (S, S), _rgb(colour) + (0,))
        layer.putalpha(glow)
        img = Image.alpha_composite(img, layer)
    top = (S - w * H / W) / 2
    sun = gradient(S, SUN, top / S, 1 - top / S).convert('RGBA')
    sun.putalpha(shape)
    return Image.alpha_composite(img, sun).resize((size, size), Image.LANCZOS)


def tab_icon(size):
    """Browser tab: the colour mark at full width on a transparent square."""
    S = size * 4
    shape = mark_mask(S, S, S / 2, S / 2)
    top = (S - S * H / W) / 2
    img = gradient(S, BLUE, top / S, 1 - top / S).convert('RGBA')
    img.putalpha(shape)
    return img.resize((size, size), Image.LANCZOS)


def write_pngs():
    A = os.path.join(HERE, 'assets')
    avatar(1024).save(os.path.join(A, 'starman-avatar.png'))
    avatar(180).save(os.path.join(A, 'favicon-180.png'))
    tab_icon(64).save(os.path.join(A, 'favicon-64.png'))


if __name__ == '__main__':
    d = write_svgs()
    patch_index(d)
    write_pngs()
    print('mark:', d)
