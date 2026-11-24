"""Put a finished Bittu Ki Riya film on YouTube.

The words come from the plan's "youtube" section, written with the story:

    "youtube": {
      "title": "Chaand Gayab Ho Gaya! 🌙 Kya Hota Agar...?",
      "caption": "Bittu ne Riya ko chaand gift kar diya... aur duniya ulti ho gayi 🌊",
      "question": "Aap Bittu ki jagah hote toh kya karte?",
      "hashtags": ["#KyaHotaAgar", "#Moon", "#Science"],
      "category": "entertainment"
    }

Every part may be left out. The rules are kept here, in code, instead of
being trusted to whoever wrote the plan:

- the title is the section's "title" (else the plan's), at most 100
  characters (YouTube's limit), without < or >;
- the description is short: the caption, the question, then the hashtags on
  the last line, where YouTube picks up to three to show above the title;
- 3 to 6 hashtags: #BittuKiRiya first, #Shorts on an upright film of 3
  minutes or less and never on a wide one, no spaces, no repeats;
- not made for kids, and no "altered or synthetic" label: YouTube does not
  ask for one on clearly unrealistic content such as cartoons;
- the key must belong to the Bittu Ki Riya channel, checked before a byte of
  the film is sent.

    python3 engine/youtube.py text   PLAN FILM.mp4    # what would be posted
    python3 engine/youtube.py upload PLAN FILM.mp4 --record youtube/SLUG.json --run RUN_ID
    python3 engine/youtube.py check                   # does the key work? posts nothing

The key is three GitHub secrets (YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET,
YOUTUBE_REFRESH_TOKEN), made once by Roshan: docs/YOUTUBE-SETUP.md. Without
them "upload" says so and stops without failing. Nothing here prints them.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BRAND = '#BittuKiRiya'
SHORTS = '#Shorts'
MAX_HASHTAGS = 6
MAX_TITLE = 100            # YouTube refuses longer titles
PHONE_TITLE = 60           # longer ones are cut off on phones
MAX_DESCRIPTION = 5000     # bytes
SHORT_SECONDS = 180        # YouTube counts an upright film up to 3 minutes as a Short
CATEGORIES = {'entertainment': '24', 'education': '27', 'comedy': '23', 'people': '22'}
CHUNK = 8 * 1024 * 1024    # a multiple of 256 KB, as resumable uploads require
KEY_NAMES = ('YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_REFRESH_TOKEN')
SETUP = 'docs/YOUTUBE-SETUP.md'


# --- the words --------------------------------------------------------------

def clean(text):
    """One line of plain text: no < or > (YouTube refuses them), single spaces."""
    return re.sub(r'\s+', ' ', str(text or '').replace('<', '').replace('>', '')).strip()


def cut(text, limit):
    """Text of at most `limit` characters, cut at a space when it is too long."""
    if len(text) <= limit:
        return text
    head = text[:limit - 1]
    if ' ' in head[limit // 2:]:
        head = head[:head.rindex(' ')]
    return head.rstrip(' .,!?-|:') + '…'


def hashtag(word):
    """'#Kya Hota Agar' -> '#KyaHotaAgar'; None when nothing usable is left.
    Letters, digits and _ stay, in any script, with their vowel signs (Hindi)."""
    body = ''.join(c for c in str(word or '').lstrip('#')
                   if c == '_' or unicodedata.category(c)[0] in 'LNM')
    return '#' + body if body and not body.isdigit() else None


def hashtags(given, short):
    """The film's hashtags in order, and notes on anything that was changed."""
    notes = []
    if isinstance(given, str):
        given = given.split(',') if ',' in given else given.split()
    if not isinstance(given, list):
        given = []
    seen, picked = {BRAND.lower(), SHORTS.lower()}, []
    for raw in given:
        tag = hashtag(raw)
        if tag is None:
            notes.append(f'hashtag "{raw}" has no letters, so it was left out')
            continue
        if tag != '#' + str(raw).strip().lstrip('#'):
            notes.append(f'hashtag "{raw}" became {tag} (no spaces or signs inside a hashtag)')
        if tag.lower() == SHORTS.lower() and not short:
            notes.append('#Shorts left out: this is not an upright film of 3 minutes or less')
        if tag.lower() in seen:
            continue
        seen.add(tag.lower())
        picked.append(tag)
    fixed = [BRAND] + ([SHORTS] if short else [])
    room = MAX_HASHTAGS - len(fixed)
    if len(picked) > room:
        notes.append(f'{len(picked) + len(fixed)} hashtags: only the first {MAX_HASHTAGS} are kept; '
                     'a few that fit the film reach more people than many')
        picked = picked[:room]
    tags = [BRAND] + picked[:1] + ([SHORTS] if short else []) + picked[1:]
    if len(tags) < 3:
        notes.append(f'only {len(tags)} hashtags: 3 to {MAX_HASHTAGS} reach more people')
    return tags, notes


def film_shape(film, plan):
    """(short, seconds): is the film a Short, and how long it is."""
    seconds, upright = None, None
    try:
        out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                              '-show_entries', 'stream=width,height:format=duration', '-of', 'json', str(film)],
                             capture_output=True, text=True, timeout=60, check=True).stdout
        info = json.loads(out)
        stream = (info.get('streams') or [{}])[0]
        upright = int(stream['height']) > int(stream['width'])
        seconds = float(info['format']['duration'])
    except Exception:
        pass
    if upright is None:
        upright = plan.get('layout') == 'short' or plan.get('frame') == '9:16'
    return bool(upright and (seconds is None or seconds <= SHORT_SECONDS)), seconds


def metadata(plan, short):
    """The video's snippet and status for YouTube, and notes on what was changed."""
    yt = plan.get('youtube') if isinstance(plan.get('youtube'), dict) else {}
    notes = []
    if not yt:
        notes.append('the plan has no "youtube" section: the plan\'s title and #BittuKiRiya are used')
    title = clean(yt.get('title') or plan.get('title'))
    if not title:
        title = 'Bittu Ki Riya'
    if len(title) > MAX_TITLE:
        notes.append(f'the title had {len(title)} characters; YouTube allows {MAX_TITLE}, so it was cut')
        title = cut(title, MAX_TITLE)
    elif len(title) > PHONE_TITLE:
        notes.append(f'the title has {len(title)} characters; phones show about {PHONE_TITLE}')
    tags, tag_notes = hashtags(yt.get('hashtags'), short)
    notes += tag_notes
    caption = clean(yt.get('caption') or plan.get('description') or plan.get('title'))
    question = clean(yt.get('question'))
    if question and not re.search(r'[\U0001F300-\U0001FAFF]\s*$', question):
        question += ' 👇'
    tail = '\n\n' + ' '.join(tags)
    room = MAX_DESCRIPTION - len(tail.encode()) - len(question.encode()) - 1
    while len(caption.encode()) > room:
        caption = cut(caption, len(caption) - 20)
    description = '\n'.join(x for x in (caption, question) if x) + tail
    words = ['Bittu Ki Riya', 'Bittu Riya'] + [t[1:] for t in tags if t not in (BRAND, SHORTS)]
    keywords, size = [], 0
    for w in words:
        size += len(w) + (2 if ' ' in w else 0) + 1
        if size > 450:
            break
        keywords.append(w)
    category = str(yt.get('category', 'entertainment')).lower()
    if category not in CATEGORIES:
        notes.append(f'category "{category}" is not one of {", ".join(CATEGORIES)}: entertainment is used')
        category = 'entertainment'
    language = 'hi' if plan.get('language') == 'hi' else 'en'
    privacy = os.environ.get('YOUTUBE_PRIVACY', 'public')
    if privacy not in ('public', 'unlisted', 'private'):
        privacy = 'public'
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': keywords,
            'categoryId': CATEGORIES[category],
            'defaultLanguage': language,
            'defaultAudioLanguage': language,
        },
        'status': {
            'privacyStatus': privacy,
            'selfDeclaredMadeForKids': False,
            'containsSyntheticMedia': False,
            'embeddable': True,
            'license': 'youtube',
        },
    }
    return body, notes


def describe(body, short, seconds):
    s = body['snippet']
    length = f'{seconds:.0f} s' if seconds else 'length unknown'
    return '\n'.join([
        f'Title:       {s["title"]}',
        f'Kind:        {"Short (upright, 3 minutes or less)" if short else "video"}, {length}',
        f'Visibility:  {body["status"]["privacyStatus"]}, not made for kids',
        'Description:',
        *('  ' + line for line in s['description'].split('\n')),
    ])


# --- talking to Google ------------------------------------------------------

class Refused(Exception):
    """YouTube or Google said no; the message says what to do about it."""


def endpoints():
    """Google's addresses, or a local test server (tests only, never elsewhere)."""
    test = os.environ.get('YOUTUBE_TEST_SERVER', '')
    if test:
        if not re.fullmatch(r'http://127\.0\.0\.1:\d+', test):
            raise Refused('YOUTUBE_TEST_SERVER may only point at this computer')
        return test + '/token', test + '/youtube/v3', test + '/upload/youtube/v3/videos'
    return ('https://oauth2.googleapis.com/token', 'https://www.googleapis.com/youtube/v3',
            'https://www.googleapis.com/upload/youtube/v3/videos')


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def call(method, url, data=None, headers=None, timeout=120):
    """(status, headers, body); a refusal is returned, not raised."""
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with _opener.open(req, timeout=timeout) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read() or b''


REASONS = {
    'invalid_grant': 'The YouTube key no longer works: it was withdrawn, or the Google project was left in '
                     '"Testing", where keys stop after 7 days. Check it says "In production" (' + SETUP + ', step 2), '
                     'then make a new refresh token (steps 4 and 5).',
    'invalid_client': 'YOUTUBE_CLIENT_ID or YOUTUBE_CLIENT_SECRET is wrong. Copy them again: ' + SETUP + ', step 3.',
    'unauthorized_client': 'This refresh token was made with a different client ID. Make it again with the '
                           'client ID in YOUTUBE_CLIENT_ID: ' + SETUP + ', step 4.',
    'insufficientPermissions': 'The key was made without both permissions. Make it again and tick '
                               'youtube.upload AND youtube.readonly: ' + SETUP + ', step 4.',
    'ACCESS_TOKEN_SCOPE_INSUFFICIENT': 'The key was made without both permissions. Make it again and tick '
                                       'youtube.upload AND youtube.readonly: ' + SETUP + ', step 4.',
    'quotaExceeded': 'Google\'s daily allowance for this project is used up. It resets at midnight '
                     'Pacific time; re-run this job tomorrow.',
    'uploadLimitExceeded': 'YouTube\'s upload limit for this channel is reached for today. Re-run this job '
                           'in 24 hours.',
    'youtubeSignupRequired': 'The key belongs to a Google account with no YouTube channel. Make it again '
                             'signed in as the Bittu Ki Riya channel: ' + SETUP + ', step 4.',
    'accessNotConfigured': 'The YouTube Data API is not switched on in the Google project: ' + SETUP + ', step 1.',
    'SERVICE_DISABLED': 'The YouTube Data API is not switched on in the Google project: ' + SETUP + ', step 1.',
}


def explain(what, status, body):
    """A plain sentence for a refusal. Google's own message never holds the key."""
    try:
        obj = json.loads(body or b'{}')
    except ValueError:
        obj = {}
    err = obj.get('error')
    reasons, message = [], ''
    if isinstance(err, str):                      # the token address answers like this
        reasons, message = [err], obj.get('error_description', '')
    elif isinstance(err, dict):
        message = err.get('message', '')
        reasons = [e.get('reason', '') for e in err.get('errors') or []]
        reasons += [d.get('reason', '') for d in err.get('details') or [] if isinstance(d, dict)]
        reasons.append(err.get('status', ''))
    for r in reasons:
        if r in REASONS:
            return f'{what}: {REASONS[r]}'
    detail = ', '.join(r for r in reasons if r) or 'no reason given'
    return f'{what} was refused (HTTP {status}, {detail}). Google says: {clean(message)[:300] or "nothing"}'


def access_token(token_url):
    data = urllib.parse.urlencode({
        'client_id': os.environ['YOUTUBE_CLIENT_ID'].strip(),
        'client_secret': os.environ['YOUTUBE_CLIENT_SECRET'].strip(),
        'refresh_token': os.environ['YOUTUBE_REFRESH_TOKEN'].strip(),
        'grant_type': 'refresh_token',
    }).encode()
    status, _, body = call('POST', token_url, data, {'Content-Type': 'application/x-www-form-urlencoded'})
    if status != 200:
        raise Refused(explain('Signing in to YouTube', status, body))
    token = json.loads(body).get('access_token')
    if not token:
        raise Refused('Signing in to YouTube gave no access token')
    if os.environ.get('GITHUB_ACTIONS'):
        print('::add-mask::' + token)
    return token


def check_channel(api, token, expected):
    """Refuse a key that belongs to any channel but Bittu Ki Riya."""
    status, _, body = call('GET', api + '/channels?part=id,snippet&mine=true',
                           headers={'Authorization': 'Bearer ' + token})
    if status != 200:
        raise Refused(explain('Checking which channel the key belongs to', status, body))
    items = json.loads(body).get('items') or []
    if not items:
        raise Refused(REASONS['youtubeSignupRequired'])
    got = items[0].get('id', '')
    name = (items[0].get('snippet') or {}).get('title', '?')
    if got != expected:
        raise Refused(f'The key belongs to the channel "{name}" ({got}), not Bittu Ki Riya ({expected}). '
                      f'Nothing was posted. Make the key again and pick the Bittu Ki Riya channel when Google '
                      f'asks which account to use: {SETUP}, step 4.')
    return name


def upload(upload_url, token, body, film, size):
    """Send the film by YouTube's resumable upload; returns the new video."""
    query = urllib.parse.urlencode({'uploadType': 'resumable', 'part': 'snippet,status',
                                    'notifySubscribers': 'true'})
    status, headers, answer = call('POST', f'{upload_url}?{query}', json.dumps(body).encode(), {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Upload-Content-Length': str(size),
        'X-Upload-Content-Type': 'video/mp4',
    })
    session = headers.get('location', '')
    if status != 200 or not session.startswith(upload_url):
        raise Refused(explain('Starting the upload', status, answer))
    if os.environ.get('GITHUB_ACTIONS'):
        print('::add-mask::' + session)

    def sent_so_far(h):
        m = re.fullmatch(r'bytes=0-(\d+)', h.get('range', ''))
        return int(m.group(1)) + 1 if m else 0

    def ask_where():
        return call('PUT', session, b'', {'Authorization': 'Bearer ' + token,
                                          'Content-Range': f'bytes */{size}'})

    offset, trouble = 0, 0
    with open(film, 'rb') as f:
        while True:
            f.seek(offset)
            chunk = f.read(CHUNK)
            end = offset + len(chunk)
            try:
                status, headers, answer = call('PUT', session, chunk, {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'video/mp4',
                    'Content-Range': f'bytes {offset}-{end - 1}/{size}',
                }, timeout=300)
            except (OSError, urllib.error.URLError):
                status, headers, answer = None, {}, b''
            if status in (200, 201):
                return json.loads(answer)
            if status == 308:
                offset, trouble = sent_so_far(headers), 0
                continue
            if status is not None and status < 500 and status != 429:
                raise Refused(explain('Sending the film', status, answer))
            trouble += 1
            if trouble > 6:
                raise Refused(f'Sending the film kept failing (last answer: {status}). Re-run this job; '
                              'YouTube keeps nothing half-sent.')
            time.sleep(min(60, 2 ** trouble))
            try:
                status, headers, answer = ask_where()
            except (OSError, urllib.error.URLError):
                continue
            if status in (200, 201):
                return json.loads(answer)
            if status == 308:
                offset = sent_so_far(headers)


def check_key():
    """Sign in and name the key's channel, posting nothing. Returns the channel's name."""
    missing = [k for k in KEY_NAMES if not os.environ.get(k, '').strip()]
    if missing:
        raise Refused(f'{", ".join(missing)} missing: add them as repository secrets ({SETUP}, step 5)')
    expected = os.environ.get('YOUTUBE_CHANNEL_ID', '').strip()
    if not expected:
        raise Refused('YOUTUBE_CHANNEL_ID is not set, so the channel cannot be checked')
    token_url, api, _ = endpoints()
    return check_channel(api, access_token(token_url), expected)


def post(plan, film, record=None, run=''):
    """Upload the film; returns the record of where it went (or None if skipped)."""
    missing = [k for k in KEY_NAMES if not os.environ.get(k, '').strip()]
    if missing:
        print(f'YouTube is not set up yet ({", ".join(missing)} missing), so the film was not posted. '
              f'Set it up once: {SETUP}')
        return None
    expected = os.environ.get('YOUTUBE_CHANNEL_ID', '').strip()
    if not expected:
        raise Refused('YOUTUBE_CHANNEL_ID is not set, so the channel cannot be checked; nothing was posted')
    if record and run:
        try:
            old = json.loads(pathlib.Path(record).read_text())
        except (OSError, ValueError):
            old = {}
        if str(old.get('run')) == str(run) and old.get('url'):
            print(f'Already posted from this run: {old["url"]}')
            return old
    short, seconds = film_shape(film, plan)
    body, notes = metadata(plan, short)
    token_url, api, upload_url = endpoints()
    token = access_token(token_url)
    channel = check_channel(api, token, expected)
    size = pathlib.Path(film).stat().st_size
    video = upload(upload_url, token, body, film, size)
    vid = video.get('id')
    if not vid:
        raise Refused('YouTube took the film but gave no video id; look in YouTube Studio before re-running')
    url = f'https://youtube.com/shorts/{vid}' if short else f'https://youtu.be/{vid}'
    out = {
        'slug': pathlib.Path(record).stem if record else pathlib.Path(film).stem,
        'video_id': vid,
        'url': url,
        'studio': f'https://studio.youtube.com/video/{vid}/edit',
        'title': body['snippet']['title'],
        'privacy': (video.get('status') or {}).get('privacyStatus', body['status']['privacyStatus']),
        'short': short,
        'channel': channel,
        'run': str(run),
        'at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'notes': notes,
    }
    if record:
        pathlib.Path(record).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(record).write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return out


def summary(text):
    path = os.environ.get('GITHUB_STEP_SUMMARY')
    if path:
        with open(path, 'a', encoding='utf-8') as f:
            f.write(text + '\n')


def main(argv):
    if argv[:1] == ['check']:
        try:
            name = check_key()
        except (Refused, OSError, urllib.error.URLError) as e:
            why = str(e) if isinstance(e, Refused) else f'Google could not be reached ({type(e).__name__}). Try again.'
            print('KEY NOT WORKING: ' + why)
            summary('## YouTube key: NOT working\n\n' + why + '\n')
            return 1
        print(f'The YouTube key works and belongs to "{name}". Films will be posted there.')
        summary(f'## YouTube key works\n\nIt belongs to "{name}". Films will be posted there.\n')
        return 0
    if len(argv) < 3 or argv[0] not in ('text', 'upload'):
        print(__doc__)
        return 2
    mode, plan_path, film = argv[0], pathlib.Path(argv[1]), pathlib.Path(argv[2])
    record = argv[argv.index('--record') + 1] if '--record' in argv else None
    run = argv[argv.index('--run') + 1] if '--run' in argv else ''
    plan = json.loads(plan_path.read_text(encoding='utf-8-sig'))
    if mode == 'text':
        short, seconds = film_shape(film, plan)
        body, notes = metadata(plan, short)
        text = describe(body, short, seconds)
        print(text)
        for n in notes:
            print('note   ' + n)
        summary('## On YouTube\n\n```\n' + text + '\n```\n' + ''.join(f'- {n}\n' for n in notes))
        return 0
    try:
        out = post(plan, film, record, run)
    except (Refused, OSError, urllib.error.URLError) as e:
        why = str(e) if isinstance(e, Refused) else ('YouTube could not be reached '
                                                      f'({type(e).__name__}). Re-run this job.')
        print('NOT POSTED: ' + why)
        summary('## YouTube: NOT POSTED\n\n' + why + '\n')
        return 1
    if out is None:
        summary(f'## YouTube: not set up yet\n\nThe film was not posted. Set it up once: `{SETUP}`.\n')
        return 0
    print(f'Posted on YouTube ({out["privacy"]}): {out["url"]}')
    summary(f'## On YouTube ({out["privacy"]})\n\n{out["url"]}\n\nEdit or delete: {out["studio"]}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
