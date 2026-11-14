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

Voices:
  - Kokoro (free, on the runner): English voices like am_michael, and the
    Hindi voices hm_omega, hm_psi, hf_alpha and hf_beta. For English Kokoro
    reports when it says each word. For Hindi it does not, so the times are
    worked out from how long the voice holds each sound (hindi_words below).
  - Azure neural voices, optional (any voice named like hi-IN-MadhurNeural).
    Azure reports every word's time too. They need the repository secrets
    AZURE_SPEECH_KEY and AZURE_SPEECH_REGION.

The plan picks with "language" ("en" or "hi") and optionally "voice".
"""
import json
import pathlib
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from timing import narration_words, paragraphs, shot_starts, word_starts  # noqa: E402

RATE = 24000
LEAD = 0.20       # silence before the first word
BREATH = 0.45     # silence between paragraphs
DEFAULT_VOICE = {'en': 'am_michael', 'hi': 'hm_omega'}
FRAME = 600 / RATE   # one unit of Kokoro's sound lengths, in seconds
NOT_A_WORD = set(' ;:,.!?—…"()“”«»।॥-\'')


def spoken_text(say):
    """What the voice reads: the words without the *highlight* marks."""
    return say.replace('*', '').strip()


def is_azure(voice):
    return voice.endswith('Neural') and voice[2:3] == '-'


def azure_voice(plan, voice, speed):
    """Speak with an Azure neural voice; returns (samples, tokens)."""
    import os
    from xml.sax.saxutils import escape
    try:
        import azure.cognitiveservices.speech as sdk
    except ImportError:
        raise SystemExit('The Azure voice library is not installed (locks/voice-azure.txt).')
    key, region = os.environ.get('AZURE_SPEECH_KEY'), os.environ.get('AZURE_SPEECH_REGION')
    if not key or not region:
        raise SystemExit('The voice ' + voice + ' needs an Azure Speech key: add the repository secrets '
                         'AZURE_SPEECH_KEY and AZURE_SPEECH_REGION (Settings > Secrets and variables > Actions).')
    shots = plan['shots']
    lang = voice[:5]
    rate = f'{round((speed - 1) * 100):+d}%'
    parts = []
    for p, group in enumerate(paragraphs(shots)):
        if p:
            parts.append(f'<break time="{int(BREATH * 1000)}ms"/>')
        parts.append(escape(' '.join(spoken_text(shots[i]['say']) for i in group)))
    ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">'
            f'<voice name="{voice}"><prosody rate="{rate}">{"".join(parts)}</prosody></voice></speak>')
    cfg = sdk.SpeechConfig(subscription=key, region=region)
    cfg.set_speech_synthesis_output_format(sdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm)
    synth = sdk.SpeechSynthesizer(speech_config=cfg, audio_config=None)
    tokens = []

    def on_word(evt):
        if evt.boundary_type == sdk.SpeechSynthesisBoundaryType.Word:
            start = evt.audio_offset / 1e7
            tokens.append((evt.text, LEAD + start, LEAD + start + evt.duration.total_seconds(), ' '))

    synth.synthesis_word_boundary.connect(on_word)
    result = synth.speak_ssml_async(ssml).get()
    if result.reason != sdk.ResultReason.SynthesizingAudioCompleted:
        d = result.cancellation_details
        raise SystemExit(f'Azure did not speak the narration: {d.reason} {d.error_details}')
    import io
    audio, rate_hz = sf.read(io.BytesIO(result.audio_data), dtype='float32')
    if rate_hz != RATE:
        raise SystemExit(f'Azure returned {rate_hz} Hz audio, expected {RATE}')
    audio = np.concatenate([np.zeros(int(LEAD * RATE), dtype=np.float32), audio])
    return audio, tokens, 0


def hindi_words(graphemes, phonemes, pred_dur, vocab):
    """When each word of a Hindi chunk starts and ends, in seconds from the
    start of the chunk's sound: [(word, start, end)].

    Kokoro speaks the chunk's phonemes, one sound length (in units of 600
    samples) per phoneme it knows, between a start and an end marker. Words
    are separated by spaces in the phonemes, so adding up the lengths gives
    the moment each word's first sound begins. The phoneme words are then
    paired with the written words; when espeak split or joined a word and
    the counts differ, each written word takes the phoneme word at the same
    place in the line."""
    kept = [p for p in phonemes if p in vocab]
    durs = [int(d) for d in pred_dur]
    if len(durs) < len(kept) + 2:
        return []
    # Words are what sits between spaces. Punctuation counts for time but
    # does not start or end a word: espeak writes some Hindi sounds with a
    # full stop inside the word ("pəhˈaːr.õ" for पहाड़ों), so only a space
    # separates words.
    t = durs[0] * FRAME
    spans, cur = [], None
    for ch, d in zip(kept, durs[1:len(kept) + 1]):
        if ch == ' ':
            if cur is not None:
                spans.append(cur)
                cur = None
        elif ch not in NOT_A_WORD:
            if cur is None:
                cur = [t, t + d * FRAME]
            else:
                cur[1] = t + d * FRAME
        t += d * FRAME
    if cur is not None:
        spans.append(cur)
    written = [w for w in graphemes.split() if any(c.isalnum() for c in w)]
    if not written or not spans:
        return []
    out = []
    for k, w in enumerate(written):
        j = k if len(spans) == len(written) else min(len(spans) - 1, round(k * len(spans) / len(written)))
        out.append((w, spans[j][0], spans[j][1]))
    return out


def kokoro_voice(plan, voice, speed):
    """Speak with Kokoro; returns (samples, tokens, pieces without a time)."""
    from kokoro import KPipeline

    shots = plan['shots']
    code = voice[:1] if voice[:1] in 'abh' else 'a'
    pipe = KPipeline(lang_code=code)
    audio = [np.zeros(int(LEAD * RATE), dtype=np.float32)]
    at = LEAD
    tokens = []
    missing = 0
    for p, group in enumerate(paragraphs(shots)):
        if p:
            audio.append(np.zeros(int(BREATH * RATE), dtype=np.float32))
            at += BREATH
        text = ' '.join(spoken_text(shots[i]['say']) for i in group)
        for r in pipe(text, voice=voice, speed=speed, split_pattern=None):
            if r.audio is None:
                continue
            a = np.asarray(r.audio, dtype=np.float32)
            if code == 'h':
                timed = hindi_words(r.graphemes, r.phonemes, r.pred_dur.tolist(), pipe.model.vocab)
                if not timed:
                    missing += len(r.graphemes.split())
                for w, s, e in timed:
                    tokens.append((w, at + s, at + e, ' '))
            for t in r.tokens or []:
                s = getattr(t, 'start_ts', None)
                e = getattr(t, 'end_ts', None)
                if s is None:
                    missing += 1
                tokens.append((t.text, None if s is None else at + s, None if e is None else at + e,
                               getattr(t, 'whitespace', None)))
            audio.append(a)
            at += len(a) / RATE
    return np.concatenate(audio), tokens, missing


def main(plan_path, out_dir):
    plan = json.loads(pathlib.Path(plan_path).read_text(encoding='utf-8-sig'))
    shots = plan['shots']
    lang = plan.get('language', 'en')
    voice = plan.get('voice') or DEFAULT_VOICE.get(lang, 'am_michael')
    speed = float(plan.get('speed') or 1.0)
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    wav, tokens, missing = (azure_voice if is_azure(voice) else kokoro_voice)(plan, voice, speed)
    sf.write(out / 'voice.wav', wav, RATE)

    says = [s['say'] for s in shots]
    starts = shot_starts(says, tokens)
    words = [{'shot': i, 'word': w, 'start': s}
             for (i, w), s in zip(narration_words(says), word_starts(says, tokens))]
    spoken = [t for t in tokens if t[1] is not None and any(c.isalnum() for c in t[0])]
    speech_end = max((t[2] or t[1]) for t in spoken) if spoken else len(wav) / RATE
    (out / 'words.json').write_text(json.dumps(
        [{'text': t[0], 'start': t[1], 'end': t[2]} for t in tokens], indent=0))
    (out / 'cuts.json').write_text(json.dumps({
        'starts': starts, 'speech_end': speech_end, 'audio_seconds': len(wav) / RATE,
        'voice': voice, 'speed': speed, 'words_without_time': missing, 'words': words}, indent=1, ensure_ascii=False))
    n_words = sum(1 for t in spoken)
    print(f'voice {voice} at {speed}: {len(wav) / RATE:.1f} s, {n_words} words timed, '
          f'{missing} pieces without a time, {len(shots)} shots')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
