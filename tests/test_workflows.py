"""Rules the GitHub workflows keep, learned the hard way on the Rose engine.

    python3 tests/test_workflows.py

- Every job names its Ubuntu (ubuntu-24.04). On 13 Nov 2026 "ubuntu-latest"
  moved to Python 3.14, the voice's packages could not install, and a film
  stopped at "Voice recorded -- failed".
- Every pip install takes its versions from locks/, so a new release of the
  voice or a picture library cannot change a film until someone chooses it.
- The film workflow accepts exactly the inputs the upload page sends, and
  passes the Drive secrets to the delivery.
- No workflow commits pictures, ZIPs or films.
"""
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
WF = ROOT / '.github' / 'workflows'
bad = 0


def say(ok, msg):
    global bad
    bad += not ok
    print(('ok   ' if ok else 'FAIL ') + msg)


flows = {f.name: yaml.safe_load(f.read_text()) for f in sorted(WF.glob('*.yml'))}
texts = {f.name: f.read_text() for f in sorted(WF.glob('*.yml'))}

floating = [f'{n}: {job}' for n, w in flows.items() for job, spec in (w.get('jobs') or {}).items()
            if 'runs-on' in spec and not re.fullmatch(r'ubuntu-\d\d\.\d\d', str(spec['runs-on']))]
say(not floating, 'every job names its Ubuntu' + ('' if not floating else f': {floating}'))

loose = []
for n, t in texts.items():
    if n == 'lock-versions.yml':
        continue
    for k, line in enumerate(t.splitlines(), 1):
        if re.search(r'\bpip install\b', line) and 'locks/' not in line and 'pyyaml' not in line:
            loose.append(f'{n}:{k}')
say(not loose, 'every pip install uses the versions in locks/' + ('' if not loose else f': {loose}'))

mf = flows['make-film.yml']
on = mf.get('on', mf.get(True))
inputs = set(on['workflow_dispatch']['inputs'])
page = {'slug', 'build', 'deliver', 'frame', 'ignore_plan_errors', 'logo', 'keep_pictures'}
say(inputs == page, 'make-film accepts exactly the inputs the upload page sends')
deliver = mf['jobs']['deliver']
say(deliver.get('uses') == './.github/workflows/final-video-delivery.yml'
    and set(deliver.get('secrets', {})) == {'UPLOAD_TOKEN', 'DRIVE_ENDPOINT_URL'},
    'the delivery gets the two Drive secrets')

commits = [n for n, t in texts.items() if re.search(r'git add [^\n]*(\.mp4|\.png|\.jpg|\.zip|story/|output/)', t)]
say(not commits, 'no workflow commits pictures, ZIPs or films')

print('\nall good' if not bad else f'\n{bad} failing')
sys.exit(1 if bad else 0)
