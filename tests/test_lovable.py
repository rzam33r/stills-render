"""The upload page's still-picture check is the one in the Lovable prompt, and it works.

    python3 tests/test_lovable.py

- The code in docs/lovable/stills-tab-prompt.md and stills-paste-plan-prompt.md
  is stills-upload-check.js exactly, so pasting either gives Lovable the
  tested code.
- Pictures named the way Google Flow saves them ("1 - Medium shot.jpg") are
  found, and two files for one picture are refused.
- With node: the three examples pass with their pictures, a missing picture
  is named, an animated (Rose) plan is sent to the other tab, a Hindi film
  with an English voice is refused, filmKind tells the two kinds apart, and
  every story name fits make-film.yml's rule.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOV = ROOT / 'docs' / 'lovable'
bad = 0


def say(ok, msg):
    global bad
    bad += not ok
    print(('ok   ' if ok else 'FAIL ') + msg)


code = (LOV / 'stills-upload-check.js').read_text()
prompt = (LOV / 'stills-tab-prompt.md').read_text()
for name in ('stills-tab-prompt.md', 'stills-paste-plan-prompt.md'):
    m = re.search(r'```javascript\n(.*?)```', (LOV / name).read_text(), re.S)
    say(bool(m) and m.group(1) == code, f'{name} carries stills-upload-check.js exactly')
say('rose-render-test' in prompt and 'make-film.yml' in prompt, 'the prompt names both repositories\' workflows')

node = shutil.which('node')
if not node:
    print('skip node checks: node is not installed')
else:
    cases = []
    for f in sorted((ROOT / 'examples').glob('*-plan.json')):
        plan = json.loads(f.read_text())
        names = [f'story/{s[k]}.png' for s in plan['shots'] for k in ('picture', 'doodle') if s.get(k)]
        cases.append({'name': f.name, 'plan': f.read_text(), 'files': ['story/plan.json'] + names})
        first = next(s['picture'] for s in plan['shots'] if s.get('picture'))
        cases.append({'name': f.name + ' without ' + first, 'plan': f.read_text(),
                      'files': [n for n in names if not n.endswith(f'/{first}.png')], 'missing': first})
    rose = json.dumps({'title': 'x', 'scenes': [{'template': 'beat-hold'}]})
    hindi_en = json.loads((ROOT / 'examples' / 'boond-hindi-short-plan.json').read_text())
    hindi_en['voice'] = 'am_michael'
    devanagari = json.loads((ROOT / 'examples' / 'boond-hindi-short-plan.json').read_text())
    devanagari['title'] = 'एक बूँद का सफ़र'
    script = f"""
const {{ checkStillsUpload, filmKind }} = require({json.dumps(str(LOV / 'stills-upload-check.js'))});
const cases = {json.dumps(cases)};
const out = cases.map(c => ({{ name: c.name, missing: c.missing || null, r: checkStillsUpload(c.plan, c.files) }}));
out.push({{ name: 'rose', r: checkStillsUpload({json.dumps(rose)}, ['plan.json']) }});
out.push({{ name: 'hindi-english-voice', r: checkStillsUpload({json.dumps(json.dumps(hindi_en, ensure_ascii=False))},
  {json.dumps(['plan.json'] + [f'{s[k]}.jpg' for s in hindi_en['shots'] for k in ('picture', 'doodle') if s.get(k)])}) }});
out.push({{ name: 'devanagari-title', r: checkStillsUpload({json.dumps(json.dumps(devanagari, ensure_ascii=False))},
  {json.dumps(['plan.json'] + [f'{s[k]}.webp' for s in devanagari['shots'] for k in ('picture', 'doodle') if s.get(k)])}) }});
const flowPlan = {json.dumps(cases[0]['plan'])};
const flowNames = JSON.parse(flowPlan).shots.flatMap(s => ['picture', 'doodle'].filter(k => s[k]).map(k => `Flow/${{Number(s[k])}} - Medium shot of a man.jpg`));
out.push({{ name: 'flow-names', r: checkStillsUpload(flowPlan, flowNames) }});
out.push({{ name: 'flow-duplicate', r: checkStillsUpload(flowPlan, flowNames.concat(['001.png'])) }});
out.push({{ name: 'kinds', r: [filmKind({json.dumps(rose)}), filmKind({json.dumps(cases[0]['plan'])}), filmKind('not json')] }});
console.log(JSON.stringify(out));
"""
    res = subprocess.run([node, '-e', script], capture_output=True, text=True)
    if res.returncode:
        say(False, 'node ran the check: ' + res.stderr.strip()[-400:])
    else:
        slug_rule = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
        for o in json.loads(res.stdout):
            r = o['r']
            if o['name'] == 'kinds':
                say(r == ['animated', 'stills', 'unknown'], f'filmKind tells the kinds apart: {r}')
            elif o['name'] == 'flow-names':
                say(r['ok'], 'Flow-style picture names are found' + ('' if r['ok'] else f': {r["problems"]}'))
            elif o['name'] == 'flow-duplicate':
                say(not r['ok'] and any('two files for picture "001"' in p for p in r['problems']),
                    'two files for one picture are refused')
            elif o['name'] == 'rose':
                say(not r['ok'] and 'Animated films' in r['problems'][0], 'an animated plan is sent to the Animated films tab')
            elif o['name'] == 'hindi-english-voice':
                say(not r['ok'] and any('Hindi voice' in p for p in r['problems']), 'a Hindi film with an English voice is refused')
            elif o['name'] == 'devanagari-title':
                say(r['ok'] and r['slug'].startswith('film-') and slug_rule.match(r['slug']) and len(r['slug']) <= 30,
                    f'a Devanagari title still gets a valid story name: {r["slug"]}')
            elif o['missing']:
                say(not r['ok'] and any(f'"{o["missing"]}"' in p for p in r['problems']),
                    f'{o["name"]}: the missing picture is named')
            else:
                ok = r['ok'] and bool(slug_rule.match(r['slug'])) and len(r['slug']) <= 30
                say(ok, f'{o["name"]}: passes, story name {r["slug"]}, {" / ".join(r["notes"])}'
                    + ('' if r['ok'] else f' PROBLEMS {r["problems"]}'))

print('\nall good' if not bad else f'\n{bad} failed')
sys.exit(1 if bad else 0)
