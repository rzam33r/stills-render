"""Shared helpers for the Hindi voice comparison (tools/voice_compare).

Every candidate reads the same plan sentence by sentence; each sentence is
trimmed to its sound and joined with the engine's own sentence pause, so
the voices differ only in how they speak.
"""
import json
import pathlib
import sys
import time

import numpy as np
import soundfile as sf

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'engine'))
from hindi import sentences  # noqa: E402

PAUSE = 0.32


def plan_sentences(plan_path):
    plan = json.loads(pathlib.Path(plan_path).read_text(encoding='utf-8-sig'))
    text = ' '.join(s['say'].replace('*', '') for s in plan['shots'])
    return sentences(text)


def trim(a, rate, keep_before=0.03, keep_after=0.06):
    a = np.asarray(a, dtype=np.float32).reshape(-1)
    if not len(a):
        return a
    step = max(1, int(0.01 * rate))
    rms = np.sqrt(np.convolve(a ** 2, np.ones(step) / step, mode='same'))
    loud = np.flatnonzero(rms > max(0.005, 0.03 * float(np.abs(a).max() or 1)))
    if not len(loud):
        return a
    return a[max(0, loud[0] - int(keep_before * rate)):min(len(a), loud[-1] + int(keep_after * rate))]


def join(pieces, rate):
    out = [np.zeros(int(0.25 * rate), dtype=np.float32)]
    for p in pieces:
        out += [trim(p, rate), np.zeros(int(PAUSE * rate), dtype=np.float32)]
    return np.concatenate(out)


class Timer:
    def __enter__(self):
        self.t = time.time()
        return self

    def __exit__(self, *a):
        self.seconds = time.time() - self.t


def save(out_dir, name, audio, rate, seconds, extra=None):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sf.write(out / f'{name}.wav', audio, rate)
    info = {'name': name, 'audio_seconds': round(len(audio) / rate, 2),
            'compute_seconds': round(seconds, 1), **(extra or {})}
    info['compute_per_audio_second'] = round(seconds / max(info['audio_seconds'], 0.01), 2)
    (out / f'{name}.json').write_text(json.dumps(info, ensure_ascii=False))
    print(json.dumps(info, ensure_ascii=False))
