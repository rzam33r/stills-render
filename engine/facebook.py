"""Post a finished upright Bittu Ki Riya film on the Bittu Ki Riya Facebook Page.

Facebook lets apps post only to a Page, never to a person's profile, so the
film goes to the Page (FACEBOOK_PAGE_ID, written into the workflows):

- up to 90 seconds: as a Reel (Meta's Reels Publishing API takes 3 to 90 s);
- longer: as an ordinary Page video. Facebook shows an upright video full
  screen, but it is not a Reel.

The film's bytes go straight to Meta (no public link, unlike Instagram).
Instagram's copy is used (engine/instagram.py prepare): sound at 128 kbps,
no MP4 edit lists, index first, which also meets Facebook's Reels rules.

The key (FACEBOOK_TOKEN) is a never-expiring system-user key of Roshan's
business portfolio, allowed to post to the Page. From it this asks Meta for
the Page's own key at every run, and posts only to FACEBOOK_PAGE_ID, checked
before anything is sent. The caption is Instagram's: the plan's "youtube"
caption and question, then the hashtags (#BittuKiRiya first, no #Shorts).

    python3 engine/facebook.py should FILM.mp4 [--record facebook/SLUG.json --run RUN]
    python3 engine/facebook.py post   PLAN FILM.mp4 --record facebook/SLUG.json --run RUN
    python3 engine/facebook.py check

Setup, once: docs/FACEBOOK-SETUP.md. Nothing here prints a key.
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
import uuid
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import instagram  # noqa: E402  (the film's shape, its copy and the caption are shared)
import youtube  # noqa: E402

VERSION = 'v26.0'
SETUP = 'docs/FACEBOOK-SETUP.md'
REEL_SECONDS = 90
WAIT_SECONDS = 15
WAIT_TRIES = 40          # 10 minutes for Facebook to process the film


class Refused(Exception):
    """Facebook said no; the message says what to do about it."""


def hosts():
    """(the API, the upload host for Reels, the upload host for videos)."""
    test = os.environ.get('FACEBOOK_TEST_SERVER', '')
    if test:
        if not re.fullmatch(r'http://127\.0\.0\.1:\d+', test):
            raise Refused('FACEBOOK_TEST_SERVER may only point at this computer')
        return test, test, test
    return 'https://graph.facebook.com', 'https://rupload.facebook.com', 'https://graph-video.facebook.com'


_masked = set()


def mask(t):
    if t and os.environ.get('GITHUB_ACTIONS') and t not in _masked:
        print('::add-mask::' + t)
        _masked.add(t)
    return t


def key():
    return mask(os.environ.get('FACEBOOK_TOKEN', '').strip())


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def send(method, url, data=None, headers=None, timeout=300):
    """(status, json body). No address or key is ever printed."""
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with _opener.open(req, timeout=timeout) as r:
            status, raw = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read() or b''
    try:
        body = json.loads(raw or b'{}')
    except ValueError:
        body = {}
    return status, body if isinstance(body, dict) else {}


def get(path, token, **params):
    params['access_token'] = token
    return send('GET', f'{hosts()[0]}/{VERSION}/{path}?{urllib.parse.urlencode(params)}')


def post_form(path, token, **fields):
    fields['access_token'] = token
    return send('POST', f'{hosts()[0]}/{VERSION}/{path}', urllib.parse.urlencode(fields).encode(),
                {'Content-Type': 'application/x-www-form-urlencoded'})


def explain(what, body):
    """A plain sentence for Facebook's refusal. Its message never holds a key."""
    err = body.get('error') if isinstance(body, dict) else None
    if not isinstance(err, dict):
        return f'{what} was refused, with no reason given'
    code, sub = err.get('code'), err.get('error_subcode')
    msg = youtube.clean(err.get('error_user_msg') or err.get('message') or '')[:300]
    if code == 190:
        return (f'{what}: the Facebook key no longer works (it was withdrawn or replaced). Make a new one: '
                f'{SETUP}, steps 3 and 4.')
    if code in (10, 200, 3) or 'permission' in msg.lower():
        return (f'{what}: the key may not post to the Page. Give it pages_manage_posts, pages_read_engagement '
                f'and pages_show_list, with the Page as its asset: {SETUP}, step 3.')
    if code in (4, 9, 17, 32, 613, 368):
        return f'{what}: Facebook\'s posting limit is reached for now. Re-run this job tomorrow.'
    return f'{what} was refused (code {code}{"/" + str(sub) if sub else ""}). Facebook says: {msg or "nothing"}'


# --- the film ----------------------------------------------------------------

def should(film, record=None, run=''):
    """(True, '') when the film goes to the Facebook Page, else (False, why not)."""
    if not os.environ.get('FACEBOOK_TOKEN', '').strip():
        return False, f'Facebook is not set up yet, so the film was not posted there ({SETUP})'
    w, h, seconds = instagram.shape(film)
    if h <= w:
        return False, 'a wide film: the Facebook Page gets upright films only'
    if seconds < 3:
        return False, f'{seconds:.1f} s: Facebook takes videos of at least 3 seconds'
    if record and run:
        try:
            old = json.loads(pathlib.Path(record).read_text())
        except (OSError, ValueError):
            old = {}
        if str(old.get('run')) == str(run) and old.get('url'):
            return False, f'already posted from this run: {old["url"]}'
    return True, ''


# --- the Page ----------------------------------------------------------------

def page():
    """(Page id, Page name, the Page's own key), for FACEBOOK_PAGE_ID only."""
    pid = os.environ.get('FACEBOOK_PAGE_ID', '').strip()
    if not pid.isdigit():
        raise Refused(f'FACEBOOK_PAGE_ID is not set, so the Page cannot be found; nothing was posted ({SETUP})')
    k = key()
    if not k:
        raise Refused(f'FACEBOOK_TOKEN is not set ({SETUP}, step 4)')
    status, body = get(pid, k, fields='id,name,access_token')
    if status == 200 and body.get('access_token') and str(body.get('id')) == pid:
        return pid, body.get('name', '?'), mask(body['access_token'])
    first = body
    # The key may already be the Page's own key, or reach the Page only
    # through the list of Pages it may manage.
    status, me = get('me', k, fields='id,name')
    if status == 200 and str(me.get('id')) == pid:
        return pid, me.get('name', '?'), k
    if status != 200:
        raise Refused(explain('Signing in to Facebook', me))
    status, acc = get('me/accounts', k, fields='id,name,access_token', limit='100')
    for p in acc.get('data') or []:
        if str(p.get('id')) == pid and p.get('access_token'):
            return pid, p.get('name', '?'), mask(p['access_token'])
    if isinstance(first.get('error'), dict) and first['error'].get('code') == 190:
        raise Refused(explain('Signing in to Facebook', first))
    raise Refused(f'The Facebook key works but may not post to Page {pid}; nothing was posted. Give it the Page '
                  f'as an asset with "Create content": {SETUP}, step 3.')


# --- posting -----------------------------------------------------------------

def wait(video, token, sleep=time.sleep):
    """Until Facebook has processed and published the video. '' or why it failed."""
    for _ in range(WAIT_TRIES):
        status, body = get(video, token, fields='status')
        if status != 200:
            raise Refused(explain('Waiting for Facebook', body))
        st = body.get('status') or {}
        phases = {k: (st.get(k) or {}) for k in ('uploading_phase', 'processing_phase', 'publishing_phase')}
        for name, ph in phases.items():
            if ph.get('status') == 'error':
                err = ph.get('error') or {}
                return youtube.clean(err.get('message') or f'{name.split("_")[0]} failed')
        if st.get('video_status') == 'error':
            return 'Facebook could not process the film'
        if phases['publishing_phase'].get('status') == 'complete' or st.get('video_status') == 'ready':
            return ''
        sleep(WAIT_SECONDS)
    return 'Facebook was still processing the film after 10 minutes'


def as_reel(pid, token, film, text, title, sleep=time.sleep):
    status, body = post_form(f'{pid}/video_reels', token, upload_phase='start')
    if status != 200 or not body.get('video_id'):
        raise Refused(explain('Starting the Reel', body))
    video = str(body['video_id'])
    data = pathlib.Path(film).read_bytes()
    status, body = send('POST', f'{hosts()[1]}/video-upload/{VERSION}/{video}', data,
                        {'Authorization': f'OAuth {token}', 'offset': '0', 'file_size': str(len(data)),
                         'Content-Type': 'application/octet-stream'})
    if status != 200 or not body.get('success'):
        raise Refused(explain('Sending the film to Facebook', body))
    status, body = post_form(f'{pid}/video_reels', token, upload_phase='finish', video_id=video,
                             video_state='PUBLISHED', description=text, title=title)
    if status != 200 or not body.get('success'):
        raise Refused(explain('Publishing the Reel', body))
    why = wait(video, token, sleep)
    if why:
        raise Refused(f'Facebook took the Reel but could not publish it: {why}. Check the Page, then re-run this job.')
    return video


def as_video(pid, token, film, text, title, sleep=time.sleep):
    """A film over 90 s: an ordinary Page video, in one upload (films are small)."""
    edge = '----stills' + uuid.uuid4().hex
    parts = []
    for name, value in (('access_token', token), ('description', text), ('title', title), ('published', 'true')):
        parts.append(f'--{edge}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f'--{edge}\r\nContent-Disposition: form-data; name="source"; filename="film.mp4"\r\n'
                 f'Content-Type: video/mp4\r\n\r\n'.encode() + pathlib.Path(film).read_bytes() + b'\r\n')
    parts.append(f'--{edge}--\r\n'.encode())
    status, body = send('POST', f'{hosts()[2]}/{VERSION}/{pid}/videos', b''.join(parts),
                        {'Content-Type': f'multipart/form-data; boundary={edge}'}, timeout=900)
    if status != 200 or not body.get('id'):
        raise Refused(explain('Posting the video', body))
    video = str(body['id'])
    why = wait(video, token, sleep)
    if why:
        raise Refused(f'Facebook took the video but could not publish it: {why}. Check the Page, then re-run this job.')
    return video


def post(plan, film, record=None, run='', sleep=time.sleep):
    pid, name, token = page()
    text = instagram.caption(plan)
    meta, _ = youtube.metadata(plan, short=False)
    title = meta['snippet']['title']
    seconds = instagram.shape(film)[2]
    reel = seconds <= REEL_SECONDS
    video = (as_reel if reel else as_video)(pid, token, film, text, title, sleep)
    status, body = get(video, token, fields='permalink_url')
    link = body.get('permalink_url') or ''
    if link.startswith('/'):
        link = 'https://www.facebook.com' + link
    link = link or f'https://www.facebook.com/{pid}'
    out = {
        'slug': pathlib.Path(record).stem if record else pathlib.Path(film).stem,
        'video_id': video,
        'url': link,
        'as': 'reel' if reel else 'video',
        'page': name,
        'run': str(run),
        'at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
    if record:
        pathlib.Path(record).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(record).write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return out


# --- the command line --------------------------------------------------------

def opt(argv, name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


def main(argv):
    if not argv or argv[0] not in ('should', 'post', 'check'):
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
                youtube.summary('## Facebook: not posted\n\n' + why + '\n')
            return 0
        if mode == 'check':
            _, name, _ = page()
            print(f'The Facebook key works and may post to the Page "{name}". Upright films will be posted there.')
            youtube.summary(f'## Facebook key works\n\nIt may post to the Page "{name}".\n')
            return 0
        plan = json.loads(pathlib.Path(argv[1]).read_text(encoding='utf-8-sig'))
        out = post(plan, argv[2], opt(argv, '--record'), opt(argv, '--run', ''))
        kind = 'a Reel' if out['as'] == 'reel' else 'a video (over 90 s, so not a Reel)'
        print(f'Posted on Facebook as {kind}: {out["url"]}')
        youtube.summary(f'## On Facebook\n\nAs {kind}: {out["url"]}\n')
        return 0
    except (Refused, OSError, urllib.error.URLError, subprocess.CalledProcessError) as e:
        why = str(e) if isinstance(e, Refused) else f'Facebook could not be reached ({type(e).__name__}). Re-run this job.'
        print('NOT POSTED: ' + why if mode == 'post' else 'FAILED: ' + why)
        youtube.summary(f'## Facebook: {"NOT POSTED" if mode == "post" else "problem"}\n\n{why}\n')
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
