"""Where each word starts in recorded Hindi speech, and what was heard.

Chatterbox does not say when it speaks each word, and the film's pictures
change on words. So every recorded sentence is lined up against its own
words (CTC forced alignment, torchaudio) by Vakyansh's Hindi wav2vec2 model
(MIT, trained on 4,200 hours of Hindi; skylord's XLSR Hindi model, Apache-2.0,
is the backup). AI4Bharat's IndicWav2Vec was the first choice but needs a
Hugging Face account to download, which unattended films cannot have. The
same model also says what it heard, so a sentence that comes out garbled can
be recorded again (engine/chatterbox_hi.py).
"""
import re
import sys
import unicodedata
import pathlib

import numpy as np
import torch
import torchaudio
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

MODELS = ('Harveenchadha/vakyansh-wav2vec2-hindi-him-4200', 'skylord/wav2vec2-large-xlsr-hindi')
from hindi import ANUSVARA, CHANDRABINDU, cer, norm  # noqa: E402,F401


class Aligner:
    def __init__(self, revisions=None):
        revisions = revisions or {}
        problems = []
        for repo in MODELS:
            try:
                # Wav2Vec2Processor, not AutoProcessor: Vakyansh also ships a
                # language model add-on that needs another library.
                self.proc = Wav2Vec2Processor.from_pretrained(repo, revision=revisions.get(repo))
                self.model = Wav2Vec2ForCTC.from_pretrained(repo, revision=revisions.get(repo)).eval()
                self.name = repo
                break
            except Exception as e:  # noqa: BLE001
                problems.append(f'{repo}: {e}')
        else:
            raise SystemExit('ERROR no Hindi word-timing model could be loaded: ' + ' | '.join(problems))
        if problems:
            print('word timing uses the backup model:', ' | '.join(problems), flush=True)
        print(f'word timing: {self.name}', flush=True)
        tok = self.proc.tokenizer
        self.vocab = tok.get_vocab()
        self.blank = tok.pad_token_id if tok.pad_token_id is not None else 0
        self.delim = self.vocab.get(getattr(tok, 'word_delimiter_token', None) or '|')
        self.id_to_char = {i: c for c, i in self.vocab.items()}

    def letters(self, word):
        """The recogniser's ids for a word's letters; letters it does not
        know (a nukta, punctuation) are left out."""
        t = unicodedata.normalize('NFD', word)
        ids = []
        for c in t:
            if c in self.vocab:
                ids.append(self.vocab[c])
            elif c == CHANDRABINDU and ANUSVARA in self.vocab:
                ids.append(self.vocab[ANUSVARA])
        if not ids:
            # Some vocabularies hold composed letters; try the word as written.
            ids = [self.vocab[c] for c in unicodedata.normalize('NFC', word) if c in self.vocab]
        return ids

    def emissions(self, a, rate):
        x = torch.from_numpy(np.asarray(a, dtype=np.float32))
        if rate != 16000:
            x = torchaudio.functional.resample(x, rate, 16000)
        inputs = self.proc(x.numpy(), sampling_rate=16000, return_tensors='pt')
        with torch.no_grad():
            logits = self.model(inputs.input_values).logits
        lp = torch.log_softmax(logits, dim=-1)[0]
        return lp, (len(x) / 16000) / max(1, lp.shape[0])

    def heard(self, lp):
        ids = lp.argmax(dim=-1).tolist()
        out, last = [], None
        for i in ids:
            if i != last and i != self.blank:
                out.append(' ' if i == self.delim else self.id_to_char.get(i, ''))
            last = i
        return re.sub(r'\s+', ' ', ''.join(out)).strip()

    def align(self, a, words, rate=24000):
        """[(word, start, end)] in seconds into `a`, and what was heard.
        A word the recogniser has no letters for takes the gap between its
        neighbours."""
        lp, step = self.emissions(a, rate)
        heard = self.heard(lp)
        targets, owner = [], []
        for wi, w in enumerate(words):
            ids = self.letters(w)
            if not ids:
                continue
            if targets and self.delim is not None:
                targets.append(self.delim)
                owner.append(None)
            targets += ids
            owner += [wi] * len(ids)
        spans = {}
        if targets and len(targets) <= lp.shape[0]:
            ali, scores = torchaudio.functional.forced_align(
                lp.unsqueeze(0).float(), torch.tensor([targets], dtype=torch.int32), blank=self.blank)
            merged = torchaudio.functional.merge_tokens(ali[0], scores[0].exp(), blank=self.blank)
            if len(merged) == len(targets):
                for k, span in enumerate(merged):
                    wi = owner[k]
                    if wi is None:
                        continue
                    s, e = span.start * step, span.end * step
                    if wi in spans:
                        spans[wi] = (min(spans[wi][0], s), max(spans[wi][1], e))
                    else:
                        spans[wi] = (s, e)
        if not spans:
            # Nothing lined up: spread the words over the speech by length.
            total = sum(max(1, len(norm(w))) for w in words) or 1
            dur, at = len(a) / rate, 0.0
            for wi, w in enumerate(words):
                d = dur * max(1, len(norm(w))) / total
                spans[wi] = (at, at + d)
                at += d
        out = []
        for wi, w in enumerate(words):
            if wi in spans:
                out.append((w, round(spans[wi][0], 3), round(spans[wi][1], 3)))
                continue
            before = max((spans[j][1] for j in spans if j < wi), default=0.0)
            after = min((spans[j][0] for j in spans if j > wi), default=len(a) / rate)
            out.append((w, round(before, 3), round(max(before, after), 3)))
        return out, heard
