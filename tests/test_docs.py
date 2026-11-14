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
n = len((DOCS / 'PROJECT_INSTRUCTIONS.md').read_text(encoding='utf-8'))
say(n < 8000, f'PROJECT_INSTRUCTIONS.md is {n} characters, under 8,000')
prompts = [s['prompt'] for s in ex['shots'] if 'prompt' in s]
say(all(p.endswith(ex['style']) for p in prompts), 'every picture prompt ends with the style block')
say(all(ex['character'] in p for p in prompts), 'every picture prompt describes the lead the same way')
print('\nall good' if not bad else f'\n{bad} failing')
sys.exit(1 if bad else 0)
