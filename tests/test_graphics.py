"""The animated graphics and the icon library.

    python3 tests/test_graphics.py

No download needed: icons are stand-in discs. Checks that:
  - icons are found by name, by emoji and by U+ code, and unknown names are not;
  - every icon a guide example names exists;
  - the plan check accepts good graphics and catches each kind of mistake;
  - every kind draws at the film's size, upright and wide, and moves;
  - numbers are grouped the Indian way in Hindi films.
"""
import json
import pathlib
import re
import sys
import tempfile

from PIL import Image, ImageChops, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
import graphics  # noqa: E402
import icons  # noqa: E402
from check_plan import check, check_graphic  # noqa: E402

bad = 0


def say(ok, msg):
    global bad
    bad += not ok
    print(('ok   ' if ok else 'FAIL ') + msg)


# Icons by name, emoji and code.
say(icons.lookup('apple') == icons.lookup('Red Apple') == icons.lookup('🍎') == icons.lookup('U+1F34E') == '1f34e',
    'an icon is found by name, by any letter case, by emoji and by U+ code')
say(icons.lookup('cut_of_meat') == icons.lookup('cut of meat') is not None, 'underscores and spaces are the same')
say(icons.lookup('appel') is None and icons.lookup('') is None, 'an unknown name is not an icon')
say(len(set(icons.NAMES.values())) >= 1500, f'the library has {len(set(icons.NAMES.values()))} icons')
guide = (ROOT / 'docs' / 'chatgpt' / '8_GRAPHICS.md').read_text()
listed = [n for part in guide.split('## Icons')[1].split('### ')[1:] for n in part.split('\n', 2)[2].strip().split(', ')]
say(listed and all(icons.lookup(n) for n in listed), f'every one of the {len(listed)} names in 8_GRAPHICS.md is an icon')
for name in ('north-star-plan.json', 'rain-short-plan.json', 'boond-hindi-short-plan.json'):
    plan = json.loads((ROOT / 'examples' / name).read_text())
    shots = [s for s in plan['shots'] if 'graphic' in s]
    say(shots and not check(plan)[0], f'{name}: has an animated graphic and passes the plan check')

# The plan check on graphics.
good = [{'kind': 'pie', 'value': 30, 'icon': 'apple', 'label': 'eat fruit daily'},
        {'kind': 'pie', 'values': [50, 30, 20]},
        {'kind': 'bars', 'values': [1, 2, 3], 'labels': ['a', 'b', 'c'], 'unit': '%'},
        {'kind': 'gauge', 'value': 82}, {'kind': 'count', 'value': 30000, 'unit': 'years', 'icon': 'fire'},
        {'kind': 'road', 'icon': 'house', 'from': 'tent'}, {'kind': 'map', 'icon': 'world map', 'at': [0.66, 0.47]},
        {'kind': 'icons', 'icons': ['apple', '🍌', 'carrot']}]
say(all(not check_graphic(g, 'x')[0] for g in good), 'good graphics of every kind pass')
wrong = {'a percentage over 100': {'kind': 'pie', 'value': 130}, 'one bar': {'kind': 'bars', 'values': [4]},
         'labels that do not match the bars': {'kind': 'bars', 'values': [1, 2], 'labels': ['a']},
         'an unknown icon': {'kind': 'icons', 'icons': ['appel']}, 'an unknown kind': {'kind': 'spin'},
         'a road with nowhere to go': {'kind': 'road'}, 'a pin off the map': {'kind': 'map', 'at': [2, 0]},
         'a gauge over 100': {'kind': 'gauge', 'value': 140}, 'seven icons': {'kind': 'icons', 'icons': ['apple'] * 7},
         'a long label': {'kind': 'gauge', 'value': 5, 'label': 'one two three four five six seven'}}
for what, g in wrong.items():
    say(bool(check_graphic(g, 'x')[0]), f'the plan check catches {what}')
two = {'title': 'T', 'style': 's', 'shots': [{'say': 'one two three four five six', 'picture': '001', 'prompt': 'p'},
                                             {'say': 'one two three four five six', 'card': 'Old card'}]}
say(any('retired' in w for w in check(two)[1]) and not check(two)[0], 'an old white card still works but is called retired')
two['shots'][1] = {'say': 'one two three four five six', 'picture': '002', 'prompt': 'p', 'graphic': good[3]}
say(bool(check(two)[0]), 'a shot cannot be both a picture and a graphic')

# Every kind draws, at both shapes, and moves.
tmp = pathlib.Path(tempfile.mkdtemp())
for k, code in enumerate(sorted({icons.lookup(n) for g in good for n in icons.icon_names(g) + icons.BUILT_IN.get(g['kind'], [])}
                                | {icons.lookup('world map')})):
    im = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((40, 40, 472, 472), fill=(40 + k * 30 % 200, 120, 180, 255))
    im.save(tmp / f'emoji_u{code}.png')
for size in ((1080, 1920), (1920, 1080)):
    for g in good:
        a = graphics.frame(g, 0.3, 4.0, size, tmp)
        b = graphics.frame(g, 2.5, 4.0, size, tmp)
        moved = ImageChops.difference(a, b).getbbox() is not None
        say(a.size == size and b.mode == 'RGB' and moved, f'{g["kind"]} draws at {size[0]}x{size[1]} and moves')
say(graphics.number_text(1250000, 'hi') == '12,50,000' and graphics.number_text(1250000, 'en') == '1,250,000'
    and graphics.number_text(12.5) == '12.5', 'numbers: 12,50,000 in Hindi, 1,250,000 in English, 12.5 stays 12.5')
hindi = graphics.frame({'kind': 'count', 'value': 1250000, 'unit': 'लोग', 'label': 'हर साल'}, 3.0, 4.0, (1080, 1920), tmp, 'hi')
say(hindi.size == (1080, 1920), 'Hindi words on a graphic draw')

print('\nall good' if not bad else f'\n{bad} failing')
sys.exit(1 if bad else 0)
