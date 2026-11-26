"""Upright films go to Instagram as Reels, by Instagram's rules, to the right account.

    python3 tests/test_instagram.py

- Instagram's copy: same picture, sound at 128 kbps, no MP4 edit lists,
  index first (the Reels rules). A wide film, or no key, is not posted.
- The caption: the plan's caption and question, then the hashtags with
  #BittuKiRiya first and no #Shorts.
- Against a pretend Instagram on this computer: sign in, check the account
  BEFORE anything is sent, start the Reel from the public link, wait while
  Instagram processes it, publish, record the link. If Instagram cannot
  fetch GitHub's link, the link it redirects to is tried. A key for another
  account posts nothing; a dead key says what to do; the weekly renewal
  writes the key out only when Instagram gives a new one.
- A Facebook-kind key (Unified login, starts "EA") goes to the Facebook
  host, finds the account by INSTAGRAM_USER_ID (not "me"), posts the same
  way, never needs renewing when it never expires, and fails the weekly
  job 14 days before one that does expires.
- The key never appears in anything printed.
"""
import contextlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
import instagram  # noqa: E402

bad = 0


def say(ok, msg):
    global bad
    bad += not ok
    print(('ok   ' if ok else 'FAIL ') + msg)


plan = {'title': 'Chaand', 'language': 'hi', 'layout': 'short',
        'youtube': {'title': 'Chaand Gayab Ho Gaya! 🌙', 'caption': 'Bittu ne Riya ko chaand gift kar diya 🌊',
                    'question': 'Aap Bittu ki jagah hote toh kya karte?', 'hashtags': ['#KyaHotaAgar', '#Moon', '#Shorts']},
        'shots': [{'say': 'एक', 'picture': '001'}]}
text = instagram.caption(plan)
say(text == 'Bittu ne Riya ko chaand gift kar diya 🌊\nAap Bittu ki jagah hote toh kya karte? 👇\n\n'
            '#BittuKiRiya #KyaHotaAgar #Moon', f'the caption, then the hashtags without #Shorts: {text!r}')
long = json.loads(json.dumps(plan))
long['youtube']['caption'] = 'lamba ' * 500
say(len(instagram.caption(long)) <= 2200 and instagram.caption(long).endswith('#Moon'),
    'a long caption is cut to 2,200 characters and keeps its hashtags')

work = pathlib.Path(tempfile.mkdtemp())
os.environ.pop('GITHUB_ACTIONS', None)
os.environ.pop('GITHUB_STEP_SUMMARY', None)
os.environ.pop('GITHUB_OUTPUT', None)
if shutil.which('ffmpeg'):
    for name, size in (('up', '1080x1920'), ('wide', '1920x1080')):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=c=red:s={size}:d=4:r=30',
                        '-f', 'lavfi', '-i', 'sine=f=330:d=4:sample_rate=48000', '-c:v', 'libx264', '-preset',
                        'veryfast', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                        '-movflags', '+faststart', str(work / f'{name}.mp4')], check=True)
    say(b'elst' in (work / 'up.mp4').read_bytes(), 'a film as ffmpeg makes it has an edit list (Instagram refuses those)')
    instagram.prepare(work / 'up.mp4', work / 'insta.mp4')
    data = (work / 'insta.mp4').read_bytes()
    rate = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=bit_rate',
                           '-of', 'csv=p=0', str(work / 'insta.mp4')], capture_output=True, text=True).stdout.strip()
    say(b'elst' not in data and data.find(b'moov') < data.find(b'mdat') and int(rate) <= 130000,
        f'Instagram\'s copy: no edit list, index first, sound at {int(rate) // 1000} kbps')
    os.environ['INSTAGRAM_TOKEN'] = 'IG-secret-token'
    say(instagram.should(work / 'up.mp4')[0] and not instagram.should(work / 'wide.mp4')[0],
        'an upright film goes to Instagram; a wide one does not')
    os.environ.pop('INSTAGRAM_TOKEN')
    say('not set up' in instagram.should(work / 'up.mp4')[1], 'with no key, nothing goes to Instagram')
    film = work / 'insta.mp4'
else:
    print('skip the film checks: no ffmpeg here')
    film = work / 'insta.mp4'
    film.write_bytes(b'x' * 1000)


class Fake:
    username = 'bittukiriya'
    token = 'IG-secret-token'
    fetchable = set()            # links the pretend Instagram can fetch
    order = []
    polls = 0
    published = None


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

    def args(self):
        u = urllib.parse.urlparse(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        n = int(self.headers.get('Content-Length') or 0)
        if n:
            q.update(urllib.parse.parse_qsl(self.rfile.read(n).decode()))
        return u.path, q

    def do_HEAD(self):
        if self.path == '/download/film.mp4':
            return self.reply(302, None, {'Location': f'http://127.0.0.1:{port}/store/film.mp4?sig=abc'})
        self.reply(404)

    def do_GET(self):
        path, q = self.args()
        if path == '/refresh_access_token':
            Fake.order.append('refresh')
            if q.get('access_token') != Fake.token:
                return self.reply(400, {'error': {'code': 190, 'message': 'Invalid OAuth access token.'}})
            return self.reply(200, {'access_token': Fake.new_token, 'token_type': 'bearer', 'expires_in': 5183944})
        if q.get('access_token') != Fake.token:
            return self.reply(400, {'error': {'code': 190, 'message': 'Error validating access token.'}})
        if path == '/v26.0/me':
            Fake.order.append('me')
            if Fake.token.startswith('EA'):     # a Facebook-kind key's "me" is a system user
                return self.reply(200, {'id': '999', 'name': 'uploader system user'})
            return self.reply(200, {'user_id': '1784', 'username': Fake.username})
        if path == '/v26.0/1784' and q.get('fields') == 'id,username':
            Fake.order.append('me')
            return self.reply(200, {'id': '1784', 'username': Fake.username})
        if path == '/v26.0/debug_token' and q.get('input_token') == Fake.token:
            return self.reply(200, {'data': {'is_valid': True, 'expires_at': Fake.expires,
                                             'data_access_expires_at': 0}})
        if path == '/v26.0/C1':
            Fake.polls += 1
            Fake.order.append('poll')
            ok = Fake.url in Fake.fetchable
            code = 'IN_PROGRESS' if Fake.polls == 1 else ('FINISHED' if ok else 'ERROR')
            return self.reply(200, {'status_code': code, 'status': 'Error: media download failed' if code == 'ERROR' else code})
        if path == '/v26.0/M9':
            return self.reply(200, {'permalink': 'https://www.instagram.com/reel/ABC123/'})
        self.reply(404, {'error': {'code': 100, 'message': 'no'}})

    def do_POST(self):
        path, q = self.args()
        if q.get('access_token') != Fake.token:
            return self.reply(400, {'error': {'code': 190, 'message': 'Error validating access token.'}})
        if path == '/v26.0/1784/media':
            Fake.order.append('start')
            Fake.url, Fake.polls, Fake.sent = q.get('video_url'), 0, q
            return self.reply(200, {'id': 'C1'})
        if path == '/v26.0/1784/media_publish' and q.get('creation_id') == 'C1':
            Fake.order.append('publish')
            Fake.published = q
            return self.reply(200, {'id': 'M9'})
        self.reply(404, {'error': {'code': 100, 'message': 'no'}})


server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
port = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()
os.environ.update(INSTAGRAM_TEST_SERVER=f'http://127.0.0.1:{port}', INSTAGRAM_TOKEN=Fake.token,
                  INSTAGRAM_ACCOUNT='@BittuKiRiya')
public = f'http://127.0.0.1:{port}/download/film.mp4'
stored = f'http://127.0.0.1:{port}/store/film.mp4?sig=abc'
record = work / 'instagram' / 'chaand.json'
(work / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False), encoding='utf-8')
instagram.WAIT_SECONDS = 0
instagram.time.sleep = lambda s: None


def run(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = instagram.main(list(args))
    said = out.getvalue()
    say(Fake.token not in said and 'IG-new-token' not in said and 'EA-secret-token' not in said,
        'nothing printed holds the key')
    return code, said


Fake.fetchable = {public}
code, said = run('post', str(work / 'plan.json'), str(film), '--url', public, '--record', str(record), '--run', '7')
rec = json.loads(record.read_text()) if record.exists() else {}
say(code == 0 and Fake.order[:2] == ['me', 'start'] and 'publish' in Fake.order,
    f'sign in and check the account first, then start, wait, publish: {Fake.order}')
say(Fake.sent.get('media_type') == 'REELS' and Fake.sent.get('share_to_feed') == 'true'
    and Fake.sent.get('caption') == text and Fake.sent.get('video_url') == public,
    'a Reel, shown in the feed too, with the caption, from the public link')
say(Fake.order.index('publish') > Fake.order.index('poll') and Fake.polls == 2,
    'it waits until Instagram has processed the film before publishing')
say(rec.get('url') == 'https://www.instagram.com/reel/ABC123/' and rec.get('run') == '7', f'the link is recorded: {rec.get("url")}')
say(instagram.should(film, record, '7') == (False, 'already posted from this run: https://www.instagram.com/reel/ABC123/')
    or not shutil.which('ffprobe'), 'a re-run of the same run never posts twice')

Fake.order, Fake.fetchable = [], {stored}
record.unlink()
code, said = run('post', str(work / 'plan.json'), str(film), '--url', public, '--record', str(record), '--run', '8')
say(code == 0 and Fake.order.count('start') == 2 and Fake.url == stored,
    'when Instagram cannot fetch GitHub\'s link, the address it redirects to is tried, and works')

Fake.username, Fake.order = 'someone_else', []
code, said = run('post', str(work / 'plan.json'), str(film), '--url', public, '--record', str(record), '--run', '9')
say(code == 1 and 'start' not in Fake.order and '@someone_else' in said, 'a key for another account posts nothing, and says so')
Fake.username = 'bittukiriya'

os.environ['INSTAGRAM_TOKEN'] = 'IG-dead-token'
code, said = run('check')
say(code == 1 and 'no longer works' in said and 'INSTAGRAM-SETUP' in said and 'IG-dead-token' not in said,
    'a dead key says how to make a new one')
os.environ['INSTAGRAM_TOKEN'] = Fake.token
code, said = run('check')
say(code == 0 and '@bittukiriya' in said, 'the key check names the account and posts nothing')

out_file = work / 'new-token'
Fake.new_token = Fake.token
code, said = run('refresh', '--out', str(out_file))
say(code == 0 and not out_file.exists() and 'more days' in said, 'renewing gives the same key: nothing to save')
Fake.new_token = 'IG-new-token'
code, said = run('refresh', '--out', str(out_file))
say(code == 0 and out_file.read_text() == 'IG-new-token' and oct(out_file.stat().st_mode & 0o777) == '0o600',
    'renewing gives a new key: written to a private file for the workflow to save')

# --- the Facebook-kind key (Unified login) -----------------------------------
import time  # noqa: E402
Fake.token, Fake.expires, Fake.order = 'EA-secret-token', 0, []
os.environ['INSTAGRAM_TOKEN'] = Fake.token
os.environ.pop('INSTAGRAM_USER_ID', None)
code, said = run('post', str(work / 'plan.json'), str(film), '--url', public, '--record', str(record), '--run', '10')
say(code == 1 and 'start' not in Fake.order and 'INSTAGRAM_USER_ID' in said,
    'a Facebook-kind key with no account number posts nothing, and says what is missing')
os.environ['INSTAGRAM_USER_ID'] = '1784'
Fake.order, Fake.fetchable = [], {public}
record.unlink(missing_ok=True)
code, said = run('post', str(work / 'plan.json'), str(film), '--url', public, '--record', str(record), '--run', '11')
say(code == 0 and Fake.order[:2] == ['me', 'start'] and Fake.published and Fake.sent.get('media_type') == 'REELS',
    f'a Facebook-kind key finds the account by its number, checks it, then posts the Reel: {Fake.order}')
code, said = run('check')
say(code == 0 and '@bittukiriya' in said and 'never expires' in said, 'its key check says it never expires')
out_file.unlink(missing_ok=True)
code, said = run('refresh', '--out', str(out_file))
say(code == 0 and not out_file.exists() and 'nothing to renew' in said,
    'the weekly job renews nothing for a key that never expires, and needs no GitHub key to save one')
Fake.expires = int(time.time()) + 5 * 86400 + 3600
code, said = run('refresh', '--out', str(out_file))
say(code == 1 and 'runs out in 5 days' in said and 'INSTAGRAM-SETUP' in said and not out_file.exists(),
    'one that expires fails the weekly job 14 days ahead, saying how to make a new one')
Fake.expires = 0
os.environ['INSTAGRAM_TOKEN'] = 'EA-dead-token'
code, said = run('check')
say(code == 1 and 'no longer works' in said and 'EA-dead-token' not in said, 'a dead Facebook-kind key says how to make a new one')
server.shutdown()

test_server = os.environ.pop('INSTAGRAM_TEST_SERVER')
os.environ['INSTAGRAM_TOKEN'] = 'EA-x'
fb = instagram.api()
os.environ['INSTAGRAM_TOKEN'] = 'IG-x'
say(fb == 'https://graph.facebook.com' and instagram.api() == 'https://graph.instagram.com',
    'a Facebook-kind key goes to graph.facebook.com, an Instagram-kind one to graph.instagram.com')

guide = (ROOT / 'docs' / 'INSTAGRAM-SETUP.md').read_text()
import re  # noqa: E402
steps = re.findall(r'^## (\d)\. ', guide, re.M)
said_steps = set(re.findall(r'steps? (\d)', pathlib.Path(instagram.__file__).read_text()))
say(steps == ['1', '2', '3', '4', '5', '6'] and said_steps <= set(steps), f'the messages point at real setup steps: {sorted(said_steps)}')
say(all(k in guide for k in ('INSTAGRAM_TOKEN', 'INSTAGRAM_ACCOUNT', 'GH_SECRETS_TOKEN', 'instagram-check.yml',
                              'instagram_content_publish', 'Unified login', 'INSTAGRAM_USER_ID')),
    'the guide names the secrets, the permission, the Unified-login route and the key check')

print('\nall good' if not bad else f'\n{bad} failing')
sys.exit(1 if bad else 0)
