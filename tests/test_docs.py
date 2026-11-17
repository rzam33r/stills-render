"""The ChatGPT instructions agree with the engine.

    python3 tests/test_docs.py

- The example in 4_PLAN_FORMAT.md is the example plan, and it passes the plan
  check with no warning but the length note.
- Every key the format table names is one the plan check knows.
- PROJECT_INSTRUCTIONS.md fits ChatGPT's 8,000-character limit.
- Every picture prompt in the example ends with the style block and every
  prompt showing the lead uses the character description word for word.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs' / 'chatgpt'
sys.path.insert(0, str(ROOT / 'engine'))
from check_plan import KEYS, TOP, check  # noqa: E402

bad = 0


def say(ok, msg):
    global bad
    bad += not ok
    print(('ok   ' if ok else 'FAIL ') + msg)


fmt = (DOCS / '4_PLAN_FORMAT.md').read_text()
m = re.search(r'```json\n(.*?)\n```', fmt, re.S)
doc_plan = json.loads(m.group(1))
ex = json.loads((ROOT / 'examples' / 'north-star-plan.json').read_text())
say(doc_plan == ex, '4_PLAN_FORMAT.md shows the example plan exactly')
errors, warnings = check(ex)
say(not errors and len(warnings) == 1, 'the example passes the plan check cleanly' + ('' if not errors else f': {errors}'))
named = set(re.findall(r'^\| `([a-z_]+)` \|', fmt, re.M))
say(named <= KEYS | TOP, 'every key in the format table is known to the plan check' + f' (unknown: {sorted(named - KEYS - TOP)})' * bool(named - KEYS - TOP))
shorts = (DOCS / '5_SHORTS.md').read_text()
blocks = [json.loads(b) for b in re.findall(r'```json\n(.*?)\n```', shorts, re.S)]
want = [json.loads((ROOT / 'examples' / n).read_text()) for n in ('rain-short-plan.json', 'boond-hindi-short-plan.json')]
say(blocks == want, '5_SHORTS.md shows the English and Hindi short examples exactly')
for b in want:
    e, w = check(b)
    say(not e and len(w) == 1, f'the {b["language"]} short example passes the plan check cleanly' + ('' if not e else f': {e}'))
n = len((DOCS / 'PROJECT_INSTRUCTIONS.md').read_text(encoding='utf-8'))
say(n < 8000, f'PROJECT_INSTRUCTIONS.md is {n} characters, under 8,000')
prompts = [s['prompt'] for s in ex['shots'] if 'prompt' in s]
say(all(p.endswith(ex['style']) for p in prompts), 'every picture prompt ends with the style block')
say(all(ex['character'] in p for p in prompts), 'every picture prompt describes the lead the same way')
# The Antigravity project agrees with the guide and the engine.
import shutil, subprocess, tempfile  # noqa: E401,E402
AG = ROOT / 'docs' / 'antigravity' / 'studio'
rule = (AG / '.agent' / 'rules' / 'studio.md').read_text()
flows = {f.stem: f.read_text() for f in (AG / '.agent' / 'workflows').glob('*.md')}
say(rule.startswith('---\ntrigger: always_on\n---'), 'the studio rule is always on')
say(set(flows) == {'new-film', 'make-pictures', 'upload-film', 'fix-plan', 'check-studio'}
    and all(t.startswith('---\ndescription: ') for t in flows.values()), 'the five workflows exist, each with a description')
called = {c for t in flows.values() for c in re.findall(r'(?<![\w/])/([a-z]+(?:-[a-z]+)+)\b', t)}
say(called <= set(flows), f'every /workflow a workflow calls exists: {sorted(called)}')
texts = [rule] + list(flows.values()) + [(DOCS / 'PROJECT_INSTRUCTIONS.md').read_text()]
named = {n for t in texts for n in re.findall(r'\b([1-7]_[A-Z_]+\.md)', t)}
say(named and all((DOCS / n).exists() for n in named), f'every guide file named exists ({len(named)} named)')
say(all((DOCS / f'{n}').exists() for n in ('6_LONG_FILMS.md', '7_HINDI_VOICE.md')), 'the long-film and Hindi guide files exist')
# Quoted words in the workflows are plan keys, plan values, or answers
# Roshan types ("ready"); only the keys must be ones the engine knows.
ANSWERS = {'ready', 'yes', 'no', 'story'}
# Flow Connector's flow_generate options, named in /make-pictures; not plan keys.
FLOW_OPTIONS = {'mode', 'prompt', 'aspect_ratio', 'character_refs', 'image_model', 'outputs', 'folder'}
keys = {k for t in flows.values() for k in re.findall(r'"([a-z_]+)"', t)} - {'say', 'short', 'wide'} - ANSWERS - (FLOW_OPTIONS - {'prompt'})
say(keys <= KEYS | TOP | {'say'}, f'the workflows use only plan keys the engine knows: {sorted(keys)}')
say('`bharat-mein-badhti-mehngai`' in rule and 'at most 30 characters' in rule, 'the story name follows the upload page\'s rule')
url = 'https://picture-plan-film-forge.lovable.app/stills'
say(url in rule and url in flows['upload-film'], 'the rule and /upload-film name the same upload page')
say('plan.json' in flows['upload-film'] and 'Never type' in flows['upload-film'], '/upload-film zips the plan and never types a password')
say('ONE Google Flow project' in rule and 'no other' in flows['make-pictures'], 'pictures are made in the film\'s own Flow project only')
# Bittu & Riya: the cast's rule book, its characters, and the plan check agree.
import json  # noqa: E402
from check_plan import CASTS, check as check_plan  # noqa: E402
CAST = AG / 'cast' / 'bittu-riya'
cast_md = (CAST / 'CAST.md').read_text()
people = {json.loads((CAST / f).read_text())['name'] for f in ('bittu.json', 'riya.json')}
say(CASTS == {'Bittu & Riya': ('Bittu', 'Riya')} and people == {'Bittu', 'Riya'}
    and '**`Bittu & Riya`**' in cast_md, 'the cast, its Flow project and its character files agree')
keep = re.findall(r'- (?:Bittu|Riya): `([^`]+)`', cast_md)
example = cast_md.split('Example')[1].replace('\n> ', ' ')
say(len(keep) == 2 and all(k in example for k in keep), 'the cast example carries both keep-lines word for word')
everything = [rule, cast_md] + list(flows.values()) + [(DOCS / n).read_text() for n in ('3_FLOW_PROMPTS.md', '4_PLAN_FORMAT.md')]
say(sum(t.count('Bitto') for t in everything) == 1 and 'never "Bitto"' in cast_md, 'his name is Bittu everywhere (Bitto only in "never Bitto")')
mp = flows['make-pictures']
say('"character_refs"' in mp and 'Never make a picture of Bittu or Riya' in mp
    and 'first 2 pictures' in mp and 'Never create the project' in mp,
    '/make-pictures casts Bittu and Riya as Flow characters, stops after 2 pictures the first time, never creates the cast project')
say('Never use your own browser for Flow' in mp and 'Use your own browser for Google Flow' in rule
    and 'width × height' in mp and all(f'"{o}"' in mp for o in ('aspect_ratio', 'image_model', 'folder', 'outputs')),
    'pictures are made with Flow Connector only, never Antigravity\'s browser, and checked for name and shape')
say('Never change models in the middle of a film' in mp and '"nano-banana-pro"' in mp,
    'every picture of a film uses the same image model')
say('`Bittu & Riya`' in rule and 'Never create the `Bittu & Riya` project' in rule, 'the rule keeps Bittu & Riya films in their own Flow project')
cast_plan = {'title': 'T', 'layout': 'short', 'style': 's', 'cast': 'Bittu & Riya', 'shots': [
    {'say': 'one two three', 'picture': '001', 'prompt': 'Riya laughs as Bittu trips', 'who': ['Riya', 'Bittu']}]}
say(not check_plan(cast_plan)[0], 'a good Bittu & Riya plan passes the plan check')
for what, shot in (('a misspelt name', {'who': ['Bitto', 'Riya']}), ('a name left out of "who"', {'who': ['Riya']}),
                   ('"who" on a card', {'picture': None})):
    bad_plan = json.loads(json.dumps(cast_plan))
    s = bad_plan['shots'][0]
    s.update(shot)
    if s.get('picture') is None:
        s.pop('picture'), s.pop('prompt'), s.update(card='Hi')
    say(bool(check_plan(bad_plan)[0]), f'the plan check refuses {what}')
# Bittu & Riya stories: the rules, the lengths, the link and the checker agree.
from check_plan import KEEP, WPS_BY_LANGUAGE  # noqa: E402
stories = (CAST / 'STORIES.md').read_text()
say(dict(zip(('Bittu', 'Riya'), keep)) == KEEP, 'the plan check uses the keep-lines from CAST.md, word for word')
say('cast/bittu-riya/STORIES.md' in flows['new-film'] and 'instead of steps 1 to 6' in flows['new-film'],
    '/new-film hands a one-liner about Bittu or Riya to the story steps')
say(all(f'| {n} |' in stories for n in ('90 seconds', '3 minutes', '6 minutes', '9 minutes', '12 minutes', '15 minutes')),
    'stories come in 90 s, 3, 6, 9, 12 and 15 minutes')
link = 'https://flow.google.com/project/983f2d4b-d432-439c-8283-587e8c9865c9'
say(link in cast_md and link in mp and 'from\n     its link' in mp and 'sign in' in mp, '/make-pictures has Roshan open the Bittu & Riya project from its link in Chrome')
say('invented adventure in a real world' in stories and 'every fact it shows is real' in rule,
    'a story is invented, the facts in it are real')
say('medium shot or close-up' in mp and 'Judge them only in medium shots and close-ups' in cast_md,
    'earrings, pendant and watch are judged only in medium shots and close-ups')
for lang, per_min in (('en', 165), ('hi', 200)):
    say(abs(WPS_BY_LANGUAGE[lang] * 60 - per_min) <= 5 and f'{per_min}' in (DOCS / '1_SCRIPT_RULES.md').read_text(),
        f'the guide and the plan check agree on the {lang} voice: about {per_min} words a minute')
look = 'a tall stone-age man with a bushy black beard and a brown fur wrap'
story = {'title': 'T', 'style': 's', 'cast': 'Bittu & Riya', 'extras': {'Ugg': look}, 'shots': [
    {'say': 'one two three four five six', 'picture': '001', 'prompt': f'Bittu meets Ugg, {look}. {KEEP["Bittu"]}', 'who': ['Bittu']}]}
say(check_plan(story) == ([], check_plan(story)[1]) and len(check_plan(story)[1]) == 1, 'a good story plan has no errors and no warnings')
loose = json.loads(json.dumps(story))
loose['shots'][0]['prompt'] = f'Bittu meets Ugg the caveman. {KEEP["Bittu"]}'
say(any('Ugg' in w for w in check_plan(loose)[1]), 'the plan check warns when a one-off person appears without their look')
loose['shots'][0]['prompt'] = f'Bittu meets Ugg, {look}.'
say(any('keep-line' in w for w in check_plan(loose)[1]), 'the plan check warns when a prompt lacks a keep-line')
for bad_line in ('"voice": "', '"speed": '):
    say(not any(bad_line in (DOCS / n).read_text() for n in ('4_PLAN_FORMAT.md', '5_SHORTS.md')),
        f'no example in the guide sets {bad_line.split(":")[0]} (writers copy examples)')
tmp = pathlib.Path(tempfile.mkdtemp())
for f in ('check_plan.py', 'voices.py'):
    shutil.copy(ROOT / 'engine' / f, tmp / f)
r = subprocess.run([sys.executable, '-I', str(tmp / 'check_plan.py'), str(ROOT / 'examples' / 'rain-short-plan.json')],
                   capture_output=True, text=True)
say(r.returncode == 0 and 'ready' in r.stdout, 'the plan check runs on its own from the project\'s tools folder')

print('\nall good' if not bad else f'\n{bad} failing')
sys.exit(1 if bad else 0)
