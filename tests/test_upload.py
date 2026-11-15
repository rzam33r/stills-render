"""What arrives from the upload page becomes a story the engine can make.

    python3 tests/test_upload.py

- Pictures saved by Google Flow / Flow Connect ("1 - Medium shot of a
  man.jpg") are matched to the plan's "001" by the number at the start.
- A picture already named the plan's way keeps its name.
- Two files for one picture are refused, naming both.
- A plan pasted on the upload page (sent as its own plan.json) wins over the
  one in the ZIP; with neither, the error says how to add one.
- An Azure voice without the Azure key falls back to the language's Kokoro
  voice with a warning; Kokoro voices and a set key are left alone.
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

e, v, w = voice_engine({'language': 'hi', 'voice': 'hi-IN-MadhurNeural'}, False)
say((e, v) == ('kokoro', 'hm_omega') and 'AZURE_SPEECH_KEY' in w, 'Azure voice without a key falls back to hm_omega')
e, v, w = voice_engine({'language': 'en', 'voice': 'en-US-AndrewNeural'}, False)
say((e, v) == ('kokoro', 'am_michael') and w, 'English Azure voice without a key falls back to am_michael')
say(voice_engine({'language': 'hi', 'voice': 'hi-IN-MadhurNeural'}, True) == ('azure', 'hi-IN-MadhurNeural', ''),
    'with the key, the Azure voice is used')
say(voice_engine({'language': 'hi'}, False) == ('kokoro', 'hm_omega', ''), 'no voice: the language default')
say(voice_engine({'voice': 'hf_beta', 'language': 'hi'}, False) == ('kokoro', 'hf_beta', ''), 'a Kokoro voice is kept')

print('\nall good' if not bad else f'\n{bad} failed')
sys.exit(1 if bad else 0)
