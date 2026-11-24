"""Hugging Face downloads that survive a busy day.

GitHub's computers share a few internet addresses, and Hugging Face limits
how often one address may ask for anything without an account. On 24 Nov
2026 the Hindi voice test was turned away ("429 Too Many Requests ... Retry
after 124 seconds") while every model it needed was already in GitHub's
cache: it had only asked for the list of the Hindi model's files. A Hindi
film records its voice on up to 16 computers at once, so every question
counts. So:

- a model already in the cache (GitHub keeps it between films) is read
  from there without asking Hugging Face anything;
- "too many requests" or a server hiccup waits as long as Hugging Face asks
  (a minute if it does not say) and tries again, up to TRIES times.

Nothing here needs huggingface_hub to be installed until a download is
actually made.
"""
import os
import pathlib
import re
import time

TRIES = 5
BUSY = (429, 500, 502, 503, 504)


def cache_dir():
    """Where Hugging Face keeps downloaded models, as huggingface_hub decides it."""
    for k in ('HF_HUB_CACHE', 'HUGGINGFACE_HUB_CACHE'):
        if os.environ.get(k):
            return pathlib.Path(os.environ[k])
    home = os.environ.get('HF_HOME') or os.path.join(os.path.expanduser('~'), '.cache', 'huggingface')
    return pathlib.Path(home) / 'hub'


def cached_files(repo, revision):
    """The files of `repo` at commit `revision` already in the cache ([] if none)."""
    if not revision:
        return []
    snap = cache_dir() / ('models--' + repo.replace('/', '--')) / 'snapshots' / revision
    if not snap.is_dir():
        return []
    return sorted(p.relative_to(snap).as_posix() for p in snap.rglob('*') if p.is_file())


def wait_for(error):
    """Seconds to wait before asking again after `error`, or None when asking
    again cannot help (a missing file, a wrong name)."""
    status, after, text = None, None, ''
    e, seen = error, 0
    while e is not None and seen < 6:            # the error, and what caused it
        seen += 1
        text += ' ' + str(e)
        resp = getattr(e, 'response', None)
        code = getattr(resp, 'status_code', None)
        if code is not None and status is None:
            status = code
            after = (getattr(resp, 'headers', None) or {}).get('Retry-After')
        e = e.__cause__ or e.__context__
    if status is None:
        m = re.search(r'\b(429|50[0234])\b', text) or re.search(r'Too Many Requests', text)
        status = (int(m.group(1)) if m.groups() else 429) if m else None
    if status not in BUSY:
        return None
    if after is None:
        m = re.search(r'[Rr]etry after (\d+) seconds', text)
        after = m.group(1) if m else None
    try:
        return min(300, max(5, int(after) + 5))
    except (TypeError, ValueError):
        return 60


def patient(fn, *args, sleep=time.sleep, **kwargs):
    """fn(*args, **kwargs), asked again while Hugging Face is busy."""
    for attempt in range(1, TRIES + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            wait = wait_for(e)
            if wait is None or attempt == TRIES:
                raise
            print(f'Hugging Face is busy ({type(e).__name__}); waiting {wait} s, then try {attempt + 1} of {TRIES}',
                  flush=True)
            sleep(wait)


def download(repo, name, revision):
    """The local path of one file: from the cache if it is there, else fetched."""
    from huggingface_hub import hf_hub_download
    try:
        return hf_hub_download(repo, name, revision=revision, local_files_only=True)
    except Exception:  # noqa: BLE001 -- not cached yet
        return patient(hf_hub_download, repo, name, revision=revision)


def repo_files(repo, revision, needs):
    """The repo's file names: the cached ones when they include a file for
    which needs(name) is true, else the list from Hugging Face."""
    files = cached_files(repo, revision)
    if any(needs(f) for f in files):
        return files
    from huggingface_hub import list_repo_files
    return patient(list_repo_files, repo, revision=revision)


def load(cls, repo, revision):
    """cls.from_pretrained(repo), from the cache first, else fetched patiently."""
    if cached_files(repo, revision):
        try:
            return cls.from_pretrained(repo, revision=revision, local_files_only=True)
        except Exception:  # noqa: BLE001 -- the cache lacks a file it needs
            pass
    return patient(cls.from_pretrained, repo, revision=revision)
