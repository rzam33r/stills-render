"""Chatterbox Multilingual, Hindi edition (ResembleAI/Chatterbox-Multilingual-hi, MIT).

    python run_chatterbox.py PLAN OUT_DIR REFERENCE.wav

Two takes: the model's own stock voice, and the voice of REFERENCE.wav
(the engine's Kokoro hm_omega narration, so the brand voice could stay).
"""
import pathlib
import shutil
import sys

import torch
from huggingface_hub import hf_hub_download, list_repo_files

from common import Timer, join, plan_sentences, save

plan, out, ref = sys.argv[1:4]
torch.set_num_threads(4)
ck = pathlib.Path('/tmp/chatterbox-hi')
ck.mkdir(exist_ok=True)


def put(src, name):
    """Copy a downloaded file in; Hugging Face's cache files are read-only."""
    dst = ck / name
    if dst.exists():
        dst.chmod(0o644)
        dst.unlink()
    shutil.copyfile(src, dst)


hi_files = list_repo_files('ResembleAI/Chatterbox-Multilingual-hi')
print('Hindi pack files:', hi_files)
for f in ('ve.pt', 'conds.pt', 's3gen.pt', 'grapheme_mtl_merged_expanded_v1.json', 'Cangjie5_TC.json'):
    put(hf_hub_download('ResembleAI/chatterbox', f), f)
t3 = next(f for f in hi_files if f.startswith('t3') and f.endswith('.safetensors'))
put(hf_hub_download('ResembleAI/Chatterbox-Multilingual-hi', t3), t3)
for f in ('grapheme_mtl_merged_expanded_v1.json',):
    if f in hi_files:
        put(hf_hub_download('ResembleAI/Chatterbox-Multilingual-hi', f), f)
s3 = [f for f in hi_files if f.startswith('s3gen') and f.endswith('.pt')]
if s3:
    put(hf_hub_download('ResembleAI/Chatterbox-Multilingual-hi', s3[0]), 's3gen.pt')
print('using', t3, 'and', s3[0] if s3 else 's3gen.pt from the main repo')

from chatterbox.mtl_tts import ChatterboxMultilingualTTS  # noqa: E402
model = ChatterboxMultilingualTTS.from_local(ck, 'cpu', t3_model=t3)
lines = plan_sentences(plan)
for take, prompt in (('chatterbox-hi-stock', None), ('chatterbox-hi-omega', ref)):
    if prompt:
        model.prepare_conditionals(prompt)
    with Timer() as t:
        pieces = []
        for line in lines:
            torch.manual_seed(7)
            wav = model.generate(line, language_id='hi')
            pieces.append(wav.squeeze(0).cpu().numpy())
    save(out, take, join(pieces, model.sr), model.sr, t.seconds,
         {'model': f'ResembleAI/Chatterbox-Multilingual-hi ({t3})', 'licence': 'MIT', 'voice': 'stock' if not prompt else 'Kokoro hm_omega as reference'})
