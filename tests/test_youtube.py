"""The YouTube step posts what the plan says, by the rules, to the right channel.

    python3 tests/test_youtube.py

- The words: title within YouTube's 100 characters, a short description with
  the hashtags on its last line, #BittuKiRiya first, #Shorts only on an
  upright film of 3 minutes or less, at most 6 hashtags, no spaces inside
  one, not made for kids, no synthetic-content label.
- The upload, against a pretend YouTube on this computer: the key is turned
  into a sign-in, the channel is checked BEFORE the film is sent, the film
  goes in pieces and survives a dropped piece, and the link is recorded.
- A key for another channel posts nothing. A withdrawn key says what to do.
  No key at all: the step says so and passes. A re-run never posts twice.
- The key never appears in anything printed.
"""
import contextlib
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
import youtube  # noqa: E402

bad = 0


def say(ok, msg):
    global bad
    bad += not ok
    print(('ok   ' if ok else 'FAIL ') + msg)


CHANNEL = 'UCBJBFuwimmZdoB5DXbRT7kg'
plan = {'title': 'Bittu Bana Caveman Ka Guru', 'language': 'hi', 'layout': 'short', 'cast': 'Bittu & Riya',
        'youtube': {'title': 'Chaand Gayab Ho Gaya! 🌙 Kya Hota Agar...?',
                    'caption': 'Bittu ne Riya ko chaand gift kar diya... aur duniya ulti ho gayi 🌊',
                    'question': 'Aap Bittu ki jagah hote toh kya karte?',
                    'hashtags': ['#KyaHotaAgar', '#Moon', '#Science']},
        'shots': [{'say': 'एक दो तीन', 'picture': '001'}]}

# --- the words ----------------------------------------------------------------
body, notes = youtube.metadata(plan, short=True)
s, st = body['snippet'], body['status']
last = s['description'].split('\n')[-1]
say(s['title'] == plan['youtube']['title'] and not notes, 'a good "youtube" section is used as written, with no notes')
say(last == '#BittuKiRiya #KyaHotaAgar #Shorts #Moon #Science', f'hashtags on the last line, brand first: {last}')
say(s['description'].startswith(plan['youtube']['caption'] + '\nAap Bittu ki jagah hote toh kya karte? 👇\n\n'),
    'the description is the caption, then the question, then the hashtags')
say(st == {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False, 'containsSyntheticMedia': False,
           'embeddable': True, 'license': 'youtube'}, 'public, not made for kids, no synthetic-content label')
say(s['defaultLanguage'] == 'hi' and s['defaultAudioLanguage'] == 'hi' and s['categoryId'] == '24',
    'a Hindi film is marked Hindi, in Entertainment')
wide, _ = youtube.metadata(plan, short=False)
say('#Shorts' not in wide['snippet']['description'], 'a wide film never carries #Shorts')

messy = json.loads(json.dumps(plan))
messy['youtube'].update(title='Kya <Hota> Agar ' + 'bahut lamba title ' * 10,
                        hashtags='#Kya Hota Agar, #moon, #Moon, #Shorts, #a, #b, #c, #d, #e, #!!')
body, notes = youtube.metadata(messy, short=False)
tags = body['snippet']['description'].split('\n')[-1].split()
say(len(body['snippet']['title']) <= 100 and '<' not in body['snippet']['title'] and body['snippet']['title'].endswith('…'),
    'a long title with < > is cleaned and cut to 100 characters')
say(len(tags) == 6 and tags[0] == '#BittuKiRiya' and '#Shorts' not in tags and len({t.lower() for t in tags}) == 6,
    f'at most 6 hashtags, no repeats, no #Shorts on a wide film: {" ".join(tags)}')
say(any('100' in n for n in notes) and any('#Shorts left out' in n for n in notes) and any('first 6' in n for n in notes),
    'every change is reported as a note')
say(youtube.hashtag('#Kya Hota Agar') == '#KyaHotaAgar' and youtube.hashtag('#!!') is None
    and youtube.hashtag('#भारत') == '#भारत', 'a hashtag has no spaces or signs; Hindi letters are kept')
bare, notes = youtube.metadata({'title': 'Plain Plan', 'shots': []}, short=True)
say(bare['snippet']['title'] == 'Plain Plan' and bare['snippet']['description'].endswith('#BittuKiRiya #Shorts')
    and any('no "youtube" section' in n for n in notes), 'a plan with no "youtube" section still posts, by its title')

if shutil.which('ffmpeg') and shutil.which('ffprobe'):
    tmp = pathlib.Path(tempfile.mkdtemp())
    for name, size, secs in (('up', '360x640', 2), ('wide', '640x360', 2)):
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color=c=red:s={size}:d={secs}',
                        str(tmp / f'{name}.mp4')], check=True)
    say(youtube.film_shape(tmp / 'up.mp4', {})[0] and not youtube.film_shape(tmp / 'wide.mp4', {'layout': 'short'})[0],
        'the film itself decides: upright is a Short, wide is not, whatever the plan says')
else:
    print('skip the film-shape check: no ffmpeg here')


# --- a pretend YouTube on this computer --------------------------------------
class Fake:
    channel = CHANNEL
    refresh = 'RT-secret-refresh'
    sent = bytearray()
    meta = None
    order = []
    drop_once = True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, code, obj=None, headers=None):
        data = json.dumps(obj).encode() if obj is not None else b''
        self.send_response(code)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        return self.rfile.read(int(self.headers.get('Content-Length') or 0))

    def authorised(self):
        return self.headers.get('Authorization') == 'Bearer AT-access'

    def do_POST(self):
        data = self.body()
        if self.path == '/token':
            form = dict(urllib.parse.parse_qsl(data.decode()))
            Fake.order.append('token')
            if form.get('client_secret') != 'CS-secret' or form.get('client_id') != 'CID':
                return self.reply(401, {'error': 'invalid_client'})
            if form.get('refresh_token') != Fake.refresh:
                return self.reply(400, {'error': 'invalid_grant', 'error_description': 'Token has been expired or revoked.'})
            return self.reply(200, {'access_token': 'AT-access', 'expires_in': 3599})
        if self.path.startswith('/upload/youtube/v3/videos?') and self.authorised():
            Fake.order.append('start')
            Fake.meta = json.loads(data)
            Fake.size = int(self.headers['X-Upload-Content-Length'])
            return self.reply(200, None, {'Location': f'http://127.0.0.1:{port}/upload/youtube/v3/videos?upload_id=U1'})
        self.reply(404, {'error': {'message': 'no'}})

    def do_GET(self):
        if self.path.startswith('/youtube/v3/channels') and self.authorised():
            Fake.order.append('channel')
            return self.reply(200, {'items': [{'id': Fake.channel, 'snippet': {'title': 'Somebody'}}]})
        self.reply(404, {'error': {'message': 'no'}})

    def do_PUT(self):
        data = self.body()
        rng = self.headers.get('Content-Range', '')
        if rng.startswith('bytes */'):
            Fake.order.append('where')
        else:
            first = int(rng.split()[1].split('-')[0])
            if Fake.drop_once and first > 0:
                Fake.drop_once = False
                Fake.order.append('dropped')
                return self.reply(503, {'error': {'message': 'busy'}})
            if first != len(Fake.sent):
                return self.reply(400, {'error': {'message': 'out of order'}})
            Fake.sent += data
            Fake.order.append('piece')
        if len(Fake.sent) == Fake.size:
            return self.reply(200, {'id': 'VID123', 'status': {'privacyStatus': 'public'}})
        return self.reply(308, None, {'Range': f'bytes=0-{len(Fake.sent) - 1}'} if Fake.sent else {})


server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
port = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()

youtube.CHUNK = 256 * 1024
youtube.time.sleep = lambda s: None
work = pathlib.Path(tempfile.mkdtemp())
film = work / 'chaand.mp4'
film.write_bytes(os.urandom(700 * 1024))
(work / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False), encoding='utf-8')
record = work / 'youtube' / 'chaand.json'
os.environ.update(YOUTUBE_TEST_SERVER=f'http://127.0.0.1:{port}', YOUTUBE_CLIENT_ID='CID',
                  YOUTUBE_CLIENT_SECRET='CS-secret', YOUTUBE_REFRESH_TOKEN=Fake.refresh,
                  YOUTUBE_CHANNEL_ID=CHANNEL, YOUTUBE_PRIVACY='public')
os.environ.pop('GITHUB_STEP_SUMMARY', None)
os.environ.pop('GITHUB_ACTIONS', None)


def run(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = youtube.main(['upload', str(work / 'plan.json'), str(film), '--record', str(record), *args])
    text = out.getvalue()
    say(not any(x in text for x in ('CS-secret', Fake.refresh, 'AT-access')), 'nothing printed holds the key')
    return code, text


code, text = run('--run', '111')
rec = json.loads(record.read_text()) if record.exists() else {}
say(code == 0 and bytes(Fake.sent) == film.read_bytes(), 'the whole film arrives, byte for byte, in pieces')
say(Fake.order[:3] == ['token', 'channel', 'start'], f'sign in, check the channel, then start: {Fake.order[:3]}')
say('dropped' in Fake.order and Fake.order[Fake.order.index('dropped') + 1] == 'where',
    'a dropped piece is followed by asking YouTube how much arrived, then carrying on')
say(Fake.meta['snippet']['title'] == plan['youtube']['title'] and Fake.meta['status']['privacyStatus'] == 'public',
    'YouTube gets the plan\'s title, public')
say(rec.get('url') == 'https://youtube.com/shorts/VID123' and rec.get('run') == '111' and 'Posted on YouTube' in text,
    f'the link is recorded: {rec.get("url")}')

out = io.StringIO()
with contextlib.redirect_stdout(out):
    code = youtube.main(['check'])
say(code == 0 and 'belongs to "Somebody"' in out.getvalue() and 'start' not in Fake.order[-2:],
    'the key check signs in and names the channel, posting nothing')
before = list(Fake.order)
code, text = run('--run', '111')
say(code == 0 and Fake.order == before and 'Already posted from this run' in text, 'a re-run of the same run never posts twice')

Fake.channel = 'UCsomebodyElse0000000000'
Fake.order, Fake.sent = [], bytearray()
code, text = run('--run', '222')
say(code == 1 and 'start' not in Fake.order and 'not Bittu Ki Riya' in text,
    'a key for another channel posts nothing, and says so')
Fake.channel = CHANNEL

os.environ['YOUTUBE_REFRESH_TOKEN'] = 'RT-old-withdrawn'
code, text = run('--run', '333')
say(code == 1 and 'no longer works' in text and 'YOUTUBE-SETUP' in text and 'RT-old-withdrawn' not in text,
    'a withdrawn key says how to make a new one')

for k in youtube.KEY_NAMES:
    os.environ.pop(k)
code, text = run('--run', '444')
say(code == 0 and 'not set up yet' in text, 'with no key yet the step says so and passes (the film is still in Drive)')

os.environ['YOUTUBE_TEST_SERVER'] = 'http://example.com:80'
try:
    youtube.endpoints()
    say(False, 'the test address can only point at this computer')
except youtube.Refused:
    say(True, 'the test address can only point at this computer')
server.shutdown()

# --- the setup guide matches the code ----------------------------------------
guide = (ROOT / 'docs' / 'YOUTUBE-SETUP.md').read_text()
steps = re.findall(r'^## (\d)\. ', guide, re.M)
said = set(re.findall(r'steps? (\d)', pathlib.Path(youtube.__file__).read_text()))
say(steps == ['1', '2', '3', '4', '5', '6'] and said <= set(steps), f'the messages point at real setup steps: {sorted(said)}')
say(all(k in guide for k in youtube.KEY_NAMES) and 'auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly' in guide
    and 'In production' in guide and 'youtube-check.yml' in guide,
    'the guide names the three secrets, both permissions, "In production" and the key check')

print('\nall good' if not bad else f'\n{bad} failing')
sys.exit(1 if bad else 0)
