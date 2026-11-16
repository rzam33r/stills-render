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
- Every Python step has its packages installed by an earlier step in the same
  job. On 15 Nov 2026 the film workflow's "Which voice" step loaded the voice
  code before numpy was installed, and the first film from the upload page's
  still-picture tab stopped at "Voice recorded -- failed". The tests had only
  run copies of the film's steps, never the steps themselves.
"""
import ast
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

# Workflows that never make a film: lock-versions.yml writes the locks, and
# voice-compare.yml and voice-score.yml try new voice models before one is chosen.
EXPERIMENTS = {'lock-versions.yml', 'voice-compare.yml', 'voice-score.yml'}
loose = []
for n, t in texts.items():
    if n in EXPERIMENTS:
        continue
    for k, line in enumerate(t.splitlines(), 1):
        if re.search(r'\bpip install\b', line) and 'locks/' not in line and 'pyyaml' not in line:
            loose.append(f'{n}:{k}')
say(not loose, 'every pip install uses the versions in locks/' + ('' if not loose else f': {loose}'))

mf = flows['make-film.yml']
on = mf.get('on', mf.get(True))
inputs = set(on['workflow_dispatch']['inputs'])
page = {'slug', 'build', 'deliver', 'frame', 'ignore_plan_errors', 'logo', 'keep_pictures'}
# Inputs only tests send; each must have a default so the page never needs it.
tests_only = {'voice_parts'}
spec = on['workflow_dispatch']['inputs']
say(inputs == page | tests_only and all('default' in spec[k] for k in tests_only),
    'make-film accepts the inputs the upload page sends, plus test-only inputs that have defaults')
deliver = mf['jobs']['deliver']
say(deliver.get('uses') == './.github/workflows/final-video-delivery.yml'
    and set(deliver.get('secrets', {})) == {'UPLOAD_TOKEN', 'DRIVE_ENDPOINT_URL'},
    'the delivery gets the two Drive secrets')

commits = [n for n, t in texts.items() if re.search(r'git add [^\n]*(\.mp4|\.png|\.jpg|\.zip|story/|output/)', t)]
say(not commits, 'no workflow commits pictures, ZIPs or films')

# --- every Python step has what it imports --------------------------------
DIST = {'numpy': 'numpy', 'soundfile': 'soundfile', 'PIL': 'pillow', 'yaml': 'pyyaml',
        'kokoro': 'kokoro', 'scipy': 'scipy', 'azure': 'azure-cognitiveservices-speech',
        'torch': 'torch', 'phonemizer': 'phonemizer-fork', 'espeakng_loader': 'espeakng-loader'}
LOCAL = [ROOT / 'engine', ROOT / 'tests', ROOT / 'tools']


def norm(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def lock_names(path):
    return {norm(re.split(r'[=<>~!\[; ]', ln.strip())[0]) for ln in (ROOT / path).read_text().splitlines()
            if ln.strip() and not ln.lstrip().startswith(('#', '-'))}


def pip_packages(line):
    """The packages one `pip install` line installs."""
    words = line.split('pip install', 1)[1].split()
    out, i = set(), 0
    while i < len(words):
        w = words[i]
        if w == '-r':
            out |= lock_names(words[i + 1]); i += 2; continue
        if w in ('-c', '--extra-index-url', '--index-url'):
            i += 2; continue
        if not w.startswith('-') and not w.startswith(('$', '"', "'")):
            out.add(norm(re.split(r'[=<>~!\[]', w)[0]))
        i += 1
    return out


def top_imports(tree):
    """Module names imported when the code is loaded (not inside functions)."""
    names = set()

    def visit(nodes):
        for n in nodes:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(n, ast.Import):
                names.update(a.name.split('.')[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                names.add(n.module.split('.')[0])
            for field in ('body', 'orelse', 'finalbody', 'handlers'):
                visit(getattr(n, field, []) or [])
    visit(tree.body)
    return names


def needs(code, seen=None):
    """Third-party packages the code needs at load time, following local modules."""
    seen = set() if seen is None else seen
    out = set()
    for name in top_imports(ast.parse(code)):
        local = next((d / f'{name}.py' for d in LOCAL if (d / f'{name}.py').exists()), None)
        if local:
            if local not in seen:
                seen.add(local)
                out |= needs(local.read_text(), seen)
        elif name in sys.stdlib_module_names or name == '__future__':
            continue
        else:
            out.add(DIST.get(name, '?' + name))
    return out


missing = []
for n, w in flows.items():
    if n in EXPERIMENTS:
        continue
    for job, spec in (w.get('jobs') or {}).items():
        have = set()
        for step in spec.get('steps') or []:
            lines = str(step.get('run') or '').splitlines()
            k = 0
            while k < len(lines):
                line = lines[k]
                if re.search(r'\bpip install\b', line):
                    have |= pip_packages(line)
                checks = []
                for script in re.findall(r'python3\s+(?:-\S+\s+)*((?:engine|tests|tools)/[\w/]+\.py)', line):
                    checks.append((script, (ROOT / script).read_text()))
                h = re.search(r"python3\s+-\s*<<-?\s*'?(\w+)'?", line)
                if h:
                    end = next(j for j in range(k + 1, len(lines)) if lines[j].strip() == h.group(1))
                    import textwrap
                    checks.append((f'inline Python at line {k + 1}', textwrap.dedent('\n'.join(lines[k + 1:end]))))
                    k = end
                for what, code in checks:
                    lack = {p for p in needs(code) if norm(p) not in have}
                    if lack:
                        missing.append(f'{n} / {job} / "{step.get("name", "?")}": {what} needs {sorted(lack)}')
                k += 1
say(not missing, 'every Python step has its packages installed first'
    + ('' if not missing else ':\n       ' + '\n       '.join(missing)))

print('\nall good' if not bad else f'\n{bad} failing')
sys.exit(1 if bad else 0)
