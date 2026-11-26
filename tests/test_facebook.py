"""Upright films go to the Bittu Ki Riya Facebook Page, and only there.

    python3 tests/test_facebook.py

Against a pretend Facebook on this computer:
- the Page's own key is asked for with the system-user key, for
  FACEBOOK_PAGE_ID only, BEFORE anything is sent; a key that cannot reach
  that Page posts nothing and says what to do; a dead key says so too;
- a film of up to 90 s becomes a Reel: start, send the bytes (no public
  link), publish with the caption and title, wait until Facebook has
  published it, record the link;
- a longer film becomes an ordinary Page video, in one upload;
- a wide film, or no key, is not posted; a re-run never posts twice;
- no key ever appears in anything printed.
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
import facebook  # noqa: E402
import instagram  # noqa: E402

bad = 0


def say(ok, msg):
    global bad
    bad += not ok
    print(('ok   ' if ok else 'FAIL ') + msg)


for k in ('GITHUB_ACTIONS', 'GITHUB_STEP_SUMMARY', 'GITHUB_OUTPUT'):
    os.environ.pop(k, None)

plan = {'title': 'Chaand', 'language': 'hi', 'layout': 'short',
        'youtube': {'title': 'Chaand Gayab Ho Gaya! 🌙', 'caption': 'Bittu ne Riya ko chaand gift kar diya 🌊',
                    'question': 'Aap Bittu ki jagah hote toh kya karte?', 'hashtags': ['#KyaHotaAgar', '#Moon', '#Shorts']},
        'shots': [{'say': 'एक', 'picture': '001'}]}
text = instagram.caption(plan)

work = pathlib.Path(tempfile.mkdtemp())
film = work / 'film.mp4'
if shutil.which('ffmpeg'):
    for name, size in (('film', '1080x1920'), ('wide', '1920x1080')):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=c=red:s={size}:d=4:r=30',
                        '-f', 'lavfi', '-i', 'sine=f=330:d=4:sample_rate=48000', '-c:v', 'libx264', '-preset',
                        'veryfast', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-ac', '2',
                        str(work / f'{name}.mp4')], check=True)
    os.environ['FACEBOOK_TOKEN'] = 'EA-system-key'
    say(facebook.should(film)[0] and not facebook.should(work / 'wide.mp4')[0],
        'an upright film goes to the Facebook Page; a wide one does not')
    os.environ.pop('FACEBOOK_TOKEN')
    say('not set up' in facebook.should(film)[1], 'with no key, nothing goes to Facebook')
    real_shape = instagram.shape
else:
    print('skip the film checks: no ffmpeg here')
    film.write_bytes(b'x' * 1000)
    real_shape = None
facebook.instagram.shape = lambda f: (1080, 1920, Fake.seconds)


class Fake:
    key = 'EA-system-key'
    page_key = 'EAP-page-key'
    page = '6159'
    reach = 'direct'             # how the system key reaches the Page: direct, accounts, none
    seconds = 79.0
    order = []
    polls = 0
    upload = {}
    finish = {}
    video_form = b''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, code, obj=None):
        data = json.dumps(obj).encode() if obj is not None else b''
        self.send_response(code)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def args(self):
        u = urllib.parse.urlparse(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        n = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(n) if n else b''
        if self.headers.get('Content-Type', '').startswith('application/x-www-form-urlencoded'):
            q.update(urllib.parse.parse_qsl(raw.decode()))
        return u.path, q, raw

    def dead(self):
        return self.reply(400, {'error': {'code': 190, 'message': 'Error validating access token.'}})

    def do_GET(self):
        path, q, _ = self.args()
        tok = q.get('access_token')
        if path == f'/v26.0/{Fake.page}' and q.get('fields') == 'id,name,access_token':
            if tok != Fake.key:
                return self.dead()
            Fake.order.append('page')
            if Fake.reach == 'direct':
                return self.reply(200, {'id': Fake.page, 'name': 'Bittu Ki Riya', 'access_token': Fake.page_key})
            return self.reply(400, {'error': {'code': 100, 'message': 'Object does not exist'}})
        if path == '/v26.0/me':
            if tok != Fake.key:
                return self.dead()
            return self.reply(200, {'id': '999', 'name': 'uploader'})
        if path == '/v26.0/me/accounts':
            if tok != Fake.key:
                return self.dead()
            Fake.order.append('accounts')
            pages = [{'id': Fake.page, 'name': 'Bittu Ki Riya', 'access_token': Fake.page_key}] if Fake.reach == 'accounts' else []
            return self.reply(200, {'data': [{'id': '1', 'name': 'Other', 'access_token': 'EAO'}] + pages})
        if tok != Fake.page_key:
            return self.dead()
        if path == '/v26.0/V1' and q.get('fields') == 'status':
            Fake.polls += 1
            Fake.order.append('poll')
            done = Fake.polls > 1
            return self.reply(200, {'status': {'video_status': 'ready' if done else 'processing',
                                               'publishing_phase': {'status': 'complete' if done else 'in_progress'}}})
        if path == '/v26.0/V1' and q.get('fields') == 'permalink_url':
            return self.reply(200, {'permalink_url': '/reel/123456/'})
        self.reply(404, {'error': {'code': 100, 'message': 'no'}})

    def do_POST(self):
        path, q, raw = self.args()
        if path == '/video-upload/v26.0/V1':
            if self.headers.get('Authorization') != f'OAuth {Fake.page_key}':
                return self.dead()
            Fake.order.append('send')
            Fake.upload = {'offset': self.headers.get('offset'), 'file_size': self.headers.get('file_size'), 'bytes': len(raw)}
            return self.reply(200, {'success': True})
        if path == f'/v26.0/{Fake.page}/videos':
            if Fake.page_key.encode() not in raw:
                return self.dead()
            Fake.order.append('video')
            Fake.video_form, Fake.polls = raw, 0
            return self.reply(200, {'id': 'V1'})
        if q.get('access_token') != Fake.page_key:
            return self.dead()
        if path == f'/v26.0/{Fake.page}/video_reels' and q.get('upload_phase') == 'start':
            Fake.order.append('start')
            Fake.polls = 0
            return self.reply(200, {'video_id': 'V1', 'upload_url': 'x'})
        if path == f'/v26.0/{Fake.page}/video_reels' and q.get('upload_phase') == 'finish' and q.get('video_id') == 'V1':
            Fake.order.append('finish')
            Fake.finish = q
            return self.reply(200, {'success': True})
        self.reply(404, {'error': {'code': 100, 'message': 'no'}})


server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
port = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()
os.environ.update(FACEBOOK_TEST_SERVER=f'http://127.0.0.1:{port}', FACEBOOK_TOKEN=Fake.key, FACEBOOK_PAGE_ID=Fake.page)
record = work / 'facebook' / 'chaand.json'
(work / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False), encoding='utf-8')
facebook.WAIT_SECONDS = 0
facebook.time.sleep = lambda s: None


def run(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = facebook.main(list(args))
    said = out.getvalue()
    say(not any(k in said for k in (Fake.key, Fake.page_key, 'EAO', 'EA-dead')), 'nothing printed holds a key')
    return code, said


code, said = run('post', str(work / 'plan.json'), str(film), '--record', str(record), '--run', '7')
rec = json.loads(record.read_text()) if record.exists() else {}
say(code == 0 and Fake.order[:4] == ['page', 'start', 'send', 'finish'] and Fake.order[-1] == 'poll',
    f'find the Page first, then start the Reel, send the film, publish, wait: {Fake.order}')
size = film.stat().st_size
say(Fake.upload == {'offset': '0', 'file_size': str(size), 'bytes': size},
    'the film\'s bytes go straight to Facebook, whole, with no public link')
say(Fake.finish.get('video_state') == 'PUBLISHED' and Fake.finish.get('description') == text
    and Fake.finish.get('title') == 'Chaand Gayab Ho Gaya! 🌙', 'published with Instagram\'s caption and the YouTube title')
say(rec.get('url') == 'https://www.facebook.com/reel/123456/' and rec.get('as') == 'reel' and rec.get('run') == '7',
    f'the Reel\'s link is recorded: {rec.get("url")}')
if real_shape:
    facebook.instagram.shape = real_shape
    say(facebook.should(film, record, '7') == (False, 'already posted from this run: https://www.facebook.com/reel/123456/'),
        'a re-run of the same run never posts twice')
    facebook.instagram.shape = lambda f: (1080, 1920, Fake.seconds)

Fake.order, Fake.seconds = [], 150.0
record.unlink()
code, said = run('post', str(work / 'plan.json'), str(film), '--record', str(record), '--run', '8')
rec = json.loads(record.read_text()) if record.exists() else {}
say(code == 0 and Fake.order[:2] == ['page', 'video'] and 'start' not in Fake.order and rec.get('as') == 'video'
    and b'name="source"' in Fake.video_form and text.encode() in Fake.video_form and 'not a Reel' in said,
    'a film over 90 s goes up as an ordinary Page video, with the caption, and says it is not a Reel')
Fake.seconds = 79.0

Fake.order, Fake.reach = [], 'accounts'
code, said = run('check')
say(code == 0 and 'Bittu Ki Riya' in said and Fake.order == ['page', 'accounts'],
    'when the Page is not reachable directly, its key comes from the list of Pages the key may manage')

Fake.order, Fake.reach = [], 'none'
code, said = run('post', str(work / 'plan.json'), str(film), '--record', str(record), '--run', '9')
say(code == 1 and 'start' not in Fake.order and 'video' not in Fake.order and 'may not post to Page 6159' in said
    and 'FACEBOOK-SETUP' in said, 'a key that cannot reach the Page posts nothing, and says what to do')
Fake.reach = 'direct'

os.environ['FACEBOOK_TOKEN'] = 'EA-dead-key'
code, said = run('check')
say(code == 1 and 'no longer works' in said, 'a dead key says how to make a new one')
os.environ['FACEBOOK_TOKEN'] = Fake.key
os.environ.pop('FACEBOOK_PAGE_ID')
code, said = run('post', str(work / 'plan.json'), str(film), '--record', str(record), '--run', '10')
say(code == 1 and 'FACEBOOK_PAGE_ID' in said, 'with no Page number, nothing is posted')
server.shutdown()

guide = (ROOT / 'docs' / 'FACEBOOK-SETUP.md').read_text()
import re  # noqa: E402
steps = re.findall(r'^## (\d)\. ', guide, re.M)
said_steps = set(re.findall(r'steps? (\d)', pathlib.Path(facebook.__file__).read_text()))
say(steps and said_steps <= set(steps), f'the messages point at real setup steps: {sorted(said_steps)}')
say(all(k in guide for k in ('FACEBOOK_TOKEN', 'pages_manage_posts', 'facebook-check.yml', 'System user')),
    'the guide names the secret, the permission, the system user and the key check')

print('\nall good' if not bad else f'\n{bad} failing')
sys.exit(1 if bad else 0)
