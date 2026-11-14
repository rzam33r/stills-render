"""Make the film: each shot's picture from the frame its first word is spoken.

    python3 engine/render.py plan.json PICTURES_DIR VOICE_DIR OUT.mp4
        [--logo brand/watermark.png] [--music music/x.mp3] [--fps 30]

VOICE_DIR is what voice.py wrote (voice.wav and cuts.json).

Every shot is encoded as its own run of identical frames, exactly as many
as it is on screen, and the runs are joined without re-encoding, so a cut
happens on precisely the frame worked out from the voice; nothing is
rounded twice. The sound is the voice with the music bed under it, the
bed pushed down whenever the voice speaks, and the whole mix brought to
-14 LUFS, YouTube's loudness.
"""
import concurrent.futures
import hashlib
import json
import math
import os
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from check_plan import find_picture  # noqa: E402
from frames import SIZES, shot_image  # noqa: E402

TAIL = 0.8          # the last picture stays this long after the voice ends
MUSIC_GAIN = -22    # dB under the voice


def frame_plan(starts, total_seconds, fps):
    """[(first frame, frame count)] per shot. Shot i starts on the frame
    nearest its first word; the first shot starts on frame 0."""
    firsts = [0] + [round(s * fps) for s in starts[1:]]
    for i in range(1, len(firsts)):
        firsts[i] = max(firsts[i], firsts[i - 1] + 1)
    end = max(math.ceil(total_seconds * fps), firsts[-1] + 1)
    return [(f, (firsts[i + 1] if i + 1 < len(firsts) else end) - f) for i, f in enumerate(firsts)]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f'ffmpeg failed: {" ".join(cmd[:6])} ...\n{r.stderr[-2000:]}')


def encode_segment(png, frames, fps, out):
    run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', str(fps), '-i', str(png),
         '-frames:v', str(frames), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
         '-tune', 'stillimage', '-pix_fmt', 'yuv420p', '-r', str(fps), '-video_track_timescale', str(fps * 1000),
         '-g', str(fps * 10), str(out)])


def mix_audio(voice, music, total, out):
    """Voice, plus the bed under it if there is one, at -14 LUFS."""
    if music:
        fade_out = max(0.0, total - 3)
        chain = (f'[0:a]aresample=48000,apad,atrim=0:{total:.3f},asplit=2[v][key];'
                 f'[1:a]aresample=48000,volume={MUSIC_GAIN}dB,afade=t=in:st=0:d=1.5,'
                 f'afade=t=out:st={fade_out:.3f}:d=3[bed];'
                 f'[bed][key]sidechaincompress=threshold=0.03:ratio=8:attack=25:release=450[duck];'
                 f'[v][duck]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[a]')
        cmd = ['ffmpeg', '-v', 'error', '-y', '-i', str(voice), '-stream_loop', '-1', '-t', f'{total:.3f}',
               '-i', str(music), '-filter_complex', chain, '-map', '[a]']
    else:
        cmd = ['ffmpeg', '-v', 'error', '-y', '-i', str(voice), '-af',
               f'aresample=48000,apad,atrim=0:{total:.3f},loudnorm=I=-14:TP=-1.5:LRA=11']
    run(cmd + ['-ar', '48000', '-ac', '2', '-c:a', 'aac', '-b:a', '192k', str(out)])


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    plan_path, pic_dir, voice_dir, out = (pathlib.Path(a) for a in argv[:4])
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    fps = int(opt('--fps', 30))
    logo_path, music = opt('--logo'), opt('--music')

    plan = json.loads(plan_path.read_text(encoding='utf-8-sig'))
    shots = plan['shots']
    cuts = json.loads((voice_dir / 'cuts.json').read_text())
    size = SIZES[plan.get('frame', '16:9')]
    total = max(cuts['audio_seconds'], cuts['speech_end'] + TAIL)
    plan_frames = frame_plan(cuts['starts'], total, fps)
    logo = Image.open(logo_path).convert('RGBA') if logo_path else None

    def find(name):
        p = find_picture(pic_dir, name)
        if p is None:
            raise SystemExit(f'no picture "{name}" in {pic_dir}')
        return p

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        pngs, keys = [], []
        for i, s in enumerate(shots):
            img = shot_image(s, find, size, logo)
            key = hashlib.sha1(img.tobytes()).hexdigest()[:16]
            png = tmp / f'{key}.png'
            if not png.exists():
                img.save(png)
            pngs.append(png)
            keys.append(key)
        segs = [tmp / f'seg{i:04d}.mp4' for i in range(len(shots))]
        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as pool:
            list(pool.map(lambda a: encode_segment(*a),
                          [(pngs[i], plan_frames[i][1], fps, segs[i]) for i in range(len(shots))]))
        (tmp / 'list.txt').write_text(''.join(f"file '{p}'\n" for p in segs))
        video = tmp / 'video.mp4'
        run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(tmp / 'list.txt'),
             '-c', 'copy', str(video)])
        sound = tmp / 'sound.m4a'
        frames_total = sum(n for _, n in plan_frames)
        mix_audio(voice_dir / 'voice.wav', music, frames_total / fps, sound)
        run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-i', str(sound), '-map', '0:v', '-map', '1:a',
             '-c', 'copy', '-movflags', '+faststart', '-shortest', str(out)])

    # What the sync check needs: each shot's first frame and what it shows.
    (out.with_suffix('.cuts.json')).write_text(json.dumps({
        'fps': fps, 'frames': plan_frames, 'pictures': keys, 'starts': cuts['starts']}, indent=0))
    print(f'{out.name}: {len(shots)} shots, {frames_total} frames, {frames_total / fps:.1f} s'
          + (f', music {pathlib.Path(music).name}' if music else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
