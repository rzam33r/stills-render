"""Hindi narration recorded in parts and joined, and the voice each film gets.

    python3 tests/test_voice_parts.py

- Hindi films get Chatterbox (chatterbox-hi); English stays on Kokoro; a
  plan naming a Kokoro Hindi voice keeps it; the plan check agrees.
- A long Hindi film is recorded in parts (about 12 minutes of speech each,
  at most 8); a short one in one part; English always in one.
- The narration's pieces are its sentences in order; any number of parts
  covers every piece exactly once, in runs of about equal length.
- Joining puts the parts back in order with the engine's pauses, every word
  keeps its time, the shots start in order, and a missing part is an error
  that says so.
- The recogniser's score ignores spellings that sound the same.
"""
import json
import pathlib
import sys
import tempfile

import numpy as np
import soundfile as sf

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
from check_plan import check  # noqa: E402
from hindi import cer  # noqa: E402
from voice_parts import BREATH, LEAD, RATE, SENTENCE_PAUSE, join, pieces, split  # noqa: E402
from voices import voice_engine, voice_parts  # noqa: E402

bad = 0


def say(ok, msg):
    global bad
    bad += not ok
    print(('ok   ' if ok else 'FAIL ') + msg)


boond = json.loads((ROOT / 'examples' / 'boond-hindi-short-plan.json').read_text(encoding='utf-8'))
bharat = json.loads((ROOT / 'tests' / 'fixtures' / 'bharat-mein-badhti-mehngai-plan.json').read_text(encoding='utf-8'))
english = json.loads((ROOT / 'examples' / 'rain-short-plan.json').read_text(encoding='utf-8'))

# Which voice
say(voice_engine({k: v for k, v in boond.items() if k != 'voice'}, False)[:2] == ('chatterbox', 'chatterbox-hi'),
    'a Hindi film gets Chatterbox')
say(voice_engine(english, False)[:2] == ('kokoro', 'am_michael'), 'an English film stays on Kokoro')
say(voice_engine(dict(boond, voice='hm_omega'), False)[:2] == ('kokoro', 'hm_omega'), 'a plan naming hm_omega keeps Kokoro')
errs = check(dict(boond, voice='chatterbox-hi'))[0]
say(not errs, 'the plan check accepts chatterbox-hi for Hindi' + (f': {errs}' if errs else ''))
errs = check(dict(english, voice='chatterbox-hi'))[0]
say(any('Hindi voice' in e for e in errs), 'the plan check refuses chatterbox-hi for an English film')

# How many parts
long45 = {'language': 'hi', 'shots': [{'say': 'क' * 13 * 60 * 45}]}
say(voice_parts(boond, 'chatterbox') == 1 and voice_parts(bharat, 'chatterbox') == 1, 'a short Hindi film is one part')
say(voice_parts(long45, 'chatterbox') == 4, f'a 45-minute Hindi film is {voice_parts(long45, "chatterbox")} parts')
say(voice_parts({'shots': [{'say': 'क' * 13 * 60 * 200}]}, 'chatterbox') == 8, 'never more than 8 parts')
say(voice_parts(long45, 'kokoro') == 1, 'Kokoro is always one part')
say(voice_parts(boond, 'chatterbox', '2') == 2, 'a test can ask for 2 parts')

# Pieces and parts
items = pieces(bharat)
text = ' '.join(s['say'] for s in bharat['shots']).split()
say([w for x in items for w in x['text'].split()] == text, f'the {len(items)} pieces hold every word in order')
for n in (1, 2, 3, 5):
    runs = split(items, n)
    covered = [i for lo, hi in runs for i in range(lo, hi)]
    sizes = [sum(len(items[i]['text']) for i in range(lo, hi)) for lo, hi in runs]
    even = max(sizes) <= 2.2 * (sum(sizes) / n) + 60
    say(len(runs) == n and covered == list(range(len(items))) and even, f'{n} part(s) cover every piece once: {sizes} letters')
say(split(items[:2], 4)[2:] == [(2, 2), (2, 2)], 'more parts than pieces leaves the extra parts empty')


# Joining
def fake_parts(plan, n, where):
    its = pieces(plan)
    for k, (lo, hi) in enumerate(split(its, n)):
        d = pathlib.Path(where) / f'part-{k}'
        d.mkdir(parents=True)
        rep = []
        for x in its[lo:hi]:
            words = [w for w in x['text'].split() if any(c.isalnum() for c in w)]
            secs = 0.35 * len(words)
            sf.write(d / f'piece-{x["i"]:04d}.wav', np.full(int(secs * RATE), 0.1, dtype=np.float32), RATE)
            rep.append({'i': x['i'], 'file': f'piece-{x["i"]:04d}.wav', 'cer': 0.1, 'tries': 1 + (x['i'] == 3), 'heard': x['text'],
                        'words': [{'word': w, 'start': 0.35 * j, 'end': 0.35 * j + 0.3} for j, w in enumerate(words)]})
        (d / 'part.json').write_text(json.dumps({'part': k, 'parts': n, 'pieces': rep}, ensure_ascii=False))
    return its


for n in (1, 3):
    tmp = tempfile.mkdtemp()
    its = fake_parts(bharat, n, tmp + '/parts')
    join(bharat, tmp + '/parts', tmp + '/voice', 'chatterbox-hi')
    c = json.loads(pathlib.Path(tmp, 'voice', 'cuts.json').read_text())
    a, _ = sf.read(pathlib.Path(tmp, 'voice', 'voice.wav'))
    words = sum(len([w for w in x['text'].split() if any(ch.isalnum() for ch in w)]) for x in its)
    expect = LEAD + sum(0.35 * len([w for w in x['text'].split() if any(ch.isalnum() for ch in w)]) for x in its) \
        + len(its) * SENTENCE_PAUSE
    say(c['words_without_time'] == 0 and len(c['words']) == words, f'{n} part(s) joined: every one of the {words} words has a time')
    say(all(b > a_ for a_, b in zip(c['starts'], c['starts'][1:])) and len(c['starts']) == len(bharat['shots']),
        f'{n} part(s) joined: the {len(c["starts"])} shots start in order')
    say(abs(len(a) / RATE - expect) < 0.05 and c['pieces_redone'] == 1, f'{n} part(s) joined: {len(a) / RATE:.2f} s with the pauses, one piece redone')
    say(c['starts'][0] == 0 and abs(c['words'][0]['start'] - LEAD) < 0.01,
        'the first picture opens the film and the first word comes after the lead-in')

tmp = tempfile.mkdtemp()
fake_parts(bharat, 3, tmp + '/parts')
import shutil  # noqa: E402
shutil.rmtree(tmp + '/parts/part-1')
try:
    join(bharat, tmp + '/parts', tmp + '/voice', 'chatterbox-hi')
    say(False, 'a missing part stops the join')
except SystemExit as e:
    say('did not finish' in str(e), f'a missing part stops the join: {e}')

two = {'title': 'T', 'language': 'hi', 'shots': [{'say': 'एक।', 'picture': '001'}, {'say': 'दो।', 'picture': '002', 'paragraph': True}]}
tmp = tempfile.mkdtemp()
fake_parts(two, 1, tmp + '/parts')
join(two, tmp + '/parts', tmp + '/voice', 'chatterbox-hi')
c = json.loads(pathlib.Path(tmp, 'voice', 'cuts.json').read_text())
gap = c['words'][1]['start'] - c['words'][0]['start']
say(abs(gap - (0.35 + SENTENCE_PAUSE + BREATH)) < 0.01, f'a new paragraph adds the breath: {gap:.2f} s between their words')

# The recogniser's score
say(cer('फ़ीस बढ़ती है।', 'फीस बढती है') == 0, 'a missing nukta or full stop is not a mistake')
say(cer('महँगाई', 'महंगाई') == 0, 'chandrabindu and anusvara count as the same')
say(cer('आपकी तनख्वाह', 'अपकी') > 0.5, 'a missing word is a mistake')

print('\nall good' if not bad else f'\n{bad} failed')
sys.exit(1 if bad else 0)
