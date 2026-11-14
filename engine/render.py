"""Make the film: each shot's picture from the frame its first word is spoken.

    python3 engine/render.py plan.json PICTURES_DIR VOICE_DIR OUT.mp4
        [--logo brand/watermark.png] [--music music/x.mp3] [--fps 30]

VOICE_DIR is what voice.py wrote (voice.wav and cuts.json).

Two layouts, chosen by the plan's "layout":
  - "wide" (16:9): every picture fills the frame; no subtitles unless the
    plan asks for "captions": true.
  - "short" (9:16): black, the plan's "hook" line at the top, a square
    picture in the middle, and subtitles under it that appear word by word
    as each word is spoken, *marked* words in yellow.

The film is cut into stretches in which nothing changes (a new picture, or
a new word in the subtitles, starts a new stretch). Each stretch is encoded
as exactly as many identical frames as it lasts, and the stretches are
joined without re-encoding, so every change happens on precisely the frame
worked out from the voice. The sound is the voice with the music bed under
it, pushed down whenever the voice speaks, brought to -14 LUFS.
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
from frames import SHORT, SIZES, shot_image, short_frame, square_image, with_logo  # noqa: E402

TAIL = 0.8          # the last picture stays this long after the voice ends
MUSIC_GAIN = -22    # dB under the voice
LINE_ENDS = tuple(',.?!;:।…')


def frame_plan(starts, total_seconds, fps):
    """[(first frame, frame count)] per shot. Shot i starts on the frame
    nearest its first word; the first shot starts on frame 0."""
    firsts = [0] + [round(s * fps) for s in starts[1:]]
    for i in range(1, len(firsts)):
        firsts[i] = max(firsts[i], firsts[i - 1] + 1)
    end = max(math.ceil(total_seconds * fps), firsts[-1] + 1)
    return [(f, (firsts[i + 1] if i + 1 < len(firsts) else end) - f) for i, f in enumerate(firsts)]


def caption_lines(words, shots, max_words):
    """Group the narration's words into subtitle lines: a line ends at a
    comma, full stop, question mark or danda, at max_words, or where a new
    paragraph begins. Returns [[word index, ...], ...]."""
    lines, cur = [], []
    for k, w in enumerate(words):
        new_par = shots[w['shot']].get('paragraph') and k and words[k - 1]['shot'] != w['shot']
        if cur and (len(cur) >= max_words or new_par or words[cur[-1]]['word'].rstrip('*"\'”’').endswith(LINE_ENDS)):
            lines.append(cur)
            cur = []
        cur.append(k)
    if cur:
        lines.append(cur)
    return lines


def stretches(shot_frames, word_frames, lines, end):
    """[(first frame, frame count, (shot, line, words shown))]: the film
    split wherever the picture or the subtitle changes."""
    marks = {0, end} | {f for f, _ in shot_frames} | {f for f in word_frames if 0 <= f < end}
    marks = sorted(m for m in marks if m <= end)
    line_of = {}
    for L, line in enumerate(lines):
        for k in line:
            line_of[k] = L
    out = []
    shot_firsts = [f for f, _ in shot_frames]
    for a, b in zip(marks, marks[1:]):
        shot = max(i for i, f in enumerate(shot_firsts) if f <= a)
        said = [k for k, f in enumerate(word_frames) if f <= a]
        if said and lines:
            L = line_of[said[-1]]
            shown = sum(1 for k in lines[L] if word_frames[k] <= a)
            state = (shot, L, shown)
        else:
            state = (shot, None, 0)
        if out and out[-1][2] == state:
            out[-1] = (out[-1][0], out[-1][1] + b - a, state)
        else:
            out.append((a, b - a, state))
    return out


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
    layout = plan.get('layout', 'wide')
    cuts = json.loads((voice_dir / 'cuts.json').read_text())
    size = SHORT['size'] if layout == 'short' else SIZES[plan.get('frame', '16:9')]
    total = max(cuts['audio_seconds'], cuts['speech_end'] + TAIL)
    shot_frames = frame_plan(cuts['starts'], total, fps)
    end = shot_frames[-1][0] + shot_frames[-1][1]
    logo = Image.open(logo_path).convert('RGBA') if logo_path else None

    captions = plan.get('captions', layout == 'short')
    words = cuts.get('words') or []
    lines = caption_lines(words, shots, 5 if layout == 'short' else 7) if captions and words else []
    # A word appears on the frame it is spoken; a shot's first word appears
    # with its picture.
    word_frames = [round(w['start'] * fps) for w in words] if lines else []
    for k, w in enumerate(words if lines else []):
        first = shot_frames[w['shot']][0]
        if k == 0 or words[k - 1]['shot'] != w['shot']:
            word_frames[k] = first
        word_frames[k] = max(word_frames[k], first)
    parts = stretches(shot_frames, word_frames, lines, end)

    def find(name):
        p = find_picture(pic_dir, name)
        if p is None:
            raise SystemExit(f'no picture "{name}" in {pic_dir}')
        return p

    hook_rows, hook_size, typeset = None, SHORT['hook_size'], None
    if layout == 'short' or lines:
        import typeset
        if not typeset.shaping_ok():
            raise SystemExit('Pillow has no Raqm text shaping: Hindi would be drawn wrongly. '
                             'Install libfribidi0 (apt) and use the Pillow wheel from locks/pictures.txt.')
        if layout == 'short' and plan.get('hook'):
            hook_rows, hook_size = typeset.fit_hook(plan['hook'], SHORT['hook_size'], SHORT['caption_width'])

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        base = {}
        for i, s in enumerate(shots):
            base[i] = square_image(s, find) if layout == 'short' else shot_image(s, find, size, logo)
        pngs, keys, cache = [], [], {}
        for first, n, (shot, L, shown) in parts:
            key = (shot, L, shown)
            if key not in cache:
                cap = None
                if L is not None and shown:
                    said = ' '.join(words[k]['word'] for k in lines[L][:shown])
                    cap = typeset.lay_out(typeset.words_of(said), SHORT['caption_size'] if layout == 'short' else 56,
                                          SHORT['caption_width'] if layout == 'short' else round(size[0] * 0.8))
                if layout == 'short':
                    img = short_frame(base[shot], hook_rows, cap, logo, hook_size)
                else:
                    img = base[shot].copy()
                    if cap:
                        img = with_caption_wide(img, cap, typeset)
                h = hashlib.sha1(img.tobytes()).hexdigest()[:16]
                png = tmp / f'{h}.png'
                if not png.exists():
                    img.save(png)
                cache[key] = png
            pngs.append(cache[key])
        segs = [tmp / f'seg{i:05d}.mp4' for i in range(len(parts))]
        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as pool:
            list(pool.map(lambda a: encode_segment(*a),
                          [(pngs[i], parts[i][1], fps, segs[i]) for i in range(len(parts))]))
        (tmp / 'list.txt').write_text(''.join(f"file '{p}'\n" for p in segs))
        video = tmp / 'video.mp4'
        run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(tmp / 'list.txt'),
             '-c', 'copy', str(video)])
        sound = tmp / 'sound.m4a'
        mix_audio(voice_dir / 'voice.wav', music, end / fps, sound)
        run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-i', str(sound), '-map', '0:v', '-map', '1:a',
             '-c', 'copy', '-movflags', '+faststart', '-shortest', str(out)])

    # What the sync check needs: where each shot and each subtitle word
    # starts, what each shot shows, and where on screen to look.
    pic_keys = [hashlib.sha1(base[i].tobytes()).hexdigest()[:16] for i in range(len(shots))]
    (out.with_suffix('.cuts.json')).write_text(json.dumps({
        'fps': fps, 'frames': shot_frames, 'pictures': pic_keys, 'starts': cuts['starts'],
        'picture_box': list(SHORT['picture']) if layout == 'short' else [0, 0, size[0], size[1]],
        'caption_box': ([0, SHORT['caption_top'] - 20, size[0], size[1]] if layout == 'short'
                        else [0, round(size[1] * 0.80), size[0], size[1]]) if lines else None,
        'word_frames': sorted(set(word_frames)) if lines else [],
        'size': list(size)}, indent=0))
    print(f'{out.name}: {layout}, {len(shots)} shots, {len(parts)} stretches, {end} frames, {end / fps:.1f} s'
          + (f', {len(lines)} subtitle lines' if lines else '')
          + (f', music {pathlib.Path(music).name}' if music else ''))
    return 0


def with_caption_wide(img, rows, typeset):
    """Subtitles on a wide picture: white on a dark band near the bottom."""
    from PIL import ImageDraw
    W, H = img.size
    size = 56
    lh = round(size * 1.32)
    top = H - round(H * 0.06) - lh * len(rows)
    band = Image.new('RGBA', (W, lh * len(rows) + 40), (0, 0, 0, 140))
    out = img.convert('RGBA')
    out.alpha_composite(band, (0, top - 20))
    out = out.convert('RGB')
    typeset.draw_rows(out, rows, size, W // 2, top)
    return out


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
