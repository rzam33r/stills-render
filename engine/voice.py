"""Speak the narration and record when each shot starts.

    python3 engine/voice.py plan.json OUT_DIR

Writes, in OUT_DIR:
  voice.wav   the narration (24 kHz mono)
  words.json  every word the voice said: [{"text", "start", "end"}] in seconds
  cuts.json   {"starts": [seconds per shot], "speech_end": seconds,
               "voice": ..., "speed": ...}

The narration is spoken one paragraph at a time, each paragraph as one piece,
so sentences flow into each other the way a narrator reads them; a short
breath separates paragraphs. Kokoro reports when it says each word, and
timing.py turns that into the moment each shot's first word begins.
"""
import json
import pathlib
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from timing import paragraphs, shot_starts  # noqa: E402

RATE = 24000
LEAD = 0.20       # silence before the first word
BREATH = 0.45     # silence between paragraphs


def main(plan_path, out_dir):
    from kokoro import KPipeline

    plan = json.loads(pathlib.Path(plan_path).read_text(encoding='utf-8-sig'))
    shots = plan['shots']
    voice = plan.get('voice') or 'am_michael'
    speed = float(plan.get('speed') or 1.0)
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    pipe = KPipeline(lang_code='b' if voice[:1] == 'b' else 'a')
    audio = [np.zeros(int(LEAD * RATE), dtype=np.float32)]
    at = LEAD
    tokens = []
    missing = 0
    for p, group in enumerate(paragraphs(shots)):
        if p:
            audio.append(np.zeros(int(BREATH * RATE), dtype=np.float32))
            at += BREATH
        text = ' '.join(shots[i]['say'].strip() for i in group)
        for r in pipe(text, voice=voice, speed=speed, split_pattern=None):
            if r.audio is None:
                continue
            a = np.asarray(r.audio, dtype=np.float32)
            for t in r.tokens or []:
                s = getattr(t, 'start_ts', None)
                e = getattr(t, 'end_ts', None)
                if s is None:
                    missing += 1
                tokens.append((t.text, None if s is None else at + s, None if e is None else at + e,
                               getattr(t, 'whitespace', None)))
            audio.append(a)
            at += len(a) / RATE
    wav = np.concatenate(audio)
    sf.write(out / 'voice.wav', wav, RATE)

    starts = shot_starts([s['say'] for s in shots], tokens)
    spoken = [t for t in tokens if t[1] is not None and any(c.isalnum() for c in t[0])]
    speech_end = max((t[2] or t[1]) for t in spoken) if spoken else at
    (out / 'words.json').write_text(json.dumps(
        [{'text': t[0], 'start': t[1], 'end': t[2]} for t in tokens], indent=0))
    (out / 'cuts.json').write_text(json.dumps({
        'starts': starts, 'speech_end': speech_end, 'audio_seconds': len(wav) / RATE,
        'voice': voice, 'speed': speed, 'words_without_time': missing}, indent=1))
    n_words = sum(1 for t in spoken)
    print(f'voice {voice} at {speed}: {len(wav) / RATE:.1f} s, {n_words} words timed, '
          f'{missing} pieces without a time, {len(shots)} shots')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
