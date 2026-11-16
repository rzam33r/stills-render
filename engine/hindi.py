"""What the voice is given for a Hindi film, so it says the words clearly.

Kokoro speaks Hindi from espeak-ng's sounds. The first real Hindi film
(bharat-mein-badhti-mehngai, 15 Nov 2026) showed five faults, all fixed here
for every film, never by editing one plan:

1. espeak writes ड़ and ढ़ as "r." -- a full stop inside the word -- so the
   voice stopped mid-word: बढ़ती came out as "bar... hati". The stop is
   replaced by Kokoro's own flap sound (fix_sounds).
2. The full stop "।" was dropped, so sentences ran into each other without a
   pause. It is read as "." (for_voice).
3. फ without a nukta is always "ph": फीस became "phees", रफ्तार
   "raphtaar". Words said with an f or z sound are respelled with the nukta
   from pronounce-hi.tsv (for_voice). The writers are told to use the nukta.
4. espeak adds a vowel to some words: पहले became "pahale", मतलब "matalab".
   pronounce-hi.tsv respells them with a halant so the vowel goes.
5. espeak doubles a consonant before य: क्यों became "kkyon". Removed
   (fix_sounds).

Kokoro also cuts any piece of more than 510 sounds, and only splits Hindi at
". ! ?", never at "।", so a long paragraph could lose its end without a
word of warning. sentences() hands the voice one sentence at a time.

Every respelling keeps one word as one word, so the film's timing is still
measured against the plan's own words.
"""
import pathlib
import re
import unicodedata

TABLE = pathlib.Path(__file__).resolve().parent / 'pronounce-hi.tsv'
ENDERS = '।॥.?!'
LONG = 220            # characters; a longer sentence is split at its commas


def load_table(path=TABLE):
    """{written word: spoken word} from pronounce-hi.tsv."""
    table = {}
    for line in pathlib.Path(path).read_text(encoding='utf-8').splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        written, spoken = (unicodedata.normalize('NFC', x.strip()) for x in line.split('\t'))
        table[written] = spoken
    return table


def _core(word):
    """The word without the punctuation around it: (before, core, after)."""
    m = re.match(r'^(\W*)(.*?)(\W*)$', word, re.S)
    before, core, after = m.groups()
    # Devanagari vowel signs and the nukta are "marks", which \W can eat at
    # the end; keep every mark inside the core.
    while after and unicodedata.category(after[0]).startswith('M'):
        core, after = core + after[0], after[1:]
    return before, core, after


def for_voice(text, table=None):
    """The text the voice reads: same words in the same order, respelled
    where pronounce-hi.tsv says, with "।" and "॥" read as a full stop."""
    table = load_table() if table is None else table
    out = []
    for word in unicodedata.normalize('NFC', text).split():
        before, core, after = _core(word)
        core = table.get(core, core)
        after = after.replace('॥', '.').replace('।', '.')
        out.append(before + core + after)
    return ' '.join(out)


def sentences(text, longest=LONG):
    """The text in pieces the voice can take whole: sentences, and a very
    long sentence split at its commas."""
    pieces, cur = [], ''
    for word in text.split():
        cur = f'{cur} {word}'.strip()
        if word[-1:] in ENDERS:
            pieces.append(cur)
            cur = ''
    if cur:
        pieces.append(cur)
    out = []
    for p in pieces:
        while len(p) > longest:
            cut = max(p.rfind(',', 0, longest), p.rfind('،', 0, longest))
            if cut <= 0:
                cut = p.rfind(' ', 0, longest)
            if cut <= 0:
                break
            out.append(p[:cut + 1].strip())
            p = p[cut + 1:].strip()
        if p:
            out.append(p)
    return out


CONSONANT = 'pbtdʈɖkɡcɟmnɳɲŋszʃʂfvʋlɭɾɽɦh'


def fix_sounds(ps, vocab):
    """Mend espeak's Hindi sounds before Kokoro speaks them."""
    flap = 'ɽ' if 'ɽ' in vocab else 'ɾ'
    breath = 'ʰ' if 'ʰ' in vocab else 'h'
    ps = re.sub(r'r\.([ˈˌ]?)h', lambda m: flap + m.group(1) + breath, ps)   # ढ़
    ps = re.sub(r'r\.', flap, ps)                                          # ड़
    ps = re.sub(rf'([{CONSONANT}]ʰ?)ː(?=[ˈˌ]?j)', r'\1', ps)              # क्यों
    return ps


NUKTA, CHANDRABINDU, ANUSVARA = '\u093c', '\u0901', '\u0902'


def norm(text):
    """Letters only, spelled the way a listener hears them: no nukta,
    chandrabindu as anusvara, no punctuation or spaces."""
    t = unicodedata.normalize('NFD', str(text)).replace(NUKTA, '').replace(CHANDRABINDU, ANUSVARA)
    t = unicodedata.normalize('NFC', t)
    return ''.join(c for c in t if unicodedata.category(c)[0] in 'LMN')


def cer(said, heard):
    """Share of the written letters a listener (or a recogniser) did not hear."""
    a, b = norm(said), norm(heard)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] / max(1, len(a))
