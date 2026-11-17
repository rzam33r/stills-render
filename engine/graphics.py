"""Animated comic-style graphics: a shot whose "graphic" asks for a pie, bars,
a gauge, a counter, a road with footprints, a map with a pin, or icons.

    {"say": "Sirf tees pratishat log...", "graphic": {"kind": "pie", "value": 30}}

Each graphic plays a short entrance (about a second) and then keeps moving
gently (a slowly turning sunburst, floating icons, a breathing slice) for as
long as its shot lasts. Drawn in the films' comic style: cream sunburst, bold
dark-brown outlines, warm pastel colours, a hand-lettered font, and Noto
emoji icons turned into stickers (white ring, dark outline).

    frame(graphic, t, duration, size, icon_dir, language) -> RGB image

Kinds and their fields ("label", a short line under it, is allowed on all):
  icons  "icons": 1 to 6 icon names; they pop in one by one and float.
  pie    "value": a percentage, or "values": up to 5 shares; optional "icon".
  bars   "values": 2 to 6 numbers; optional "labels" (same count), "unit".
  gauge  "value": 0 to 100; optional "unit". The needle swings and settles.
  count  "value": a number; optional "unit" and "icon". It counts up.
  road   "icon": where the road leads; optional "from". Footprints walk it.
  map    "icon": a map or globe (default "world map"); optional "at":
         [x, y], 0 to 1 across the icon, where the pin drops.
"""
import functools
import math
import pathlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

import icons

HERE = pathlib.Path(__file__).resolve().parent.parent
FONT_LATIN = HERE / 'fonts' / 'CaveatBrush-Regular.ttf'
FONT_DEVA = HERE / 'fonts' / 'Kalam-Bold.ttf'

INK = (59, 35, 20)
CREAM = (253, 243, 227)
CREAM_DARK = (246, 228, 198)
WHITE = (255, 255, 255)
PALETTE = [(240, 128, 100), (90, 180, 170), (245, 190, 80), (120, 170, 230), (130, 190, 110), (185, 125, 195)]
ZONES = [(0, 40, (130, 190, 110)), (40, 70, (245, 190, 80)), (70, 85, (240, 150, 80)), (85, 100, (225, 90, 80))]
KINDS = ('icons', 'pie', 'bars', 'gauge', 'count', 'road', 'map')
SS = 2                      # drawn at twice the size, then halved: smooth edges


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_back(x, s=1.9):
    """Overshoots a little, then settles: a playful pop."""
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def is_devanagari(text):
    return any('ऀ' <= ch <= 'ॿ' for ch in str(text))


@functools.lru_cache(maxsize=64)
def font(px, devanagari):
    path = FONT_DEVA if devanagari else FONT_LATIN
    engine = ImageFont.Layout.RAQM if features.check('raqm') else ImageFont.Layout.BASIC
    return ImageFont.truetype(str(path), px, layout_engine=engine)


def number_text(v, language='en'):
    """1234567 -> "1,234,567" (Hindi: "12,34,567"); 12.5 stays 12.5."""
    if abs(v - round(v)) < 1e-9:
        n, frac = int(round(v)), ''
    else:
        n, frac = int(v), f'{abs(v) % 1:.1f}'[1:]
    s = str(abs(n))
    if language == 'hi' and len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        s = ','.join(([head] if head else []) + groups + [tail])
    else:
        s = f'{abs(n):,}'
    return ('-' if v < 0 else '') + s + frac


def text(draw, xy, words, px, fill=WHITE, anchor='mm', stroke=None):
    """Hand-lettered text with a dark outline, centred on xy."""
    stroke = stroke if stroke is not None else max(2, px // 9)
    draw.text(xy, str(words), font=font(px, is_devanagari(words)), fill=fill, anchor=anchor,
              stroke_width=stroke, stroke_fill=INK)


def fit_px(words, px, max_width):
    """The largest size up to px at which words fit in max_width."""
    while px > 12 and font(px, is_devanagari(words)).getlength(str(words)) > max_width:
        px = int(px * 0.92)
    return px


@functools.lru_cache(maxsize=48)
def sticker(path, px):
    """The icon at px wide as a sticker: white ring and dark outline."""
    src = Image.open(path).convert('RGBA')
    pad = 40
    big = Image.new('RGBA', (src.width + 2 * pad, src.height + 2 * pad), (0, 0, 0, 0))
    big.paste(src, (pad, pad))
    a = big.getchannel('A').point(lambda v: 255 if v > 40 else 0)
    ring = a.filter(ImageFilter.MaxFilter(23))
    edge = ring.filter(ImageFilter.MaxFilter(13))
    out = Image.new('RGBA', big.size, (0, 0, 0, 0))
    out.paste(INK + (255,), (0, 0), edge)
    out.paste(WHITE + (255,), (0, 0), ring)
    out.alpha_composite(big)
    out = out.crop(out.getbbox())
    h = round(out.height * px / out.width)
    return out.resize((px, h), Image.LANCZOS)


class Canvas:
    """One frame, drawn at SS times the film's size."""

    def __init__(self, size, t):
        self.W, self.H = size[0] * SS, size[1] * SS
        self.u = min(self.W, self.H)
        self.t = t
        self.img = Image.new('RGB', (self.W, self.H), CREAM)
        self.d = ImageDraw.Draw(self.img)
        self.portrait = self.H > self.W
        self.burst()

    def burst(self, rays=18):
        """A comic sunburst behind everything, turning slowly."""
        cx, cy = self.W / 2, self.H * 0.46
        R = math.hypot(self.W, self.H)
        turn = math.radians(self.t * 5)
        for k in range(0, rays, 2):
            a0 = turn + 2 * math.pi * k / rays
            a1 = turn + 2 * math.pi * (k + 1) / rays
            self.d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)),
                            (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=CREAM_DARK)

    def line_w(self, k=1.0):
        return max(2, round(self.u * 0.008 * k))

    def paste_icon(self, path, cx, cy, px, scale=1.0, angle=0.0):
        if scale <= 0.02 or px <= 4:
            return
        st = sticker(path, max(8, int(px)))
        w = max(2, int(st.width * scale))
        im = st.resize((w, max(2, int(st.height * scale))), Image.BICUBIC)
        if abs(angle) > 0.2:
            im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
        self.img.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)

    def label(self, words):
        if not words:
            return
        p = ease_out((self.t - 0.5) / 0.5)
        if p <= 0:
            return
        px = fit_px(words, round(self.u * (0.085 if self.portrait else 0.075)), self.W * 0.86)
        y = self.H * (0.86 if self.portrait else 0.88) + (1 - p) * self.u * 0.05
        text(self.d, (self.W / 2, y), words, px)

    def done(self, size):
        return self.img.reduce(SS) if SS > 1 else self.img


def floating(t, i, amp):
    """A gentle float and wobble for item i: (dy, degrees)."""
    return (math.sin(2 * math.pi * (t / 2.3 + i * 0.29)) * amp,
            math.sin(2 * math.pi * (t / 1.9 + i * 0.17)) * 4)


def grid(n, portrait):
    """(columns, rows) for n items."""
    if n <= 1:
        return 1, 1
    if n == 2:
        return (1, 2) if portrait else (2, 1)
    if n <= 4:
        return 2, 2
    return (2, 3) if portrait else (3, 2)


def draw_icons(c, g, paths):
    names = g.get('icons') or []
    n = len(names)
    cols, rows = grid(n, c.portrait)
    top, bottom = c.H * 0.12, c.H * (0.78 if g.get('label') else 0.88)
    cw, ch = c.W * 0.86 / cols, (bottom - top) / rows
    px = min(cw, ch) * (0.78 if n > 1 else 0.7)
    for i, name in enumerate(names):
        r, k = divmod(i, cols)
        in_row = min(cols, n - r * cols)
        cx = c.W / 2 + (k - (in_row - 1) / 2) * cw
        cy = top + (r + 0.5) * ch
        s = ease_back((c.t - 0.1 - i * 0.18) / 0.45)
        dy, rot = floating(c.t, i, c.u * 0.012)
        c.paste_icon(paths[name], cx, cy + dy, px, s, rot)


def draw_pie(c, g, paths, language):
    values = g.get('values') or [g.get('value', 0)]
    values = [max(0.0, float(v)) for v in values]
    total = sum(values)
    shares = [v / total * 100 for v in values] if total > 100 else values
    r = c.u * (0.30 if c.portrait else 0.30)
    cx, cy = (c.W / 2, c.H * 0.40) if c.portrait else (c.W * 0.36, c.H * 0.45)
    lw = c.line_w(1.2)
    pop = ease_back(c.t / 0.4)
    rr = r * pop
    if rr < 4:
        return
    c.d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=WHITE, outline=INK, width=lw)
    sweep = ease_out((c.t - 0.25) / 1.1) * 360
    start = -90.0
    for i, share in enumerate(shares):
        span = share * 3.6
        shown = clamp(sweep - (start + 90), 0, span)
        if shown > 0.3:
            off = (0.5 + 0.5 * math.sin(c.t * 3.1)) * c.u * 0.018 if i == 0 and c.t > 1.4 else 0
            mid = math.radians(start + shown / 2)
            ox, oy = off * math.cos(mid), off * math.sin(mid)
            c.d.pieslice((cx - rr + ox, cy - rr + oy, cx + rr + ox, cy + rr + oy), start, start + shown,
                         fill=PALETTE[i % len(PALETTE)], outline=INK, width=lw)
        start += span
    main = shares[0] * clamp(sweep / max(0.01, shares[0] * 3.6))
    px = round(c.u * (0.16 if c.portrait else 0.22))
    nx, ny = (cx, cy + r + c.u * 0.13) if c.portrait else (c.W * 0.72, cy)
    text(c.d, (nx, ny), number_text(round(main), language) + '%', px, fill=PALETTE[0])
    if g.get('icon') and g['icon'] in paths:
        s = ease_back((c.t - 1.2) / 0.4)
        dy, rot = floating(c.t, 1, c.u * 0.01)
        c.paste_icon(paths[g['icon']], cx + r * 0.95, cy - r * 0.95 + dy, c.u * 0.17, s, rot)


def draw_bars(c, g, paths, language):
    values = [float(v) for v in g.get('values') or []]
    labels = g.get('labels') or []
    unit = str(g.get('unit', ''))
    n = len(values)
    top_v = max(values) if values and max(values) > 0 else 1
    left, right = c.W * 0.1, c.W * 0.9
    base = c.H * (0.70 if c.portrait else 0.74)
    max_h = c.H * (0.40 if c.portrait else 0.50)
    slot = (right - left) / max(1, n)
    bw = slot * 0.62
    lw = c.line_w()
    c.d.line((left - c.u * 0.02, base, right + c.u * 0.02, base), fill=INK, width=lw)
    for i, v in enumerate(values):
        p = ease_back((c.t - 0.15 - i * 0.16) / 0.6, s=1.4)
        if p <= 0:
            continue
        breathe = 1 + 0.012 * math.sin(c.t * 2.6 + i) if c.t > 1.6 else 1
        h = max(2.0, v / top_v * max_h * p * breathe)
        x0 = left + i * slot + (slot - bw) / 2
        c.d.rounded_rectangle((x0, base - h, x0 + bw, base), radius=bw * 0.12,
                              fill=PALETTE[i % len(PALETTE)], outline=INK, width=lw)
        whole = all(abs(x - round(x)) < 1e-9 for x in values)
        shown = round(v * clamp(p)) if whole else round(v * clamp(p), 1)
        px = fit_px(number_text(round(v, 1), language) + unit, round(c.u * 0.085), slot * 0.95)
        text(c.d, (x0 + bw / 2, base - h - c.u * 0.055), number_text(shown, language) + unit, px)
        if i < len(labels) and labels[i]:
            lp = fit_px(labels[i], round(c.u * 0.055), slot * 0.95)
            text(c.d, (x0 + bw / 2, base + c.u * 0.055), labels[i], lp, fill=INK, stroke=0)


def draw_gauge(c, g, paths, language):
    target = clamp(float(g.get('value', 0)), 0, 100)
    r = c.u * (0.36 if c.portrait else 0.30)
    cx, cy = c.W / 2, c.H * (0.52 if c.portrait else 0.60)
    lw = c.line_w(1.2)
    band = r * 0.26
    for lo, hi, col in ZONES:
        c.d.pieslice((cx - r, cy - r, cx + r, cy + r), 180 + lo * 1.8, 180 + hi * 1.8, fill=col, outline=INK, width=lw)
    ri = r - band
    c.d.pieslice((cx - ri, cy - ri, cx + ri, cy + ri), 180, 360, fill=CREAM, outline=INK, width=lw)
    c.d.line((cx - r, cy, cx + r, cy), fill=INK, width=lw)
    for k in range(11):
        a = math.radians(180 + k * 18)
        c.d.line((cx + (ri - r * 0.06) * math.cos(a), cy + (ri - r * 0.06) * math.sin(a),
                  cx + ri * math.cos(a), cy + ri * math.sin(a)), fill=INK, width=lw)
    x = clamp((c.t - 0.2) / 1.7, 0, 9)
    v = target * (1 - math.exp(-3.2 * x) * math.cos(5.5 * x)) if c.t < 3.5 else target
    v += math.sin(c.t * 13) * 0.7 if c.t > 1.2 else 0
    v = clamp(v, 0, 103)
    a = math.radians(180 + v * 1.8)
    tip = (cx + (ri - r * 0.04) * math.cos(a), cy + (ri - r * 0.04) * math.sin(a))
    side = c.u * 0.022
    pa = (cx + side * math.cos(a + math.pi / 2), cy + side * math.sin(a + math.pi / 2))
    pb = (cx + side * math.cos(a - math.pi / 2), cy + side * math.sin(a - math.pi / 2))
    c.d.polygon([tip, pa, pb], fill=PALETTE[0], outline=INK, width=lw)
    hub = c.u * 0.04
    c.d.ellipse((cx - hub, cy - hub, cx + hub, cy + hub), fill=INK)
    px = round(c.u * 0.15)
    text(c.d, (cx, cy + c.u * 0.13), number_text(round(clamp(v, 0, 100)), language) + str(g.get('unit', '')), px)


def draw_count(c, g, paths, language):
    target = float(g.get('value', 0))
    p = ease_out((c.t - 0.2) / 1.5)
    shown = target * p
    if abs(target) >= 10 or abs(target - round(target)) < 1e-9:
        shown = round(shown)
    words = number_text(shown, language) + (' ' + str(g['unit']) if g.get('unit') else '')
    cx, cy = c.W / 2, c.H * (0.56 if c.portrait else 0.60)
    full = number_text(target, language) + (' ' + str(g['unit']) if g.get('unit') else '')
    px = fit_px(full, round(c.u * 0.2), c.W * 0.86)
    if p >= 1:
        pulse = 1 + 0.04 * math.sin((c.t - 1.7) * 6)
        px = round(px * pulse)
        for k in range(12):
            a = 2 * math.pi * k / 12 + c.t * 0.4
            r0, r1 = c.u * 0.33, c.u * (0.38 + 0.02 * math.sin(c.t * 5 + k))
            c.d.line((cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a)),
                     fill=PALETTE[k % len(PALETTE)], width=c.line_w(1.4))
    text(c.d, (cx, cy), words, px, fill=PALETTE[2])
    if g.get('icon') and g['icon'] in paths:
        s = ease_back((c.t - 0.05) / 0.45)
        dy, rot = floating(c.t, 0, c.u * 0.015)
        c.paste_icon(paths[g['icon']], cx, cy - c.u * 0.32 + dy, c.u * 0.26, s, rot)


@functools.lru_cache(maxsize=4)
def footprint(px):
    """One dark footprint pointing up, px tall."""
    w = px * 0.5
    im = Image.new('RGBA', (int(w * 1.4), int(px * 1.15)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox = (im.width - w) / 2
    d.ellipse((ox, px * 0.3, ox + w, px * 1.1), fill=INK + (235,))
    for k, (fx, fy, fr) in enumerate([(0.12, 0.2, 0.11), (0.38, 0.1, 0.13), (0.62, 0.11, 0.11), (0.82, 0.18, 0.09)]):
        rr = fr * px
        d.ellipse((ox + fx * w - rr, fy * px - rr + px * 0.06, ox + fx * w + rr, fy * px + rr + px * 0.06), fill=INK + (235,))
    return im


def road_point(c, s):
    """A point on the road, s from 0 (start) to 1 (end), and its heading."""
    if c.portrait:
        x = c.W / 2 + c.W * 0.22 * math.sin(2 * math.pi * s * 1.15)
        y = c.H * 0.76 - s * c.H * 0.56
    else:
        x = c.W * 0.1 + s * c.W * 0.68
        y = c.H * 0.52 + c.H * 0.15 * math.sin(2 * math.pi * s * 1.1)
    return x, y


def draw_road(c, g, paths, language):
    pts = [road_point(c, k / 80) for k in range(81)]
    reveal = ease_out(c.t / 0.5)
    shown = pts[:max(2, int(len(pts) * reveal))]
    width = c.u * 0.16
    c.d.line(shown, fill=INK, width=int(width + c.line_w(2)), joint='curve')
    c.d.line(shown, fill=(226, 196, 150), width=int(width), joint='curve')
    for k in range(0, len(shown) - 2, 6):
        c.d.line(shown[k:k + 3], fill=WHITE, width=c.line_w(0.9))
    steps = 9
    fp = footprint(int(c.u * 0.05))
    for k in range(steps):
        appear = 0.5 + k * 0.17
        if c.t < appear:
            break
        s = 0.06 + 0.8 * k / (steps - 1)
        (x0, y0), (x1, y1) = road_point(c, s), road_point(c, s + 0.01)
        heading = math.degrees(math.atan2(y1 - y0, x1 - x0))
        side = (1 if k % 2 else -1) * c.u * 0.026
        nx, ny = -(y1 - y0), (x1 - x0)
        norm = math.hypot(nx, ny) or 1
        x, y = x0 + side * nx / norm, y0 + side * ny / norm
        im = fp.rotate(-heading - 90, resample=Image.BICUBIC, expand=True)
        pop = ease_back((c.t - appear) / 0.2)
        if pop > 0.05:
            im = im.resize((max(2, int(im.width * pop)), max(2, int(im.height * pop))), Image.BICUBIC)
            c.img.paste(im, (int(x - im.width / 2), int(y - im.height / 2)), im)
    ex, ey = road_point(c, 1.0)
    if g.get('icon') in paths:
        arrive = 0.5 + steps * 0.17
        bounce = abs(math.sin((c.t - arrive) * 7)) * c.u * 0.03 * math.exp(-(c.t - arrive) * 1.5) if c.t > arrive else 0
        dy, rot = floating(c.t, 2, c.u * 0.008)
        c.paste_icon(paths[g['icon']], ex, ey - c.u * 0.06 - bounce + dy, c.u * 0.26, ease_back((c.t - 0.2) / 0.45), rot)
    if g.get('from') in paths:
        sx, sy = road_point(c, 0.0)
        c.paste_icon(paths[g['from']], sx, sy, c.u * 0.16, ease_back(c.t / 0.45))


def draw_map(c, g, paths, language):
    name = g.get('icon') or 'world map'
    px = c.u * (0.78 if c.portrait else 0.62)
    cx, cy = c.W / 2, c.H * (0.44 if c.portrait else 0.43)
    if name in paths:
        dy, rot = floating(c.t, 0, c.u * 0.006)
        c.paste_icon(paths[name], cx, cy + dy, px, ease_back(c.t / 0.5), rot * 0.3)
    at = g.get('at') or [0.62, 0.42]
    px_ = cx + (float(at[0]) - 0.5) * px * 0.9
    py_ = cy + (float(at[1]) - 0.5) * px * 0.65
    land = 0.9
    if c.t >= land:
        overlay = Image.new('RGBA', c.img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        for k in range(3):
            ph = ((c.t - land) / 1.2 + k / 3) % 1
            rr = c.u * (0.02 + 0.16 * ph)
            od.ellipse((px_ - rr, py_ - rr * 0.5, px_ + rr, py_ + rr * 0.5), outline=PALETTE[0] + (int(255 * (1 - ph)),),
                       width=c.line_w(1.2))
        c.img.paste(overlay, (0, 0), overlay)
    pin = paths.get('round pushpin')
    if pin:
        fall = ease_back((c.t - 0.45) / 0.45, s=2.4)
        y = py_ - c.u * 0.09 - (1 - fall) * c.H * 0.5
        if c.t > 0.45:
            c.paste_icon(pin, px_ + c.u * 0.02, y, c.u * 0.16)


DRAW = {'icons': draw_icons, 'pie': draw_pie, 'bars': draw_bars, 'gauge': draw_gauge,
        'count': draw_count, 'road': draw_road, 'map': draw_map}


def icon_paths(graphic, icon_dir):
    """{name as written: picture path} for every icon the graphic uses."""
    out = {}
    names = icons.icon_names(graphic) + icons.BUILT_IN.get(graphic.get('kind'), [])
    if graphic.get('kind') == 'map' and not graphic.get('icon'):
        names.append('world map')
    for n in names:
        code = icons.lookup(n)
        if code is None:
            raise SystemExit(f'graphic: no icon called "{n}" (python3 engine/icons.py list)')
        p = pathlib.Path(icon_dir) / f'emoji_u{code}.png'
        if not p.exists():
            raise SystemExit(f'graphic: icon "{n}" was not fetched into {icon_dir} (engine/icons.py fetch)')
        out[n] = p
    return out


def frame(graphic, t, duration, size, icon_dir, language='en'):
    """The graphic at t seconds into its shot, as an RGB image of size."""
    c = Canvas(size, t)
    paths = icon_paths(graphic, icon_dir)
    kind = graphic.get('kind')
    if kind == 'icons':
        DRAW[kind](c, graphic, paths)
    else:
        DRAW[kind](c, graphic, paths, language)
    c.label(graphic.get('label'))
    return c.done(size)
