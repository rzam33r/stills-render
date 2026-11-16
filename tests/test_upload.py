"""What arrives from the upload page becomes a story the engine can make.

    python3 tests/test_upload.py

- Pictures saved by Google Flow / Flow Connect ("1 - Medium shot of a
  man.jpg") are matched to the plan's "001" by the number at the start.
- A picture already named the plan's way keeps its name.
- Two files for one picture are refused, naming both.
- A plan pasted on the upload page (sent as its own plan.json) wins over the
  one in the ZIP; with neither, the error says how to add one.
- A ZIP the page sent in 8 MB pieces is joined in order and must match the
  page's size and SHA-256 (a missing or damaged piece stops the film); a ZIP
  sent whole still works.
- An Azure voice without the Azure key falls back to the language's default
  voice (Chatterbox for Hindi, Kokoro for English) with a warning; Kokoro
  voices and a set key are left alone.
"""
import io
import json
import pathlib
import sys
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
import unpack  # noqa: E402
import join_upload  # noqa: E402
from voices import voice_engine  # noqa: E402

bad = 0


def say(ok, msg):
    global bad
    bad += not ok
    print(('ok   ' if ok else 'FAIL ') + msg)


def make_zip(path, files):
    with zipfile.ZipFile(path, 'w') as z:
        for name, data in files.items():
            z.writestr(name, data)


def run(files, plan_file=None):
    tmp = pathlib.Path(tempfile.mkdtemp())
    make_zip(tmp / 'story.zip', files)
    out = io.StringIO()
    old, sys.stdout = sys.stdout, out
    try:
        code = unpack.main(tmp / 'story.zip', tmp / 'story', plan_file)
    finally:
        sys.stdout = old
    pics = sorted(p.name for p in (tmp / 'story' / 'pictures').iterdir()) if code == 0 else []
    plan = json.loads((tmp / 'story' / 'plan.json').read_text()) if code == 0 else None
    return code, out.getvalue(), pics, plan


plan = {'title': 'T', 'shots': [{'say': 'a', 'picture': '001'}, {'say': 'b', 'picture': '002'},
                                  {'say': 'c', 'card': 'x', 'doodle': '012'}]}
P = json.dumps(plan)

code, out, pics, _ = run({'Bharath_inflation/plan.json': P,
                          'Bharath_inflation/1 - Medium shot of a simple stick-figure.jpg': b'x',
                          'Bharath_inflation/2 - Close-up of a man (1).jpg': b'x',
                          'Bharath_inflation/12_doodle.png': b'x'})
say(code == 0 and pics == ['001.jpg', '002.jpg', '012.png'], f'Flow names are matched by their number: {pics}')

code, out, pics, _ = run({'plan.json': P, '001.png': b'x', '2.webp': b'x', 'notes.png': b'x'})
say(code == 0 and pics == ['001.png', '002.webp', 'notes.png'], f'plan names are kept, others left alone: {pics}')

code, out, pics, _ = run({'plan.json': P, '001.png': b'x', '1 - again.jpg': b'x'})
say(code == 1 and '001.png' in out and '1 - again.jpg' in out, 'two files for one picture are refused, naming both')

pasted = dict(plan, title='Pasted')
tmp = pathlib.Path(tempfile.mkdtemp())
(tmp / 'plan.json').write_text(json.dumps(pasted))
code, out, pics, got = run({'plan.json': P, '1 - a.jpg': b'x'}, tmp / 'plan.json')
say(code == 0 and got['title'] == 'Pasted' and 'pasted' in out, 'a pasted plan wins over the ZIP\'s')
code, out, pics, got = run({'1 - a.jpg': b'x', '2 - b.jpg': b'x'}, tmp / 'plan.json')
say(code == 0 and pics == ['001.jpg', '002.jpg'], 'a ZIP of pictures only works with a pasted plan')
code, out, pics, _ = run({'1 - a.jpg': b'x'})
say(code == 1 and 'paste' in out, 'no plan anywhere: the error says how to add one')

import hashlib  # noqa: E402
import os  # noqa: E402


def send_in_pieces(data, name, where, size=8 * 1024 * 1024):
    where.mkdir(parents=True, exist_ok=True)
    chunks = [data[i:i + size] for i in range(0, len(data), size)] or [b'']
    for i, c in enumerate(chunks, 1):
        (where / f'{name}.part{i:03d}').write_bytes(c)
    (where / f'{name}.parts.json').write_text(json.dumps(
        {'name': name, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'parts': len(chunks)}))
    return len(chunks)


def joined(where):
    out = io.StringIO()
    old, sys.stdout = sys.stdout, out
    try:
        code = join_upload.main(where, where / 'out')
    finally:
        sys.stdout = old
    return code, out.getvalue()


big = os.urandom(20 * 1024 * 1024 + 12345)
tmp = pathlib.Path(tempfile.mkdtemp())
n = send_in_pieces(big, 'royal-enfield-legend-india.zip', tmp / 'a')
code, out = joined(tmp / 'a')
say(code == 0 and n == 3 and (tmp / 'a' / 'out' / 'royal-enfield-legend-india.zip').read_bytes() == big,
    f'a ZIP sent in {n} pieces is joined back exactly: {out.strip()}')
send_in_pieces(big, 'x.zip', tmp / 'b')
(tmp / 'b' / 'x.zip.part002').unlink()
code, out = joined(tmp / 'b')
say(code == 1 and 'missing: [2]' in out, 'a missing piece is named and stops the film')
send_in_pieces(big, 'x.zip', tmp / 'c')
(tmp / 'c' / 'x.zip.part003').write_bytes(b'damaged')
code, out = joined(tmp / 'c')
say(code == 1 and 'not the one the page sent' in out and not (tmp / 'c' / 'out' / 'x.zip').exists(),
    'a damaged piece fails the fingerprint and nothing is unpacked')
(tmp / 'd').mkdir()
(tmp / 'd' / 'old.zip').write_bytes(b'PK whole')
code, out = joined(tmp / 'd')
say(code == 0 and (tmp / 'd' / 'out' / 'old.zip').read_bytes() == b'PK whole', 'a ZIP sent whole still works')
(tmp / 'e').mkdir()
code, out = joined(tmp / 'e')
say(code == 1 and 'nothing' in out, 'no ZIP at all is an error')
n = send_in_pieces(b'0123456789' * 3, 'ten.zip', tmp / 'f', size=3)
code, out = joined(tmp / 'f')
say(code == 0 and (tmp / 'f' / 'out' / 'ten.zip').read_bytes() == b'0123456789' * 3,
    f'{n} pieces join in number order, not name order (part010 after part009)')

e, v, w = voice_engine({'language': 'hi', 'voice': 'hi-IN-MadhurNeural'}, False)
say((e, v) == ('chatterbox', 'chatterbox-hi') and 'AZURE_SPEECH_KEY' in w, 'Hindi Azure voice without a key falls back to Chatterbox')
e, v, w = voice_engine({'language': 'en', 'voice': 'en-US-AndrewNeural'}, False)
say((e, v) == ('kokoro', 'am_michael') and w, 'English Azure voice without a key falls back to am_michael')
say(voice_engine({'language': 'hi', 'voice': 'hi-IN-MadhurNeural'}, True) == ('azure', 'hi-IN-MadhurNeural', ''),
    'with the key, the Azure voice is used')
say(voice_engine({'language': 'hi'}, False) == ('chatterbox', 'chatterbox-hi', ''), 'no voice: the Hindi default, Chatterbox')
say(voice_engine({'voice': 'hf_beta', 'language': 'hi'}, False) == ('kokoro', 'hf_beta', ''), 'a Kokoro voice is kept')

print('\nall good' if not bad else f'\n{bad} failed')
sys.exit(1 if bad else 0)
