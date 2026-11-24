"""A busy Hugging Face is waited for, and a cached model never asks it anything.

    python3 tests/test_hf.py

On 24 Nov 2026 the Hindi voice test was turned away by Hugging Face ("429
Too Many Requests ... Retry after 124 seconds") although its models were in
GitHub's cache: it asked for the Hindi model's file list every time.
"""
import os
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
import hf  # noqa: E402

bad = 0


def say(ok, msg):
    global bad
    bad += not ok
    print(('ok   ' if ok else 'FAIL ') + msg)


class Response:
    def __init__(self, code, headers=None):
        self.status_code, self.headers = code, headers or {}


class HTTPError(Exception):
    def __init__(self, msg, code=None, headers=None):
        super().__init__(msg)
        self.response = Response(code, headers) if code else None


real = ("429 Too Many Requests: you have reached your 'api' rate limit.\n"
        "Retry after 124 seconds (0/500 requests remaining in current 300s window).")
say(hf.wait_for(HTTPError(real)) == 129, 'the 24 Nov refusal is waited out: 124 s asked, 129 s waited')
say(hf.wait_for(HTTPError('busy', 429, {'Retry-After': '30'})) == 35, 'a Retry-After header is obeyed')
say(hf.wait_for(HTTPError('down', 503)) == 60, 'a server hiccup waits a minute')
say(hf.wait_for(HTTPError('no such file', 404)) is None, 'a missing file is not asked for again')
try:
    try:
        raise HTTPError(real)
    except HTTPError as inner:
        raise OSError('We could not connect to huggingface.co') from inner
except OSError as outer:
    say(hf.wait_for(outer) == 129, 'a refusal wrapped in another error (as transformers does) is still seen')

calls, slept = [], []


def flaky():
    calls.append(1)
    if len(calls) < 3:
        raise HTTPError(real)
    return 'model'


say(hf.patient(flaky, sleep=slept.append) == 'model' and slept == [129, 129], 'asked again after each wait, then it works')
calls.clear()
try:
    hf.patient(lambda: (_ for _ in ()).throw(HTTPError('gone', 404)), sleep=slept.append)
    say(False, 'a missing file fails at once')
except HTTPError:
    say(True, 'a missing file fails at once')
always, slept = [], []
try:
    hf.patient(lambda: always.append(1) or (_ for _ in ()).throw(HTTPError(real)), sleep=slept.append)
except HTTPError:
    pass
say(len(always) == hf.TRIES and len(slept) == hf.TRIES - 1, f'it gives up after {hf.TRIES} tries')

cache = pathlib.Path(tempfile.mkdtemp())
os.environ['HF_HUB_CACHE'] = str(cache)
rev = '82ca71273cc2a9ab19efdf8315f865c1a5af0ee7'
snap = cache / 'models--ResembleAI--Chatterbox-Multilingual-hi' / 'snapshots' / rev
(snap / 'sub').mkdir(parents=True)
blob = cache / 'blob'
blob.write_text('x')
(snap / 't3_hi.safetensors').symlink_to(blob)
(snap / 's3gen_hi.pt').symlink_to(blob)
(snap / 'gone.pt').symlink_to(cache / 'missing')       # a broken link is not a file
(snap / 'sub' / 'a.json').write_text('{}')
files = hf.cached_files('ResembleAI/Chatterbox-Multilingual-hi', rev)
say(files == ['s3gen_hi.pt', 'sub/a.json', 't3_hi.safetensors'], f'the cached files are found: {files}')
say(hf.cached_files('ResembleAI/Chatterbox-Multilingual-hi', 'f' * 40) == [] and hf.cached_files('x/y', None) == [],
    'another revision, or none, is not in the cache')
asked = []
sys.modules['huggingface_hub'] = type(sys)('huggingface_hub')
sys.modules['huggingface_hub'].list_repo_files = lambda *a, **k: asked.append(1) or ['t3_new.safetensors']
got = hf.repo_files('ResembleAI/Chatterbox-Multilingual-hi', rev, lambda f: f.startswith('t3'))
say(got == files and not asked, 'a cached model lists its files without asking Hugging Face')
got = hf.repo_files('ResembleAI/Chatterbox-Multilingual-hi', 'f' * 40, lambda f: f.startswith('t3'))
say(got == ['t3_new.safetensors'] and asked, 'a model not in the cache asks Hugging Face for its list')

print('\nall good' if not bad else f'\n{bad} failing')
sys.exit(1 if bad else 0)
