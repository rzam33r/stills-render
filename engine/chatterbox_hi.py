"""Hindi narration by Chatterbox Multilingual's Hindi edition (MIT).

Chosen on 16 Nov 2026 after a test on a real script (tools/voice_compare):
understood far better than Kokoro's Hindi, with the cleanest licence for a
paid channel. It is slow on GitHub's computers (about 11 s of work per
second of speech), so a long film is recorded in parts at the same time;
each part records its run of sentences (engine/voice_parts.py).

Every sentence is:
  1. spoken by Chatterbox with a fixed seed, so a film can be made again
     and sound the same;
  2. lined up against its own words by engine/align_hi.py, which also says
     what it heard;
  3. recorded again with another seed (up to TRIES times) when too little
     of it was understood, keeping the clearest take;
  4. trimmed to its words, and saved with each word's start and end.
"""
import json
import pathlib
import shutil

import numpy as np
import soundfile as sf
import torch
import align_hi
import hf
from voice_parts import RATE, pieces, split, trim_to_words

MAIN = 'ResembleAI/chatterbox'
HINDI = 'ResembleAI/Chatterbox-Multilingual-hi'
SEED = 7                 # the seed of the takes Roshan chose on 16 Nov 2026
TRIES = 3
GOOD_ENOUGH = 0.35       # letters not understood; a clearer take is kept above this
MODELS = pathlib.Path(__file__).resolve().parents[1] / 'locks' / 'models.txt'


def load_revisions():
    """{repo: revision} from locks/models.txt, so an update on Hugging Face
    cannot change a film's voice without anyone choosing it."""
    revs = {}
    if MODELS.exists():
        for line in MODELS.read_text().splitlines():
            parts = line.split('#', 1)[0].split()
            if len(parts) >= 2:
                revs[parts[0]] = parts[1]
    return revs


def load_model(revs):
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    ck = pathlib.Path('/tmp/chatterbox-hi')
    ck.mkdir(parents=True, exist_ok=True)

    def put(repo, name, as_name=None):
        src = hf.download(repo, name, revs.get(repo))
        dst = ck / (as_name or name)
        if dst.exists():
            dst.chmod(0o644)
            dst.unlink()
        shutil.copyfile(src, dst)

    for f in ('ve.pt', 'conds.pt', 's3gen.pt', 'grapheme_mtl_merged_expanded_v1.json', 'Cangjie5_TC.json'):
        put(MAIN, f)
    # From the cache when the model is there: asking Hugging Face for the
    # list on every part of every film got GitHub turned away (hf.py).
    files = hf.repo_files(HINDI, revs.get(HINDI), lambda f: f.startswith('t3') and f.endswith('.safetensors'))
    t3 = next(f for f in files if f.startswith('t3') and f.endswith('.safetensors'))
    put(HINDI, t3)
    if 'grapheme_mtl_merged_expanded_v1.json' in files:
        put(HINDI, 'grapheme_mtl_merged_expanded_v1.json')
    model = ChatterboxMultilingualTTS.from_local(ck, 'cpu', t3_model=t3)
    s3 = [f for f in files if f.startswith('s3gen') and f.endswith('.pt')]
    if s3:
        # The Hindi edition's decoder lacks two buffers the code computes
        # itself (the tokenizer's mel filters and window).
        state = torch.load(hf.download(HINDI, s3[0], revs.get(HINDI)), map_location='cpu', weights_only=True)
        res = model.s3gen.load_state_dict(state, strict=False)
        print(f'Chatterbox Hindi: {t3} with {s3[0]} (computed, not loaded: {res.missing_keys})', flush=True)
    return model


def speak_part(plan, part, parts, out_dir):
    items = pieces(plan)
    lo, hi = split(items, parts)[part]
    out = pathlib.Path(out_dir) / f'part-{part}'
    out.mkdir(parents=True, exist_ok=True)
    report = []
    if lo < hi:
        torch.set_num_threads(max(1, torch.get_num_threads()))
        revs = load_revisions()
        model = load_model(revs)
        aligner = align_hi.Aligner(revs)
        sr = getattr(model, 'sr', RATE)
        for x in items[lo:hi]:
            words = [w for w in x['text'].split() if any(c.isalnum() for c in w)]
            best = None
            for t in range(TRIES):
                torch.manual_seed(SEED + 1000 * t)
                with torch.no_grad():
                    wav = model.generate(x['text'], language_id='hi')
                a = wav.squeeze().float().cpu().numpy()
                if sr != RATE:
                    import torchaudio
                    a = torchaudio.functional.resample(torch.from_numpy(a), sr, RATE).numpy()
                timed, heard = aligner.align(a, words, RATE)
                err = align_hi.cer(x['text'], heard)
                if best is None or err < best[0]:
                    best = (err, a, timed, heard, t + 1)
                if err <= GOOD_ENOUGH:
                    break
            err, a, timed, heard, tries = best
            a, shift = trim_to_words(a, timed, RATE)
            name = f'piece-{x["i"]:04d}.wav'
            sf.write(out / name, a.astype(np.float32), RATE)
            report.append({'i': x['i'], 'file': name, 'cer': round(err, 3), 'tries': tries, 'heard': heard,
                           'words': [{'word': w, 'start': round(max(0.0, s - shift), 3), 'end': round(max(0.0, e - shift), 3)}
                                     for w, s, e in timed]})
            print(f'piece {x["i"] + 1}/{len(items)}: take {tries}, {err:.0%} not understood: {x["text"]}', flush=True)
    (out / 'part.json').write_text(json.dumps({'part': part, 'parts': parts, 'pieces': report},
                                              ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'part {part + 1} of {parts}: {len(report)} pieces', flush=True)
