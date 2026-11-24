"""Post a finished upright Bittu Ki Riya film on Instagram as a Reel.

The route is Meta's "Instagram API with Instagram Login": it needs an
Instagram professional account and no Facebook Page. Two things about it
shape everything here:

- Instagram does not take the film's bytes; it fetches the film from a
  public link. The workflow puts Instagram's copy on a short-lived GitHub
  release (film-<slug>) of this public repository, and deletes it as soon
  as the post is done.
- The key (a long-lived Instagram token) lasts 60 days. A weekly workflow
  (instagram-token.yml) renews it and, when Instagram hands back a new one,
  saves it as the INSTAGRAM_TOKEN secret.

What is posted:

- upright films only (Roshan's choice, 24 Nov 2026); a wide film is left
  to YouTube;
- Instagram's copy keeps the picture as it is, with the sound at 128 kbps
  and no MP4 edit lists, as the Reels rules ask;
- the caption is the plan's "youtube" caption and question, then the
  hashtags (#BittuKiRiya first, no #Shorts), within Instagram's 2,200
  characters and 30 hashtags;
- shown in the feed as well as in Reels (share_to_feed);
- only to the account named in INSTAGRAM_ACCOUNT, checked before anything
  is sent.

    python3 engine/instagram.py should  FILM.mp4 [--record instagram/SLUG.json --run RUN]
    python3 engine/instagram.py prepare FILM.mp4 OUT.mp4
    python3 engine/instagram.py post    PLAN OUT.mp4 --url PUBLIC_URL --record instagram/SLUG.json --run RUN
    python3 engine/instagram.py check
    python3 engine/instagram.py refresh --out FILE

Setup, once: docs/INSTAGRAM-SETUP.md. Nothing here prints the key.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import youtube  # noqa: E402  (the caption and hashtag rules are shared)

VERSION = 'v26.0'
SETUP = 'docs/INSTAGRAM-SETUP.md'
MAX_CAPTION = 2200
MAX_HASHTAGS = 30
WAIT_SECONDS = 15
WAIT_TRIES = 40          # 10 minutes for Instagram to fetch and process the film


class Refused(Exception):
    """Instagram said no; the message says what to do about it."""


def api():
    test = os.environ.get('INSTAGRAM_TEST_SERVER', '')
    if test:
        if not re.fullmatch(r'http://127\.0\.0\.1:\d+', test):
            raise Refused('INSTAGRAM_TEST_SERVER may only point at this computer')
        return test
    return 'https://graph.instagram.com'


def token():
    t = os.environ.get('INSTAGRAM_TOKEN', '').strip()
    if t and os.environ.get('GITHUB_ACTIONS'):
        print('::add-mask::' + t)
    return t


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def call(method, url, fields=None, timeout=120):
    """(status, headers, json body). The key travels in the body or the query,
    and no address is ever printed."""
    data = urllib.parse.urlencode(fields).encode() if fields is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with _opener.open(req, timeout=timeout) as r:
            status, headers, raw = r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
    except urllib.error.HTTPError as e:
        status, headers, raw = e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read() or b''
    try:
        body = json.loads(raw or b'{}')
    except ValueError:
        body = {}
    return status, headers, body


def get(path, **params):
    params['access_token'] = token()
    return call('GET', f'{api()}/{VERSION}/{path}?{urllib.parse.urlencode(params)}')


def post_form(path, **fields):
    fields['access_token'] = token()
    return call('POST', f'{api()}/{VERSION}/{path}', fields)


def explain(what, body):
    """A plain sentence for Instagram's refusal. Its message never holds the key."""
    err = body.get('error') if isinstance(body, dict) else None
    if not isinstance(err, dict):
        return f'{what} was refused, with no reason given'
    code, sub = err.get('code'), err.get('error_subcode')
    msg = youtube.clean(err.get('error_user_msg') or err.get('message') or '')[:300]
    if code == 190:
        return (f'{what}: the Instagram key no longer works (it expired or was withdrawn). Make a new one: '
                f'{SETUP}, steps 3 and 4.')
    if code in (10, 200, 3) or 'permission' in msg.lower():
        return (f'{what}: the key lacks a permission. Make it again with instagram_business_basic and '
                f'instagram_business_content_publish: {SETUP}, step 3.')
    if code in (4, 9, 17, 32, 613) or sub == 2207042:
        return f'{what}: Instagram\'s posting limit for today is reached. Re-run this job tomorrow.'
    return f'{what} was refused (code {code}{"/" + str(sub) if sub else ""}). Instagram says: {msg or "nothing"}'


# --- the film ----------------------------------------------------------------

def shape(film):
    out = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                     'stream=width,height:format=duration', '-of', 'json', str(film)],
                                    capture_output=True, text=True, check=True).stdout)
    s = out['streams'][0]
    return int(s['width']), int(s['height']), float(out['format']['duration'])


def should(film, record=None, run=''):
    """(True, '') when the film goes to Instagram, else (False, why not)."""
    if not os.environ.get('INSTAGRAM_TOKEN', '').strip():
        return False, f'Instagram is not set up yet, so the film was not posted there ({SETUP})'
    w, h, seconds = shape(film)
    if h <= w:
        return False, 'a wide film: Instagram gets upright films only'
    if not 3 <= seconds <= 15 * 60:
        return False, f'{seconds:.0f} s: Instagram takes Reels of 3 seconds to 15 minutes'
    if record and run:
        try:
            old = json.loads(pathlib.Path(record).read_text())
        except (OSError, ValueError):
            old = {}
        if str(old.get('run')) == str(run) and old.get('url'):
            return False, f'already posted from this run: {old["url"]}'
    return True, ''


def prepare(film, out):
    """Instagram's copy: the same picture; sound at 128 kbps; no edit lists; index first."""
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(film), '-map', '0:v:0', '-map', '0:a:0',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2',
                    '-use_editlist', '0', '-movflags', '+faststart', str(out)], check=True)
    data = pathlib.Path(out).read_bytes()
    if b'elst' in data or data.find(b'moov') > data.find(b'mdat'):
        raise Refused('Instagram\'s copy still has an edit list or its index at the end')
    size = len(data)
    if size > 300 * 1024 * 1024:
        raise Refused(f'Instagram\'s copy is {size / 2**20:.0f} MB; Reels may be at most 300 MB')
    return size


def caption(plan):
    body, _ = youtube.metadata(plan, short=False)
    text = body['snippet']['description']
    tags = text.split('\n')[-1].split()[:MAX_HASHTAGS]
    words = text.rsplit('\n\n', 1)[0]
    tail = '\n\n' + ' '.join(tags)
    if len(words) + len(tail) > MAX_CAPTION:
        words = youtube.cut(words, MAX_CAPTION - len(tail))
    return words + tail


# --- posting -----------------------------------------------------------------

def account():
    status, _, body = get('me', fields='user_id,username')
    if status != 200 or not body.get('user_id'):
        raise Refused(explain('Signing in to Instagram', body))
    return str(body['user_id']), body.get('username', '?')


def check_account(username):
    want = os.environ.get('INSTAGRAM_ACCOUNT', '').strip().lstrip('@').lower()
    if not want:
        raise Refused(f'INSTAGRAM_ACCOUNT is not set, so the account cannot be checked; nothing was posted '
                      f'({SETUP}, step 4)')
    if username.lower() != want:
        raise Refused(f'The key belongs to @{username}, not @{want}. Nothing was posted. Make the key again '
                      f'signed in as @{want}: {SETUP}, step 3.')


def final_address(url):
    """Where a public link really points: GitHub's download links redirect
    to their file store, and Instagram may not follow a redirect."""
    req = urllib.request.Request(url, method='HEAD')
    try:
        with _opener.open(req, timeout=60) as r:
            return url if r.status == 200 else None
    except urllib.error.HTTPError as e:
        loc = (e.headers or {}).get('Location')
        return loc if e.code in (301, 302, 303, 307, 308) and loc else None
    except (OSError, urllib.error.URLError):
        return None


def container(user_id, url, text, sleep=time.sleep):
    """A Reel container for the film at `url`, once Instagram has fetched it.
    Returns (container id, '') or (None, why it failed)."""
    status, _, body = post_form(f'{user_id}/media', media_type='REELS', video_url=url, caption=text,
                                share_to_feed='true')
    if status != 200 or not body.get('id'):
        raise Refused(explain('Starting the Reel', body))
    cid = body['id']
    for _ in range(WAIT_TRIES):
        status, _, body = get(cid, fields='status_code,status')
        code = body.get('status_code')
        if code == 'FINISHED':
            return cid, ''
        if code in ('ERROR', 'EXPIRED'):
            return None, youtube.clean(body.get('status') or code)
        if status != 200:
            raise Refused(explain('Waiting for Instagram', body))
        sleep(WAIT_SECONDS)
    return None, 'Instagram was still processing the film after 10 minutes'


def post(plan, film, url, record=None, run='', sleep=time.sleep):
    user_id, username = account()
    check_account(username)
    text = caption(plan)
    tried, why = [], ''
    for address in (url, final_address(url)):
        if not address or address in tried:
            continue
        tried.append(address)
        cid, why = container(user_id, address, text, sleep)
        if cid:
            break
    else:
        raise Refused(f'Instagram could not take the film: {why or "no usable link"}. Re-run this job.')
    status, _, body = post_form(f'{user_id}/media_publish', creation_id=cid)
    if status != 200 or not body.get('id'):
        raise Refused(explain('Publishing the Reel', body))
    media = body['id']
    status, _, body = get(media, fields='permalink')
    link = body.get('permalink') or f'https://www.instagram.com/{username}/'
    out = {
        'slug': pathlib.Path(record).stem if record else pathlib.Path(film).stem,
        'media_id': media,
        'url': link,
        'account': username,
        'run': str(run),
        'at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
    if record:
        pathlib.Path(record).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(record).write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return out


def refresh(out_file):
    """Renew the key for 60 more days. Writes the key to out_file only when
    Instagram hands back a different one (the workflow then saves it)."""
    old = token()
    if not old:
        raise Refused(f'INSTAGRAM_TOKEN is not set ({SETUP}, step 4)')
    q = urllib.parse.urlencode({'grant_type': 'ig_refresh_token', 'access_token': old})
    status, _, body = call('GET', f'{api()}/refresh_access_token?{q}')
    new = body.get('access_token')
    if status != 200 or not new:
        raise Refused(explain('Renewing the Instagram key', body))
    if os.environ.get('GITHUB_ACTIONS'):
        print('::add-mask::' + new)
    days = int(body.get('expires_in', 0)) // 86400
    if new != old:
        fd = os.open(out_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(new)
        return f'Instagram gave a new key, good for {days} days; it is being saved'
    return f'the Instagram key is renewed: good for {days} more days'


# --- the command line --------------------------------------------------------

def opt(argv, name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


def main(argv):
    if not argv or argv[0] not in ('should', 'prepare', 'post', 'check', 'refresh'):
        print(__doc__)
        return 2
    mode = argv[0]
    try:
        if mode == 'should':
            go, why = should(argv[1], opt(argv, '--record'), opt(argv, '--run', ''))
            print('go' if go else 'skip: ' + why)
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                    f.write(f'go={"yes" if go else "no"}\n')
            if not go:
                youtube.summary('## Instagram: not posted\n\n' + why + '\n')
            return 0
        if mode == 'prepare':
            size = prepare(argv[1], argv[2])
            print(f'Instagram\'s copy: {size / 2**20:.1f} MB, sound at 128 kbps, no edit lists')
            return 0
        if mode == 'check':
            _, username = account()
            check_account(username)
            print(f'The Instagram key works and belongs to @{username}. Upright films will be posted there.')
            youtube.summary(f'## Instagram key works\n\nIt belongs to @{username}.\n')
            return 0
        if mode == 'refresh':
            print(refresh(opt(argv, '--out', '/tmp/instagram-token')))
            return 0
        plan = json.loads(pathlib.Path(argv[1]).read_text(encoding='utf-8-sig'))
        out = post(plan, argv[2], opt(argv, '--url'), opt(argv, '--record'), opt(argv, '--run', ''))
        print(f'Posted on Instagram: {out["url"]}')
        youtube.summary(f'## On Instagram\n\n{out["url"]}\n')
        return 0
    except (Refused, OSError, urllib.error.URLError, subprocess.CalledProcessError) as e:
        why = str(e) if isinstance(e, Refused) else f'Instagram could not be reached ({type(e).__name__}). Re-run this job.'
        print('NOT POSTED: ' + why if mode == 'post' else 'FAILED: ' + why)
        youtube.summary(f'## Instagram: {"NOT POSTED" if mode == "post" else "problem"}\n\n{why}\n')
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
