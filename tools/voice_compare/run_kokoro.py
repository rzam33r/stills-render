"""Kokoro hm_omega, as films had it before 15 Nov 2026 (one call for the whole
script, no Hindi fixes) and as the engine has it now (engine/voice.py).

    python run_kokoro.py PLAN OUT_DIR
"""
import json
import pathlib
import subprocess
import sys

import numpy as np
from kokoro import KPipeline

from common import ROOT, Timer, save

plan, out = sys.argv[1:3]
p = json.loads(pathlib.Path(plan).read_text(encoding='utf-8-sig'))
text = ' '.join(s['say'].replace('*', '') for s in p['shots'])
pipe = KPipeline(lang_code='h')
with Timer() as t:
    audio = np.concatenate([np.asarray(r.audio, dtype=np.float32) for r in pipe(text, voice='hm_omega', speed=1.0, split_pattern=None) if r.audio is not None])
save(out, 'kokoro-before-fixes', audio, 24000, t.seconds, {'model': 'hexgrad/Kokoro-82M', 'licence': 'Apache-2.0', 'voice': 'hm_omega'})
with Timer() as t:
    subprocess.run([sys.executable, str(ROOT / 'engine' / 'voice.py'), plan, '/tmp/kokoro-now'], check=True)
import soundfile as sf  # noqa: E402
a, sr = sf.read('/tmp/kokoro-now/voice.wav', dtype='float32')
save(out, 'kokoro-now', a, sr, t.seconds, {'model': 'hexgrad/Kokoro-82M (engine, with the Hindi fixes)', 'licence': 'Apache-2.0', 'voice': 'hm_omega'})
