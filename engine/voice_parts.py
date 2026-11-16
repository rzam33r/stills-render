"""The narration as pieces, recorded in parts, joined into the film's voice.

    python3 engine/voice_parts.py PLAN PARTS_DIR OUT_DIR    (join)

A Hindi film's narration is a list of pieces: its sentences, paragraph by
paragraph (engine/hindi.py splits them). Chatterbox records them in one or
more parts at the same time (engine/chatterbox_hi.py, one GitHub computer
each); every part writes its pieces' sound and word times to
PARTS_DIR/part-N/. Joining puts them back in order with the engine's pauses
and writes OUT_DIR/voice.wav, words.json and cuts.json, exactly as a voice
recorded in one go.

Only numpy and soundfile: the render step joins the parts without
installing any voice.
"""
import json
import pathlib
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from hindi import sentences  # noqa: E402
from timing import narration_words, paragraphs, shot_starts, word_starts  # noqa: E402

RATE = 24000
LEAD = 0.20             # silence before the first word
BREATH = 0.45           # silence between paragraphs
SENTENCE_PAUSE = 0.32   # after each sentence
COMMA_PAUSE = 0.15      # after a long sentence's comma, where it was split
EDGE_BEFORE, EDGE_AFTER = 0.05, 0.10   # sound kept around a piece's words
ENDERS = '।॥.?!'


def spoken_text(say):
    """A shot's words as the voice reads them: *highlights* lose their stars."""
    return ' '.join(str(say).replace('*', '').split())


def pieces(plan):
    """[{'i', 'paragraph', 'text'}], in reading order."""
    shots = plan['shots']
    out = []
    for p, group in enumerate(paragraphs(shots)):
        text = ' '.join(spoken_text(shots[i]['say']) for i in group)
        for s in sentences(text):
            out.append({'i': len(out), 'paragraph': p, 'text': s})
    return out


def split(items, parts):
    """`parts` runs of whole pieces, in order, with about equal letters each."""
    total = sum(len(x['text']) for x in items) or 1
    bounds, start, acc, k = [], 0, 0, 1
    for idx, x in enumerate(items):
        acc += len(x['text'])
        if k < parts and acc >= total * k / parts and idx + 1 < len(items):
            bounds.append((start, idx + 1))
            start, k = idx + 1, k + 1
    bounds.append((start, len(items)))
    while len(bounds) < parts:
        bounds.append((len(items), len(items)))
    return bounds


def trim_to_words(a, timed, rate=RATE):
    """Cut the silence a voice leaves at both ends of a piece.

    Kokoro and Chatterbox pad what they say with quiet; spoken one sentence
    at a time, that made 1.2-second gaps (the first clear Hindi voice of
    bharat-mein-badhti-mehngai ran 84 s instead of 63). The piece is cut from
    just before its first word to just after its last, then to where the
    sound really starts and stops. Returns (samples, seconds cut from the
    start). `timed` is [(word, start, end)].
    """
    if not timed:
        return a, 0.0
    s0 = max(0.0, timed[0][1] - EDGE_BEFORE)
    e1 = min(len(a) / rate, timed[-1][2] + EDGE_AFTER)
    if e1 <= s0:
        return a, 0.0
    cut = np.asarray(a[int(s0 * rate):int(e1 * rate)], dtype=np.float32).copy()
    step = max(1, int(0.01 * rate))
    if len(cut) > 2 * step:
        rms = np.sqrt(np.convolve(cut ** 2, np.ones(step) / step, mode='same'))
        loud = np.flatnonzero(rms > max(0.005, 0.03 * float(np.abs(cut).max())))
        if len(loud):
            first = max(0, loud[0] - int(0.03 * rate))
            last = min(len(cut), loud[-1] + int(0.06 * rate))
            cut = cut[first:last]
            s0 += first / rate
    fade = min(len(cut), int(0.01 * rate))
    if fade:
        cut[:fade] *= np.linspace(0, 1, fade, dtype=cut.dtype)
        cut[-fade:] *= np.linspace(1, 0, fade, dtype=cut.dtype)
    return cut, s0


def write_outputs(plan, wav, tokens, missing, voice, speed, out_dir, rate=RATE, extra=None):
    """voice.wav, words.json and cuts.json, as every voice writes them."""
    shots = plan['shots']
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sf.write(out / 'voice.wav', wav, rate)
    says = [s['say'] for s in shots]
    starts = shot_starts(says, tokens)
    words = [{'shot': i, 'word': w, 'start': s}
             for (i, w), s in zip(narration_words(says), word_starts(says, tokens))]
    spoken = [t for t in tokens if t[1] is not None and any(c.isalnum() for c in t[0])]
    speech_end = max((t[2] or t[1]) for t in spoken) if spoken else len(wav) / rate
    (out / 'words.json').write_text(json.dumps(
        [{'text': t[0], 'start': t[1], 'end': t[2]} for t in tokens], indent=0, ensure_ascii=False))
    (out / 'cuts.json').write_text(json.dumps({
        'starts': starts, 'speech_end': speech_end, 'audio_seconds': len(wav) / rate,
        'voice': voice, 'speed': speed, 'words_without_time': missing, 'words': words,
        **(extra or {})}, indent=1, ensure_ascii=False))
    print(f'voice {voice} at {speed}: {len(wav) / rate:.1f} s, {len(spoken)} words timed, '
          f'{missing} pieces without a time, {len(shots)} shots')


def join(plan, parts_dir, out_dir, voice):
    """Put every part's pieces back in reading order and write the voice."""
    items = pieces(plan)
    got = {}
    for d in sorted(pathlib.Path(parts_dir).glob('part-*')):
        info = json.loads((d / 'part.json').read_text(encoding='utf-8'))
        for pc in info['pieces']:
            a, sr = sf.read(d / pc['file'], dtype='float32')
            if sr != RATE:
                raise SystemExit(f'ERROR {d / pc["file"]} is {sr} Hz, not {RATE}')
            got[pc['i']] = (a, pc)
    lost = [x['i'] for x in items if x['i'] not in got]
    if lost:
        raise SystemExit(f'ERROR the parts are missing pieces {lost}: a part did not finish')
    audio = [np.zeros(int(LEAD * RATE), dtype=np.float32)]
    at, para, tokens, missing = LEAD, 0, [], 0
    for x in items:
        if x['paragraph'] != para:
            audio.append(np.zeros(int(BREATH * RATE), dtype=np.float32))
            at += BREATH
            para = x['paragraph']
        a, pc = got[x['i']]
        timed = [w for w in pc['words'] if w.get('start') is not None]
        missing += sum(1 for w in x['text'].split() if any(c.isalnum() for c in w)) - len(timed)
        for w in timed:
            tokens.append((w['word'], at + w['start'], at + w['end'], ' '))
        audio.append(a)
        at += len(a) / RATE
        pause = SENTENCE_PAUSE if x['text'][-1:] in ENDERS else COMMA_PAUSE
        audio.append(np.zeros(int(pause * RATE), dtype=np.float32))
        at += pause
    checks = [got[x['i']][1] for x in items]
    extra = {'pieces': len(items), 'pieces_redone': sum(1 for c in checks if c.get('tries', 1) > 1),
             'worst_piece': max(checks, key=lambda c: c.get('cer', 0)).get('heard', '') if checks else '',
             'worst_piece_error': max((c.get('cer', 0) for c in checks), default=0)}
    write_outputs(plan, np.concatenate(audio), tokens, max(0, missing), voice, 1.0, out_dir, extra=extra)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    plan = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from voices import chosen_voice
    join(plan, sys.argv[2], sys.argv[3], chosen_voice(plan))
