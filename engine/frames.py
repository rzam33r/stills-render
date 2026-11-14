"""The picture for each shot: a painting filling the frame, or a card.

A card is drawn here rather than by an image model, so its words are always
spelled right and always in the same hand-lettered font: black capitals on
white, with an optional small doodle under them. The doodle is a picture
with a white background; it is multiplied onto the card, so its white
disappears and only its lines show.
"""
import pathlib
import textwrap

from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent.parent
FONT = HERE / 'fonts' / 'CaveatBrush-Regular.ttf'
PAPER = (255, 255, 255)
INK = (17, 17, 17)

SIZES = {'16:9': (1920, 1080), '9:16': (1080, 1920)}


def cover(img, size):
    """Scale a picture to fill the frame, cropping the overflow evenly."""
    W, H = size
    img = img.convert('RGB')
    w, h = img.size
    s = max(W / w, H / h)
    nw, nh = max(W, round(w * s)), max(H, round(h * s))
    img = img.resize((nw, nh), Image.LANCZOS)
    x, y = (nw - W) // 2, (nh - H) // 2
    return img.crop((x, y, x + W, y + H))


def _fit_text(text, box_w, box_h, biggest, smallest=40):
    """The largest font and line wrap that fit the box."""
    for size in range(biggest, smallest - 1, -4):
        font = ImageFont.truetype(str(FONT), size)
        # Try fewer, longer lines first: a card reads best on 1 to 3 lines.
        for width in range(len(text), 0, -1):
            lines = textwrap.wrap(text, width=width, break_long_words=False) or [text]
            if len(lines) > 4:
                break
            widths = [font.getbbox(l)[2] - font.getbbox(l)[0] for l in lines]
            line_h = round(size * 1.12)
            if max(widths) <= box_w and line_h * len(lines) <= box_h:
                return font, lines, line_h
    font = ImageFont.truetype(str(FONT), smallest)
    return font, textwrap.wrap(text, width=28), round(smallest * 1.12)


def card(text, size, doodle=None):
    """A white card with the line in capitals and an optional doodle under it."""
    W, H = size
    img = Image.new('RGB', size, PAPER)
    d = ImageDraw.Draw(img)
    text = ' '.join(text.split()).upper()
    tall = H > W
    box_w = round(W * (0.84 if tall else 0.78))
    if doodle is not None:
        box_h = round(H * (0.30 if tall else 0.36))
        centre = round(H * (0.36 if tall else 0.36))
    else:
        box_h = round(H * 0.5)
        centre = round(H * 0.5)
    font, lines, line_h = _fit_text(text, box_w, box_h, biggest=round(min(W, H) * (0.15 if tall else 0.14)))
    top = centre - (line_h * len(lines)) // 2
    for k, line in enumerate(lines):
        x0, y0, x1, y1 = font.getbbox(line)
        x = (W - (x1 - x0)) // 2 - x0
        y = top + k * line_h + (line_h - (y1 - y0)) // 2 - y0
        # A hair of stroke gives the brush letters the weight of a marker.
        d.text((x, y), line, font=font, fill=INK, stroke_width=max(1, line_h // 60), stroke_fill=INK)
    if doodle is not None:
        dw, dh = round(W * (0.5 if tall else 0.26)), round(H * (0.24 if tall else 0.30))
        pic = doodle.convert('RGB')
        pic.thumbnail((dw, dh), Image.LANCZOS)
        dy0 = top + line_h * len(lines) + round(H * 0.05)
        x, y = (W - pic.width) // 2, min(dy0, H - pic.height - round(H * 0.06))
        region = img.crop((x, y, x + pic.width, y + pic.height))
        img.paste(ImageChops.multiply(region, pic), (x, y))
    return img


def with_logo(img, logo, size):
    """The brand mark in the top-right corner, small."""
    if logo is None:
        return img
    W, H = size
    h = round(min(W, H) * 0.11)
    mark = logo.copy()
    mark.thumbnail((h * 2, h), Image.LANCZOS)
    m = round(min(W, H) * 0.025)
    out = img.convert('RGBA')
    out.alpha_composite(mark, (W - mark.width - m, m))
    return out.convert('RGB')


def shot_image(shot, find, size, logo=None):
    """The finished frame for one shot. find(name) gives a picture's path."""
    if 'card' in shot:
        doodle = Image.open(find(shot['doodle'])) if shot.get('doodle') else None
        img = card(shot['card'], size, doodle)
    else:
        img = cover(Image.open(find(shot['picture'])), size)
    return with_logo(img, logo, size)
