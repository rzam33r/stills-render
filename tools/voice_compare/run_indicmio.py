"""Indic-Mio (SPRINGLab/Indic-Mio, Apache-2.0) with MioCodec (MIT).

    python run_indicmio.py PLAN OUT_DIR REFERENCE.wav

The language model writes content tokens; the codec gives them a voice from
REFERENCE.wav, so every sentence has the same voice.
"""
import sys

import torch
from miocodec import MioCodecModel, load_audio
from transformers import AutoModelForCausalLM, AutoTokenizer

from common import Timer, join, plan_sentences, save

plan, out, ref = sys.argv[1:4]
torch.set_num_threads(4)
OFFSET, VOCAB = 151669, 12800
tok = AutoTokenizer.from_pretrained('SPRINGLab/Indic-Mio', trust_remote_code=True)
lm = AutoModelForCausalLM.from_pretrained('SPRINGLab/Indic-Mio', torch_dtype=torch.float32).eval()
codec = MioCodecModel.from_pretrained('Aratako/MioCodec-25Hz-24kHz').eval()
rate = codec.config.sample_rate
ref_wave = load_audio(ref, sample_rate=rate).reshape(-1)[: rate * 12]   # 12 s of the reference voice
voice = codec.encode(ref_wave).global_embedding
lines = plan_sentences(plan)
with Timer() as t:
    pieces = []
    for line in lines:
        torch.manual_seed(7)
        prompt = tok.apply_chat_template([{'role': 'user', 'content': line}], tokenize=False, add_generation_prompt=True)
        ids = tok(prompt, return_tensors='pt')
        with torch.no_grad():
            gen = lm.generate(**ids, max_new_tokens=600, do_sample=True, temperature=0.9, top_p=0.9)
        codes = [x - OFFSET for x in gen[0][ids['input_ids'].shape[1]:].tolist() if OFFSET <= x < OFFSET + VOCAB]
        if not codes:
            print('no speech for:', line)
            continue
        with torch.no_grad():
            wav = codec.decode(content_token_indices=torch.tensor(codes, dtype=torch.long), global_embedding=voice)
        pieces.append(wav.squeeze().float().cpu().numpy())
save(out, 'indic-mio-omega', join(pieces, rate), rate, t.seconds,
     {'model': 'SPRINGLab/Indic-Mio + Aratako/MioCodec-25Hz-24kHz', 'licence': 'Apache-2.0 (codec MIT)', 'voice': 'Kokoro hm_omega as reference'})
