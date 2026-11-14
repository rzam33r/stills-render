"""Set a line of text in any of the film's scripts, with highlighted words.

Text may mix Hindi (Devanagari), Latin letters and emoji, and mark words to
highlight with asterisks: "*Insaan* ka baccha 💀". Each run of characters
is set in a font that has it:
  - Devanagari: Noto Sans Devanagari Bold, shaped with Raqm so vowel signs
    and joined letters sit where a reader expects;
  - emoji: Google's emoji pictures (fonts/emoji), scaled to the text;
  - everything else: Poppins.
"""
import functools
import pathlib
import re
import unicodedata

from PIL import Image, ImageDraw, ImageFont, features

FONTS = pathlib.Path(__file__).resolve().parent.parent / 'fonts'
WHITE = (255, 255, 255)
YELLOW = (255, 214, 10)
EMOJI_STRIDE = 66


def shaping_ok():
    """Hindi needs Raqm: without it, vowel signs land on the wrong letter."""
    return features.check('raqm')


def _kind(ch):
    o = ord(ch)
    if 0x0900 <= o <= 0x097F or 0xA8E0 <= o <= 0xA8FF or o in (0x200C, 0x200D):
        return 'deva'
    if o in (0xFE0F, 0x20E3) or 0x1F000 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF or 0x2B00 <= o <= 0x2BFF \
            or (unicodedata.category(ch) == 'So' and o > 0x2100):
        return 'emoji'
    return 'latin'


@functools.lru_cache(maxsize=1)
def _emoji_sheet():
    import json
    return (Image.open(FONTS / 'emoji' / 'google-64.png').convert('RGBA'),
            json.loads((FONTS / 'emoji' / 'google-64.json').read_text()))


def emoji_pictures(text):
    """The emoji in a run, longest match first: [64x64 RGBA image, ...]."""
    sheet, where = _emoji_sheet()
    cps = [f'{ord(c):04X}' for c in text]
    out, i = [], 0
    while i < len(cps):
        for j in range(len(cps), i, -1):
            key = '-'.join(cps[i:j])
            if key in where:
                x, y = where[key]
                out.append(sheet.crop((x * EMOJI_STRIDE + 1, y * EMOJI_STRIDE + 1,
                                       x * EMOJI_STRIDE + 65, y * EMOJI_STRIDE + 65)))
                i = j
                break
        else:
            i += 1          # a lone variation selector or joiner
    return out


@functools.lru_cache(maxsize=64)
def font(kind, size, heavy=False):
    if kind == 'deva':
        f = ImageFont.truetype(str(FONTS / 'NotoSansDevanagari-Variable.ttf'), size,
                               layout_engine=ImageFont.Layout.RAQM)
        f.set_variation_by_name('ExtraBold' if heavy else 'Bold')
        return f
    return ImageFont.truetype(str(FONTS / ('Poppins-ExtraBold.ttf' if heavy else 'Poppins-Bold.ttf')), size,
                              layout_engine=ImageFont.Layout.RAQM)


def words_of(text):
    """[(word, highlighted)] from text with *highlight* marks. A mark may
    cover one word ("*Insaan*") or several ("*not one* answer")."""
    marked, inside = [], False
    for w in text.split():
        opens, closes = w.startswith('*'), w.endswith('*') and len(w) > 1
        hl = inside or opens or closes
        if opens and not closes:
            inside = True
        if closes and not opens:
            inside = False
        word = w.replace('*', '')
        if word:
            marked.append((word, hl))
    return marked


def runs(word):
    """Split a word into runs of one kind: [(kind, text)]."""
    out = []
    for ch in word:
        k = _kind(ch)
        if out and out[-1][0] == k:
            out[-1] = (k, out[-1][1] + ch)
        else:
            out.append((k, ch))
    return out


def run_width(kind, text, size, heavy=False):
    if kind == 'emoji':
        return round(len(emoji_pictures(text)) * size * 1.08)
    return round(font(kind, size, heavy).getlength(text))


def word_width(word, size, heavy=False):
    return sum(run_width(k, t, size, heavy) for k, t in runs(word))


def lay_out(words, size, max_width, heavy=False, gap=0.28):
    """Wrap [(word, highlighted)] into rows that fit max_width:
    [[(word, highlighted, width)], ...]."""
    space = round(size * gap)
    rows, row, w = [], [], 0
    for word, hl in words:
        ww = word_width(word, size, heavy)
        if row and w + space + ww > max_width:
            rows.append(row)
            row, w = [], 0
        row.append((word, hl, ww))
        w += (space if len(row) > 1 else 0) + ww
    if row:
        rows.append(row)
    return rows


def row_width(row, size, gap=0.28):
    return sum(w for _, _, w in row) + round(size * gap) * (len(row) - 1)


def draw_rows(img, rows, size, centre_x, top, colour=WHITE, highlight=YELLOW, heavy=False,
              line=1.32, gap=0.28, stroke=0):
    """Draw rows centred on centre_x from top; returns the bottom y."""
    d = ImageDraw.Draw(img)
    space = round(size * gap)
    lh = round(size * line)
    for r, row in enumerate(rows):
        x = centre_x - row_width(row, size, gap) // 2
        base = top + r * lh
        for word, hl, ww in row:
            fill = highlight if hl else colour
            for kind, text in runs(word):
                if kind == 'emoji':
                    h = round(size * 1.0)
                    for k, em in enumerate(emoji_pictures(text)):
                        em = em.resize((h, h), Image.LANCZOS)
                        img.paste(em, (x + k * round(size * 1.08), base + round(size * 0.18)), em)
                    x += run_width(kind, text, size, heavy)
                    continue
                f = font(kind, size, heavy)
                # Same baseline for every script: ascender of the Latin font.
                asc = font('latin', size, heavy).getmetrics()[0]
                d.text((x, base + asc), text, font=f, fill=fill, anchor='ls',
                       stroke_width=stroke, stroke_fill=(0, 0, 0))
                x += run_width(kind, text, size, heavy)
            x += space
    return top + len(rows) * lh


def strip_marks(text):
    return re.sub(r'\*', '', text)


def fit_hook(text, size, max_width, smallest=50):
    """The hook on one line if it fits at any size down to smallest, else
    wrapped at the full size: (rows, size)."""
    words = words_of(text)
    for s in range(size, smallest - 1, -2):
        rows = lay_out(words, s, max_width, heavy=True)
        if len(rows) == 1:
            return rows, s
    return lay_out(words, size, max_width, heavy=True), size
