"""Hindi narration is clear: the faults of the first real Hindi film stay fixed.

    python3 tests/test_hindi.py          (REQUIRE_ESPEAK=1 makes the espeak
                                          checks compulsory, as on GitHub)

- The voice gets the same words in the same order, one sentence at a time,
  never a piece Kokoro would cut (510 sounds), with "।" read as a stop.
- ड़/ढ़ never leave a full stop inside a word, and a consonant before य is
  not doubled.
- Kokoro's own half second of quiet at each end of a piece is cut away, so
  sentences are separated by the engine's pause, not 1.2 s of silence.
- With espeak (the same versions as locks/voice.txt): every line of
  engine/pronounce-hi.tsv changes how the word sounds, never reads a halant
  aloud, and gives f and z where it promises them; the whole script of
  bharat-mein-badhti-mehngai and the Hindi example come out without any of
  the five faults.
"""
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
from hindi import LONG, fix_sounds, for_voice, load_table, sentences  # noqa: E402
import numpy as np  # noqa: E402
from voice import EDGE_AFTER, EDGE_BEFORE, trim_to_words  # noqa: E402

bad = 0


def say(ok, msg):
    global bad
    bad += not ok
    print(('ok   ' if ok else 'FAIL ') + msg)


def words(t):
    return [w for w in t.split() if any(c.isalnum() for c in w)]


table = load_table()
plans = {p.name: json.loads(p.read_text(encoding='utf-8-sig')) for p in
         [ROOT / 'tests' / 'fixtures' / 'bharat-mein-badhti-mehngai-plan.json',
          ROOT / 'examples' / 'boond-hindi-short-plan.json']}

say(all(len(s.split()) == 1 and len(w.split()) == 1 for w, s in table.items()),
    f'every one of the {len(table)} respellings keeps one word as one word')
for name, plan in plans.items():
    text = ' '.join(s['say'].replace('*', '') for s in plan['shots'])
    pieces = sentences(text)
    say(words(' '.join(pieces)) == words(text), f'{name}: the sentences hold every word, in order')
    say(all(len(p) <= LONG for p in pieces), f'{name}: no piece is longer than {LONG} characters')
    spoken = [for_voice(p, table) for p in pieces]
    say(all(len(words(a)) == len(words(b)) for a, b in zip(pieces, spoken)), f'{name}: respelling keeps the word count')
    say(not any('।' in s for s in spoken), f'{name}: "।" is read as a full stop')

long = 'यह एक बहुत लंबा वाक्य है, ' * 20 + 'जो खत्म होता है।'
say(all(len(p) <= LONG for p in sentences(long)) and words(' '.join(sentences(long))) == words(long),
    'a very long sentence is split at its commas and keeps every word')

V = set('abdefhijklmnoprstuvwxzɽʰɾɟʈɖŋɡɪʊʌəɛɔː ˈˌ.,?!')
say(fix_sounds('bˈʌr.hətˌi', V) == 'bˈʌɽʰətˌi', 'ढ़ becomes one flap with breath, not "r." + h')
say(fix_sounds('bˈʌr.aː', V) == 'bˈʌɽaː', 'ड़ becomes one flap, not "r."')
say(fix_sounds('bʌr.aː', set('abr')) == 'bʌɾaː', 'without ɽ in the voice, a plain flap is used')
say(fix_sounds('kːjˈõ pːjˈaːz', V) == 'kjˈõ pjˈaːz', 'क्यों and प्याज़ lose the doubled consonant')
say(fix_sounds('bˈʌcːõ', V) == 'bˈʌcːõ', 'a real double consonant (बच्चों) is kept')

a = np.ones(24000 * 3, dtype=np.float32)
cut, shift = trim_to_words(a, [('x', 0.5, 1.0), ('y', 1.1, 2.0)])
say(abs(shift - (0.5 - EDGE_BEFORE)) < 1e-6 and abs(len(cut) / 24000 - (2.0 + EDGE_AFTER - shift)) < 1e-3,
    f'a piece is cut to its words: {shift:.2f} s off the start, {len(cut) / 24000:.2f} s kept of 3')
same, none = trim_to_words(a, [])
say(none == 0.0 and len(same) == len(a), 'a piece with no timed words is left whole')

try:
    import espeakng_loader
    from phonemizer.backend.espeak.wrapper import EspeakWrapper
    EspeakWrapper.set_library(espeakng_loader.get_library_path())
    EspeakWrapper.set_data_path(espeakng_loader.get_data_path())
    from phonemizer.backend import EspeakBackend
except ImportError:
    EspeakBackend = None
if EspeakBackend is None:
    say(os.environ.get('REQUIRE_ESPEAK') != '1', 'espeak checks skipped (phonemizer-fork and espeakng-loader not installed)')
else:
    plain = EspeakBackend('hi', preserve_punctuation=False, with_stress=False)
    # As misaki.espeak.EspeakG2P calls it for Kokoro.
    kokoro = EspeakBackend('hi', preserve_punctuation=True, with_stress=True, tie='^', language_switch='remove-flags')
    P = lambda w: plain.phonemize([w], strip=True)[0]
    same = [w for w, s in table.items() if P(w) == P(s)]
    say(not same, 'every respelling changes how the word sounds' + (f': not {same}' if same else ''))
    aloud = [w for w, s in table.items() if 'həl' in P(s) and 'həl' not in P(w)]
    say(not aloud, 'no respelling makes espeak read a halant aloud' + (f': {aloud}' if aloud else ''))
    f_lost = [w for w, s in table.items() if ('फ़' in s and 'f' not in P(s)) or ('ज़' in s and 'z' not in P(s))]
    say(not f_lost, 'every फ़ / ज़ respelling gives f / z' + (f': not {f_lost}' if f_lost else ''))
    vocab = set(''.join(table) + 'ɽʰ') | set('abcdefghijklmnopqrstuvwxyzɾɟʈɖŋɡɪʊʌəɛɔːɐɑɒæβçðɣɦɨɭɯɱɲɳɸʂʃʋʒʔθχ ˈˌ.,?!—…̃')
    for name, plan in plans.items():
        text = ' '.join(s['say'].replace('*', '') for s in plan['shots'])
        out = ' '.join(fix_sounds(kokoro.phonemize([for_voice(p, table)], strip=True)[0].replace('^', ''), vocab)
                       for p in sentences(text))
        dots = [w for w in out.split() if '.' in w.rstrip('.?!,')]
        say(not dots, f'{name}: no full stop inside a word' + (f': {dots}' if dots else ''))
        dbl = re.findall(r'\Sː[ˈˌ]?j', out)
        say(not any(c[0] not in 'aeiouɛɔəʌɪʊ' for c in dbl), f'{name}: no doubled consonant before y')
        say(out.count('.') + out.count('?') >= text.count('।'), f'{name}: every "।" became a stop the voice hears')
    bharat = ' '.join(s['say'] for s in plans['bharat-mein-badhti-mehngai-plan.json']['shots'])
    heard = {w: P(for_voice(w, table)) for w in ('फीस', 'रफ्तार', 'सिर्फ', 'पहले', 'मतलब', 'पहुँचते')}
    say('f' in heard['फीस'] and 'f' in heard['रफ्तार'] and 'f' in heard['सिर्फ'], f'फीस, रफ्तार, सिर्फ are said with f: {heard["फीस"]}, {heard["रफ्तार"]}, {heard["सिर्फ"]}')
    say('hl' in heard['पहले'] and 'tl' in heard['मतलब'] and 'ct' in heard['पहुँचते'],
        f'पहले, मतलब, पहुँचते lose the added vowel: {heard["पहले"]}, {heard["मतलब"]}, {heard["पहुँचते"]}')

print('\nall good' if not bad else f'\n{bad} failed')
sys.exit(1 if bad else 0)
