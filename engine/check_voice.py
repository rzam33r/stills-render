"""Check a voice's word times against its sound.

    python3 engine/check_voice.py PLAN VOICE_DIR [--strict]

check_sync.py proves the pictures change where the word times say; this
proves the word times are where the words are. Wherever a sentence starts
after a pause, the sound must begin close to the time its first word was
given (Hindi word times come from a speech recogniser, engine/align_hi.py;
on 16 Nov 2026 a wrong setting there put words out of order while every cut
still "matched").

Prints how far each sentence start is from its sound. With --strict it
fails when the median is over 60 ms or any start is over 250 ms away (the
tests); without, it only reports (a film is not held back by it).
"""
import json
import pathlib
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from voice_parts import pieces  # noqa: E402

QUIET_BEFORE = 0.15   # a sentence start has at least this much quiet before it


def onsets(a, rate):
    step = int(0.01 * rate)
    frames = len(a) // step
    rms = np.sqrt(np.mean(a[:frames * step].reshape(frames, step) ** 2, axis=1))
    loud = rms > max(0.004, 0.04 * float(rms.max() or 1))
    need = int(QUIET_BEFORE / 0.01)
    out = []
    for i in range(need, frames):
        if loud[i] and not loud[i - need:i].any():
            out.append(i * 0.01)
    return np.array(out)


def main(plan_path, voice_dir, strict=False):
    plan = json.loads(pathlib.Path(plan_path).read_text(encoding='utf-8-sig'))
    a, rate = sf.read(pathlib.Path(voice_dir) / 'voice.wav', dtype='float32')
    if a.ndim > 1:
        a = a.mean(axis=1)
    words = [w for w in json.loads((pathlib.Path(voice_dir) / 'words.json').read_text(encoding='utf-8'))
             if w.get('start') is not None and any(c.isalnum() for c in w['text'])]
    firsts, k = [], 0
    for x in pieces(plan):
        n = sum(1 for w in x['text'].split() if any(c.isalnum() for c in w))
        if k < len(words):
            firsts.append((words[k]['start'], x['text']))
        k += n
    starts = onsets(a, rate)
    if not len(starts) or not firsts:
        print('no sentence starts to check')
        return 0
    gaps = []
    for t, text in firsts:
        near = starts[np.argmin(np.abs(starts - t))]
        gaps.append((abs(near - t), near - t, text))
    d = np.array([g[0] for g in gaps])
    print(f'{len(gaps)} sentence starts: median {np.median(d) * 1000:.0f} ms from their sound, '
          f'largest {d.max() * 1000:.0f} ms')
    for g, signed, text in sorted(gaps, reverse=True)[:3]:
        print(f'  {signed * 1000:+.0f} ms  {text[:60]}')
    bad = np.median(d) > 0.06 or d.max() > 0.25
    if bad:
        print('WARNING the word times are not where the words are')
    return 1 if (strict and bad) else 0


if __name__ == '__main__':
    args = [x for x in sys.argv[1:] if x != '--strict']
    if len(args) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(args[0], args[1], '--strict' in sys.argv))
