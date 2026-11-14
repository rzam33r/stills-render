"""Each shot starts when its first word is spoken.

    python3 tests/test_timing.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'engine'))
from timing import paragraphs, shot_starts  # noqa: E402

bad = 0


def say(ok, msg):
    global bad
    bad += not ok
    print(('ok   ' if ok else 'FAIL ') + msg)


def toks(spec):
    """'word@start word@start' -> tokens, each lasting until the next."""
    out = []
    parts = spec.split()
    for k, p in enumerate(parts):
        text, _, t = p.partition('@')
        start = None if t in ('', '?') else float(t)
        out.append((text, start, None))
    return out


# Plain: the voice says exactly the shots' words.
says = ['It is midnight on the sea,', 'and the coast is gone.', 'No map.']
t = toks('It@0.2 is@0.4 midnight@0.6 on@1.0 the@1.1 sea@1.3 ,@1.6 and@1.8 the@2.0 coast@2.1 is@2.5 gone@2.7 .@3.0 No@3.4 map@3.6 .@3.9')
say(shot_starts(says, t) == [0.0, 1.8, 3.4], 'each shot starts on its first word')

# The voice splits words differently: punctuation, "didn't" in two, a number.
says = ["They didn't know.", "Twenty thousand years ago,", "20,000 people lived here."]
t = toks("They@0.1 did@0.3 n't@0.5 know@0.6 .@0.9 Twenty@1.2 thousand@1.5 years@1.9 ago@2.2 ,@2.5 20,000@2.8 people@3.6 lived@3.9 here@4.1")
say(shot_starts(says, t) == [0.0, 1.2, 2.8], 'contractions, punctuation and numbers line up')

# A word without a time takes the end of the word before it.
says = ['One two.', 'Three four.']
t = [('One', 0.1, 0.3), ('two', 0.3, 0.6), ('.', None, None), ('Three', None, None), ('four', 1.4, 1.7)]
say(shot_starts(says, t) == [0.0, 0.6], 'a word with no time uses the end of the one before')

# The voice changed a word ("its" for "it's"): the alignment does not drift.
says = ["It's late.", 'The tide turns.', 'Boats wait.']
t = toks('Its@0.1 late@0.4 .@0.7 The@1.0 tide@1.2 turns@1.5 .@1.9 Boats@2.3 wait@2.6')
say(shot_starts(says, t) == [0.0, 1.0, 2.3], 'a changed word does not shift later shots')

# The voice skipped a whole shot: it starts between its neighbours.
says = ['Alpha beta.', 'Gamma.', 'Delta epsilon.']
t = toks('Alpha@0.0 beta@0.4 Delta@2.0 epsilon@2.4')
s = shot_starts(says, t)
say(s[0] == 0 and 0.4 < s[1] < 2.0 and s[2] == 2.0, 'a skipped shot sits between its neighbours')

# Two shots can never start on the same frame.
says = ['A b.', 'C.', 'D e.']
t = toks('A@0 b@0.1 C@0.5 D@0.5 e@0.7')
s = shot_starts(says, t)
say(all(b - a >= 1 / 30 - 1e-9 for a, b in zip(s, s[1:])), 'shot starts are at least one frame apart')

say(paragraphs([{}, {}, {'paragraph': True}, {}]) == [[0, 1], [2, 3]], 'paragraph marks split the narration')

print('\nall good' if not bad else f'\n{bad} failing')
sys.exit(1 if bad else 0)
