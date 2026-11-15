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
say(set(flows) == {'new-film', 'make-pictures', 'upload-film', 'fix-plan'}
    and all(t.startswith('---\ndescription: ') for t in flows.values()), 'the four workflows exist, each with a description')
called = {c for t in flows.values() for c in re.findall(r'(?<![\w/])/([a-z]+(?:-[a-z]+)+)\b', t)}
say(called <= set(flows), f'every /workflow a workflow calls exists: {sorted(called)}')
texts = [rule] + list(flows.values()) + [(DOCS / 'PROJECT_INSTRUCTIONS.md').read_text()]
named = {n for t in texts for n in re.findall(r'\b([1-7]_[A-Z_]+\.md)', t)}
say(named and all((DOCS / n).exists() for n in named), f'every guide file named exists ({len(named)} named)')
say(all((DOCS / f'{n}').exists() for n in ('6_LONG_FILMS.md', '7_HINDI_VOICE.md')), 'the long-film and Hindi guide files exist')
keys = {k for t in flows.values() for k in re.findall(r'"([a-z_]+)"', t)} - {'say', 'short', 'wide'}
say(keys <= KEYS | TOP | {'say'}, f'the workflows use only plan keys the engine knows: {sorted(keys)}')
say('`bharat-mein-badhti-mehngai`' in rule and 'at most 30 characters' in rule, 'the story name follows the upload page\'s rule')
url = 'https://picture-plan-film-forge.lovable.app/stills'
say(url in rule and url in flows['upload-film'], 'the rule and /upload-film name the same upload page')
say('plan.json' in flows['upload-film'] and 'Never type' in flows['upload-film'], '/upload-film zips the plan and never types a password')
say('ONE Google Flow project' in rule and 'no other' in flows['make-pictures'], 'pictures are made in the film\'s own Flow project only')
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
