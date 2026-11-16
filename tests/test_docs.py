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
ANSWERS = {'ready', 'yes', 'no'}
keys = {k for t in flows.values() for k in re.findall(r'"([a-z_]+)"', t)} - {'say', 'short', 'wide'} - ANSWERS
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
say('real tag' in mp and 'Never make a picture of Bittu or Riya' in mp and 'Never ask Flow for the' in mp
    and 'first 2 pictures' in mp and 'Never create it' in mp,
    '/make-pictures really tags Bittu and Riya, checks the tags, stops after 2 pictures the first time, never creates the cast project')
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
