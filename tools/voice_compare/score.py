"""Score every take: how well a strong recogniser (Whisper large-v3, run by
faster-whisper) understands it, against the script.

    python score.py PLAN TAKES_DIR

CER is the share of the script's letters the recogniser got wrong (lower is
clearer). Spelling that sounds the same is not counted: nukta, chandrabindu
and punctuation are removed from both sides first.
"""
import json
import pathlib
import re
import sys
import unicodedata

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
from scipy.signal import resample_poly

plan, takes = sys.argv[1], pathlib.Path(sys.argv[2])
p = json.loads(pathlib.Path(plan).read_text(encoding='utf-8-sig'))
script = ' '.join(s['say'].replace('*', '') for s in p['shots'])


def norm(t):
    t = unicodedata.normalize('NFD', t).replace('़', '').replace('ँ', 'ं')
    t = unicodedata.normalize('NFC', t)
    return ''.join(c for c in t if unicodedata.category(c)[0] in 'LMN')


def cer(ref, hyp):
    a, b = norm(ref), norm(hyp)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] / max(1, len(a))


model = WhisperModel('large-v3', device='cpu', compute_type='int8', cpu_threads=4)
rows = []
for info_path in sorted(takes.glob('*/*.json')):
    info = json.loads(info_path.read_text())
    wav = info_path.with_suffix('.wav')
    a, sr = sf.read(str(wav), dtype='float32')
    if a.ndim > 1:
        a = a.mean(axis=1)
    # Whisper hears 16 kHz; handing it the samples skips its own file reader
    # (PyAV), whose newest version broke faster-whisper on 15 Nov 2026.
    a = resample_poly(a, 16000, sr).astype(np.float32) if sr != 16000 else a
    segs, _ = model.transcribe(a, language='hi', beam_size=5, vad_filter=False,
                               condition_on_previous_text=False)
    heard = ' '.join(s.text.strip() for s in segs)
    info['cer'] = round(cer(script, heard), 3)
    info['heard'] = heard
    rows.append(info)
    print(info['name'], info['cer'], heard[:120], flush=True)
rows.sort(key=lambda r: r['cer'])
(takes / 'scores.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1))
lines = ['## Hindi voices on bharat-mein-badhti-mehngai', '',
         'Lower CER = the recogniser understood more of the script. Compute = seconds of GitHub CPU per second of speech.', '',
         '| take | CER | length | compute per second | licence |', '|---|---|---|---|---|']
lines += [f"| {r['name']} | {r['cer']:.1%} | {r['audio_seconds']} s | {r['compute_per_audio_second']} | {r.get('licence', '')} |" for r in rows]
print('\n'.join(lines))
with open(sys.argv[3] if len(sys.argv) > 3 else '/dev/null', 'a') as f:
    f.write('\n'.join(lines) + '\n')
