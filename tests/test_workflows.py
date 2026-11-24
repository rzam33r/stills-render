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
# Inputs the page never sends; each must have a default so the page never needs it.
tests_only = {"voice_parts", "voice", "youtube", "ending", "instagram"}
spec = on['workflow_dispatch']['inputs']
say(inputs == page | tests_only and all('default' in spec[k] for k in tests_only),
    'make-film accepts the inputs the upload page sends, plus test-only inputs that have defaults')
deliver = mf['jobs']['deliver']
say(deliver.get('uses') == './.github/workflows/final-video-delivery.yml'
    and set(deliver.get('secrets', {})) == {'UPLOAD_TOKEN', 'DRIVE_ENDPOINT_URL'},
    'the delivery gets the two Drive secrets')

# --- every film ends with the Bittu Ki Riya ending ------------------------
steps = [str(s.get('name', '')) + ' ' + str(s.get('run', '')) + ' ' + str(s.get('uses', ''))
         for s in mf['jobs']['render']['steps']]
at = lambda word: next((i for i, s in enumerate(steps) if word in s), -1)  # noqa: E731
say(0 <= at('check_sync.py') < at('engine/ending.py') < at('actions/upload-artifact'),
    'the ending is added after the timing check and before the film is stored for Drive and YouTube')
say((ROOT / 'brand' / 'ending-upright.mp4').exists(), 'the ending video is in brand/')

# --- YouTube: the key reaches only the post step, and only one channel ------
yt = mf['jobs'].get('youtube') or {}
post = next((s for s in yt.get('steps') or [] if 'youtube.py upload' in str(s.get('run', ''))), {})
env = post.get('env') or {}
keyed = {k for k, v in env.items() if 'secrets.' in str(v)}
say(keyed == {'YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_REFRESH_TOKEN'}
    and env.get('YOUTUBE_CHANNEL_ID') == 'UCBJBFuwimmZdoB5DXbRT7kg' and env.get('YOUTUBE_PRIVACY') == 'public',
    'the YouTube step gets the three key secrets and posts publicly to Bittu Ki Riya only')
say('inputs.deliver' in str(yt.get('if', '')) and 'inputs.youtube' in str(yt.get('if', ''))
    and 'deliver' in (yt.get('needs') or []), 'a film goes to YouTube only when it is delivered, after the Drive copy')
leaks = [f'{n}:{k}' for n, t in texts.items() for k, line in enumerate(t.splitlines(), 1)
         if re.search(r'\b(echo|printf|cat)\b', line) and re.search(r'YOUTUBE_(CLIENT_SECRET|REFRESH_TOKEN)|secrets\.', line)]
say(not leaks, 'no workflow prints a secret' + ('' if not leaks else f': {leaks}'))
say(not any('secrets.YOUTUBE' in str(s.get('env', '')) for s in yt.get('steps') or [] if s is not post),
    'only the post step sees the YouTube key')

# --- Instagram: the key reaches only the post step; the public copy goes ---
ig = mf['jobs'].get('instagram') or {}
ig_steps = ig.get('steps') or []
full_key = [s for s in ig_steps if '${{ secrets.INSTAGRAM_TOKEN }}' in str(s.get('env', ''))]
say(len(full_key) == 1 and 'instagram.py post' in str(full_key[0].get('run', ''))
    and 'secrets.INSTAGRAM_ACCOUNT' in str(full_key[0].get('env', '')),
    'only the Instagram post step sees the Instagram key, with the account it must belong to')
gone = [s for s in ig_steps if 'gh release delete' in str(s.get('run', ''))]
say(gone and 'always()' in str(gone[0].get('if', '')), 'Instagram\'s public copy is deleted whatever happens')
say('inputs.deliver' in str(ig.get('if', '')) and 'inputs.instagram' in str(ig.get('if', ''))
    and 'deliver' in (ig.get('needs') or []), 'a film goes to Instagram only when it is delivered, after the Drive copy')
renew = flows.get('instagram-token.yml') or {}
renew_text = texts.get('instagram-token.yml', '')
say('schedule' in (renew.get(True) or renew.get('on') or {}) and 'gh secret set INSTAGRAM_TOKEN' in renew_text
    and 'secrets.GH_SECRETS_TOKEN' in renew_text
    and not any('GH_SECRETS_TOKEN' in t for n, t in texts.items() if n != 'instagram-token.yml'),
    'the Instagram key is renewed weekly; the GitHub key that saves it is used there and nowhere else')

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

# --- a skipped job upstream must not silently skip the jobs after it -------
# GitHub skips a job when ANY job before it in the chain was skipped, unless
# the job's own "if" says otherwise. A short Hindi film skips "voice_more"
# (one part is enough), and that silently skipped "deliver": the film was
# made but never reached Drive. So a job that comes after a job that can be
# skipped must say !cancelled() and check each job it needs by name.
silent = []
for n, w in flows.items():
    jobs = w.get('jobs') or {}

    def before(job, seen=None):
        seen = set() if seen is None else seen
        need = jobs[job].get('needs') or []
        for x in [need] if isinstance(need, str) else need:
            if x not in seen:
                seen.add(x)
                before(x, seen)
        return seen

    for job, spec in jobs.items():
        if not any('if' in jobs[a] for a in before(job)):
            continue
        cond = str(spec.get('if', ''))
        need = spec.get('needs') or []
        need = [need] if isinstance(need, str) else need
        lack = [x for x in need if f'needs.{x}.result' not in cond]
        if not re.search(r'!\s*cancelled\(\)|always\(\)', cond) or lack:
            silent.append(f'{n} / {job}')
say(not silent, 'no job is skipped just because an earlier job was skipped'
    + ('' if not silent else f': {silent}'))

# --- every workflow a job calls exists --------------------------------------
# 18 Nov 2026: final-video-delivery.yml was deleted and re-added; for half a
# minute every film would have failed at its Drive step, and no test noticed.
missing = []
for n, w in flows.items():
    for job, spec in (w.get('jobs') or {}).items():
        uses = str(spec.get('uses', ''))
        if uses.startswith('./.github/workflows/') and not (ROOT / uses[2:]).exists():
            missing.append(f'{n} / {job} -> {uses}')
say(not missing, 'every workflow a job calls exists' + ('' if not missing else f': {missing}'))

# --- every film render can draw its animated graphics -----------------------
# 18 Nov 2026: the example films gained a graphic, and two test jobs rendered
# them without fetching the icons (they had skipped themselves until then).
renders = []
for n in flows:
    for line in (WF / n).read_text().split('\n'):
        if 'engine/render.py' in line and not line.strip().startswith('#'):
            block = line
            renders.append((n, line))
lacking = []
for n, line in renders:
    text_n = (WF / n).read_text()
    i = text_n.index(line)
    stmt = text_n[i:text_n.find('\n', i + len(line))]
    nxt = text_n[i:].split('\n')
    joined = nxt[0] + (' ' + nxt[1] if nxt[0].rstrip().endswith('\\') else '')
    if '--icons' not in joined:
        lacking.append(f'{n}: {line.strip()[:60]}')
say(renders and not lacking, f'all {len(renders)} film renders in the workflows are given the icons'
    + ('' if not lacking else f': {lacking}'))

# --- the repository cleans up after itself ----------------------------------
# Uploaded pictures and finished films must never pile up on GitHub.
uploads = []
for n, w in flows.items():
    for job, spec in (w.get('jobs') or {}).items():
        for step in spec.get('steps') or []:
            if str(step.get('uses', '')).startswith('actions/upload-artifact'):
                days = (step.get('with') or {}).get('retention-days')
                if not isinstance(days, int) or days > 7:
                    uploads.append(f'{n} / {job} / {(step.get("with") or {}).get("name")}')
say(not uploads, 'every stored run file is deleted within 7 days' + ('' if not uploads else f': {uploads}'))
text = {n: (WF / n).read_text() for n in flows}
say('tools/tidy_releases.sh --repo "$REPO" --drop "$PROJECT"' in text.get('final-video-delivery.yml', ''),
    'a delivered film drops its story upload')
say('tools/tidy_releases.sh --repo "$REPO" --keep "$SLUG" --days 7' in text.get('make-film.yml', ''),
    'every film run sweeps uploads nobody came back to (older than 7 days)')
tidy = flows.get('tidy-releases.yml') or {}
say(bool(tidy) and 'schedule' in (tidy.get(True) or tidy.get('on') or {}) and '--days 7' in text.get('tidy-releases.yml', ''),
    'a weekly sweep drops story and film releases older than 7 days')
script = (ROOT / 'tools' / 'tidy_releases.sh').read_text()
say('film-example' in script and 'story-*|film-*' in script, 'the sweep touches only story and film releases, never the example')

print('\nall good' if not bad else f'\n{bad} failing')
sys.exit(1 if bad else 0)
