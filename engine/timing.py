"""When each shot's first word is spoken.

The voice is made from the whole narration at once (so it flows like one
speaker, not a string of separate clips), and Kokoro reports when it says
each piece of text. This file lines those pieces up with the shots: shot N
starts at the moment the voice begins shot N's first word.

Both sides are compared as words, a word being what sits between spaces,
reduced to its letters and digits in lower case. So "didn't", which the
voice says in two pieces, "20,000", "hunter-gatherer" and any punctuation
compare equal. Where the voice changes or skips a word, the alignment steps
over the difference instead of drifting.
"""
import difflib
import re

ALNUM = re.compile(r'[a-z0-9]+')


def norm(text):
    return ''.join(ALNUM.findall((text or '').lower()))


def paragraphs(shots):
    """The narration as paragraphs: [[shot index, ...], ...]."""
    out = []
    for i, s in enumerate(shots):
        if not out or s.get('paragraph'):
            out.append([])
        out[-1].append(i)
    return out


def spoken_words(tokens):
    """Group the voice's pieces into words: [(word, start, end), ...].

    tokens: [(text, start, end[, whitespace])]. A piece followed by no
    whitespace joins the next one ("did" + "n't"). Without whitespace
    information, a piece with no letters or one starting with an apostrophe
    joins the word before it.
    """
    words = []
    glue = False
    for tok in tokens:
        text, start, end = tok[0], tok[1], tok[2]
        ws = tok[3] if len(tok) > 3 else None
        joins_back = ws is None and words and (not norm(text) or text[:1] in "'’")
        if words and (glue or joins_back):
            w, s, e = words[-1]
            words[-1] = (w + text, s if s is not None else start, end if end is not None else e)
        else:
            words.append((text, start, end))
        glue = ws is not None and ws == ''
    return [(norm(w), s, e) for w, s, e in words if norm(w)]


def shot_starts(says, tokens, gap=1 / 30):
    """Start time of each shot.

    says   -- the words of each shot, in order
    tokens -- what the voice said: [(text, start, end[, whitespace]), ...] in
              seconds from the start of the voice, in order; times may be None
    gap    -- the least time between two shot starts (one frame)

    Returns a list of seconds, one per shot; the first is always 0.
    """
    nar, first = [], []
    for say in says:
        first.append(len(nar))
        nar.extend(n for n in (norm(w) for w in (say or '').split()) if n)
    spoken = spoken_words(tokens)
    heard = [w for w, _, _ in spoken]

    where = [None] * len(nar)
    sm = difflib.SequenceMatcher(None, nar, heard, autojunk=False)
    for a, b, size in sm.get_matching_blocks():
        for d in range(size):
            where[a + d] = b + d

    def time_of(k):
        """When spoken word k starts; if unknown, when the word before ended,
        else when the next timed word starts."""
        if spoken[k][1] is not None:
            return spoken[k][1]
        for j in range(k - 1, -1, -1):
            if spoken[j][2] is not None:
                return spoken[j][2]
            if spoken[j][1] is not None:
                return spoken[j][1]
        for j in range(k + 1, len(spoken)):
            if spoken[j][1] is not None:
                return spoken[j][1]
        return None

    starts = []
    for i, f in enumerate(first):
        if i == 0:
            starts.append(0.0)
            continue
        end = first[i + 1] if i + 1 < len(first) else len(nar)
        # The shot's first word, or failing that its first word the voice said.
        hit = next(((c, where[c]) for c in range(f, end) if where[c] is not None), None)
        if hit is None:
            starts.append(None)
            continue
        c, k = hit
        t = time_of(k)
        if c > f and t is not None and k > 0 and spoken[k - 1][2] is not None:
            # The first word(s) were changed by the voice: start where the
            # previous matched word ended, which is where the shot's words begin.
            t = spoken[k - 1][2]
        starts.append(t)

    # A shot whose words the voice skipped entirely starts halfway between
    # its neighbours; every start is at least one frame after the last.
    for i in range(1, len(starts)):
        if starts[i] is None:
            nxt = next((starts[k] for k in range(i + 1, len(starts)) if starts[k] is not None), None)
            starts[i] = (starts[i - 1] + nxt) / 2 if nxt is not None else starts[i - 1] + 1.0
        if starts[i] < starts[i - 1] + gap:
            starts[i] = starts[i - 1] + gap
    return starts
