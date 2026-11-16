"""Speak the narration and record when each shot starts.

    python3 engine/voice.py plan.json OUT_DIR
    python3 engine/voice.py plan.json PARTS_DIR --part N --parts M   (Chatterbox)

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
  - Chatterbox Multilingual, Hindi edition (chatterbox-hi, the Hindi default
    since 16 Nov 2026): one sentence at a time, every word found in the
    recording by engine/align_hi.py, and a sentence the aligner cannot
    understand recorded again (engine/chatterbox_hi.py). A long film is
    recorded in parts at the same time (--part) and joined by
    engine/voice_parts.py.
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
from voices import DEFAULT_VOICE, chosen_voice, is_azure, is_chatterbox  # noqa: E402,F401
from voice_parts import (BREATH, COMMA_PAUSE, EDGE_AFTER, EDGE_BEFORE, LEAD, RATE,  # noqa: E402,F401
                         SENTENCE_PAUSE, join, spoken_text, trim_to_words, write_outputs)

FRAME = 600 / RATE   # one unit of Kokoro's sound lengths, in seconds
NOT_A_WORD = set(' ;:,.!?—…"()“”«»।॥-\'')


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


def hindi_words(graphemes, phonemes, pred_dur, vocab, written=None):
    """When each word of a Hindi chunk starts and ends, in seconds from the
    start of the chunk's sound: [(word, start, end)].

    Kokoro speaks the chunk's phonemes, one sound length (in units of 600
    samples) per phoneme it knows, between a start and an end marker. Words
    are separated by spaces in the phonemes, so adding up the lengths gives
    the moment each word's first sound begins. The phoneme words are then
    paired with the written words; when espeak split or joined a word and
    the counts differ, each written word takes the phoneme word at the same
    place in the line. `written` is the plan's own words when the voice read
    respelled ones (hindi.for_voice); the count is the same."""
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
    said = [w for w in graphemes.split() if any(c.isalnum() for c in w)]
    written = written if written is not None and len(written) == len(said) else said
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
    if code == 'h':
        return hindi_voice(pipe, shots, voice, speed)
    for p, group in enumerate(paragraphs(shots)):
        if p:
            audio.append(np.zeros(int(BREATH * RATE), dtype=np.float32))
            at += BREATH
        text = ' '.join(spoken_text(shots[i]['say']) for i in group)
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
    return np.concatenate(audio), tokens, missing


def hindi_voice(pipe, shots, voice, speed):
    """Kokoro's Hindi, made clear (engine/hindi.py): one sentence at a time,
    respelled where espeak gets a word wrong, its sounds mended, and a short
    pause after each sentence. Returns (samples, tokens, pieces without a
    time); the tokens carry the plan's own words."""
    from hindi import fix_sounds, for_voice, load_table, sentences

    table = load_table()
    vocab = pipe.model.vocab
    plain_g2p = pipe.g2p

    def g2p(text):
        ps, extra = plain_g2p(text)
        return fix_sounds(ps, vocab), extra
    pipe.g2p = g2p

    audio = [np.zeros(int(LEAD * RATE), dtype=np.float32)]
    at = LEAD
    tokens, missing = [], 0
    for p, group in enumerate(paragraphs(shots)):
        if p:
            audio.append(np.zeros(int(BREATH * RATE), dtype=np.float32))
            at += BREATH
        text = ' '.join(spoken_text(shots[i]['say']) for i in group)
        for piece in sentences(text):
            written = [w for w in piece.split() if any(c.isalnum() for c in w)]
            k = 0
            for r in pipe(for_voice(piece, table), voice=voice, speed=speed, split_pattern=None):
                if r.audio is None:
                    continue
                a = np.asarray(r.audio, dtype=np.float32)
                n = len([w for w in r.graphemes.split() if any(c.isalnum() for c in w)])
                timed = hindi_words(r.graphemes, r.phonemes, r.pred_dur.tolist(), vocab, written[k:k + n])
                k += n
                if not timed:
                    missing += n
                a, shift = trim_to_words(a, timed)
                for w, s, e in timed:
                    tokens.append((w, at + s - shift, at + e - shift, ' '))
                audio.append(a)
                at += len(a) / RATE
            pause = SENTENCE_PAUSE if piece[-1:] in '।॥.?!' else COMMA_PAUSE
            audio.append(np.zeros(int(pause * RATE), dtype=np.float32))
            at += pause
    return np.concatenate(audio), tokens, missing


def main(plan_path, out_dir, part=None, parts=1):
    plan = json.loads(pathlib.Path(plan_path).read_text(encoding='utf-8-sig'))
    voice = chosen_voice(plan)
    speed = float(plan.get('speed') or 1.0)
    if is_chatterbox(voice):
        from chatterbox_hi import speak_part
        if part is not None:
            speak_part(plan, part, parts, out_dir)
            return 0
        # The whole narration on this computer (samples and tests): one part.
        parts_dir = pathlib.Path(out_dir) / 'parts'
        speak_part(plan, 0, 1, parts_dir)
        join(plan, parts_dir, out_dir, voice)
        return 0
    wav, tokens, missing = (azure_voice if is_azure(voice) else kokoro_voice)(plan, voice, speed)
    write_outputs(plan, wav, tokens, missing, voice, speed, out_dir)
    return 0


if __name__ == '__main__':
    args = sys.argv[1:]
    part, parts = None, 1
    if '--part' in args:
        i = args.index('--part')
        part = int(args[i + 1])
        del args[i:i + 2]
    if '--parts' in args:
        i = args.index('--parts')
        parts = int(args[i + 1])
        del args[i:i + 2]
    if len(args) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(args[0], args[1], part, parts))
