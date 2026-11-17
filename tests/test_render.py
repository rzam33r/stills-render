"""Make a short film from stand-in pictures and a stand-in voice, and check it.

    python3 tests/test_render.py [--keep DIR]

No Kokoro needed: the voice is a tone per word at known times, so where each
picture must start is known exactly. Checks that:
  - every picture change in the film is on the frame of its shot's first word;
  - the checker itself catches a picture that is three frames late;
  - picture and sound are the same length, at 1920x1080 and 30 fps;
  - a card's words stay inside the frame, however long, and a doodle's
    white background vanishes into the card.
"""
import json
import math
import pathlib
import shutil
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
from frames import card  # noqa: E402
from timing import narration_words, shot_starts, word_starts  # noqa: E402

bad = 0


def say(ok, msg):
    global bad
    bad += not ok
    print(('ok   ' if ok else 'FAIL ') + msg)


def picture(path, n, size=(1344, 768)):
    img = Image.new('RGB', size, ((n * 67) % 200 + 30, (n * 131) % 200 + 30, (n * 29) % 200 + 30))
    d = ImageDraw.Draw(img)
    d.ellipse((size[0] // 2 - 120, size[1] // 2 - 120, size[0] // 2 + 120, size[1] // 2 + 120), fill='white')
    d.text((size[0] // 2 - 10, size[1] // 2 - 6), str(n), fill='black')
    img.save(path)


def doodle(path):
    img = Image.new('RGB', (600, 600), 'white')
    d = ImageDraw.Draw(img)
    d.line((100, 100, 500, 500), fill='black', width=24)
    d.line((500, 100, 100, 500), fill='black', width=24)
    img.save(path)


def fake_voice(plan, out):
    """A 220 Hz tone for each word, 0.32 s per word with a gap at commas;
    the tokens the real voice would report; cuts.json from them."""
    rate, t, tokens, chunks = 24000, 0.2, [], [np.zeros(int(0.2 * 24000), np.float32)]
    for s in plan['shots']:
        for w in s['say'].replace('*', '').split():
            dur = 0.32
            tone = 0.3 * np.sin(2 * math.pi * 220 * np.arange(int(dur * rate)) / rate).astype(np.float32)
            tokens.append((w, t, t + dur, ' '))
            chunks += [tone, np.zeros(int(0.04 * rate), np.float32)]
            t += dur + 0.04
    audio = np.concatenate(chunks)
    out.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out / 'voice.wav'), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate)
        f.writeframes((audio * 32767).astype('<i2').tobytes())
    says = [s['say'] for s in plan['shots']]
    starts = shot_starts(says, tokens)
    words = [{'shot': i, 'word': w, 'start': s} for (i, w), s in zip(narration_words(says), word_starts(says, tokens))]
    (out / 'cuts.json').write_text(json.dumps({'starts': starts, 'speech_end': t, 'audio_seconds': len(audio) / rate,
                                               'words': words}, ensure_ascii=False))
    return starts


def stand_in_icons(plan, folder):
    """A coloured disc for every icon the plan's graphics use (no download)."""
    import icons
    folder.mkdir(parents=True, exist_ok=True)
    for k, code in enumerate(sorted(icons.plan_codes(plan))):
        im = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
        ImageDraw.Draw(im).ellipse((40, 40, 472, 472), fill=((k * 70) % 200 + 40, 120, 200 - (k * 40) % 150, 255))
        im.save(folder / f'emoji_u{code}.png')


def film_test(name, want_size, keep, captions=False):
    plan_path = name if isinstance(name, pathlib.Path) else ROOT / 'examples' / name
    name = plan_path.name
    plan = json.loads(plan_path.read_text())
    tag = name.replace('-plan.json', '') + (' with subtitles' if captions else '')
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        if captions:
            plan['captions'] = True
            plan_path = tmp / 'plan.json'
            plan_path.write_text(json.dumps(plan, ensure_ascii=False))
        pics = tmp / 'pictures'
        pics.mkdir()
        for s in plan['shots']:
            if 'picture' in s:
                picture(pics / f"{s['picture']}.png", int(s['picture']))
            if s.get('doodle'):
                doodle(pics / f"{s['doodle']}.jpg")
        r = subprocess.run([sys.executable, str(ROOT / 'engine' / 'check_plan.py'), str(plan_path),
                            '--pictures', str(pics)], capture_output=True, text=True)
        say(r.returncode == 0, f'{tag}: the plan passes with its pictures present')
        fake_voice(plan, tmp / 'voice')
        stand_in_icons(plan, tmp / 'icons')
        film = tmp / 'film.mp4'
        music = sorted((ROOT / 'music').glob('*.mp3'))[0]
        r = subprocess.run([sys.executable, str(ROOT / 'engine' / 'render.py'), str(plan_path),
                            str(pics), str(tmp / 'voice'), str(film), '--logo', str(ROOT / 'brand' / 'watermark.png'),
                            '--music', str(music), '--icons', str(tmp / 'icons')], capture_output=True, text=True)
        print('     ' + (r.stdout.strip() or r.stderr.strip()[-600:]))
        say(r.returncode == 0 and film.exists(), f'{tag}: the film renders')
        if not film.exists():
            return
        r = subprocess.run([sys.executable, str(ROOT / 'engine' / 'check_sync.py'), str(film)], capture_output=True, text=True)
        print('     ' + r.stdout.strip().replace('\n', '\n     '))
        say(r.returncode == 0, f'{tag}: every picture (and subtitle word) changes on its word\'s frame')
        probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                'stream=width,height,r_frame_rate', '-of', 'csv=p=0', str(film)],
                               capture_output=True, text=True).stdout.strip()
        say(probe == f'{want_size},30/1', f'{tag}: {want_size.replace(",", "x")} at 30 fps ({probe})')
        info = json.loads(film.with_suffix('.cuts.json').read_text())
        info['frames'][4][0] += 3
        film.with_suffix('.cuts.json').write_text(json.dumps(info))
        r = subprocess.run([sys.executable, str(ROOT / 'engine' / 'check_sync.py'), str(film)], capture_output=True, text=True)
        say(r.returncode == 1 and 'should change at frame' in r.stdout, f'{tag}: a picture 3 frames late is caught')
        if keep:
            pathlib.Path(keep).mkdir(parents=True, exist_ok=True)
            shutil.copy(film, pathlib.Path(keep) / f"{tag.replace(' ', '-')}.mp4")


def main():
    keep = sys.argv[sys.argv.index('--keep') + 1] if '--keep' in sys.argv else None
    for name, size in (('north-star-plan.json', '1920,1080'), ('rain-short-plan.json', '1080,1920'),
                       ('boond-hindi-short-plan.json', '1080,1920')):
        film_test(name, size, keep)
    film_test('boond-hindi-short-plan.json', '1080,1920', keep, captions=True)
    # Animated graphics: every kind, upright, with subtitles drawn over them.
    film_test(ROOT / 'tests' / 'fixtures' / 'graphics-plan.json', '1080,1920', keep, captions=True)

    # Cards: words inside the frame, doodle white gone.
    for text in ('No map.', 'The star that never moves.',
                 'Nothing but the sky, the sea and a wooden boat far from home tonight'):
        img = card(text, (1920, 1080), Image.open(ROOT / 'tests' / 'doodle.png') if (ROOT / 'tests' / 'doodle.png').exists() else None)
        a = np.asarray(img.convert('L'))
        ink = np.argwhere(a < 128)
        y0, x0 = ink.min(0)
        y1, x1 = ink.max(0)
        say(x0 > 1920 * 0.05 and x1 < 1920 * 0.95 and y0 > 1080 * 0.05 and y1 < 1080 * 0.95,
            f'card "{text[:30]}" stays inside the frame')
    with tempfile.TemporaryDirectory() as tmp:
        p = pathlib.Path(tmp) / 'd.jpg'
        doodle(p)
        img = np.asarray(card('No map.', (1920, 1080), Image.open(p)).convert('L'))
        say((img > 250).mean() > 0.9, 'a doodle\'s white background disappears into the card')
        tall = card('The star that never moves.', (1080, 1920), Image.open(p))
        say(tall.size == (1080, 1920), 'cards also draw upright (9:16)')

    print('\nall good' if not bad else f'\n{bad} failing')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
