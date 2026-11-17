"""Check, in the finished film itself, that every picture and every
subtitle word lands on its spoken word.

    python3 engine/check_sync.py FILM.mp4

Reads FILM.cuts.json (written by render.py), decodes the film, and finds
every frame where the picture area changes and, for films with subtitles,
every frame where the subtitle area changes. Fails if any change is more
than one frame from where the voice says it belongs, if something changes
where nothing should, or if the sound and the picture differ in length.
"""
import json
import pathlib
import subprocess
import sys

import numpy as np

TOLERANCE = 1      # frames


def decode(film, size):
    """Every frame, small and grey: (frames, h, w)."""
    W, H = size
    w, h = 108, round(108 * H / W)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(film), '-vf', f'scale={w}:{h}',
                          '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.int16), w / W


def changes(frames, box, scale, threshold):
    x0, y0, x1, y1 = (round(v * scale) for v in box)
    area = frames[:, y0:y1, x0:x1]
    diff = np.abs(np.diff(area, axis=0)).mean(axis=(1, 2))
    return [int(i) + 1 for i in np.nonzero(diff > threshold)[0]]


def compare(want, got, what, fps):
    bad = []
    for f in want:
        near = min(got, key=lambda g: abs(g - f), default=None)
        if near is None or abs(near - f) > TOLERANCE:
            bad.append(f'{what} should change at frame {f} ({f / fps:.2f} s), '
                       f'nearest change is {"none" if near is None else f"frame {near}"}')
    extra = [g for g in got if all(abs(g - f) > TOLERANCE for f in want)]
    for g in extra[:10]:
        bad.append(f'{what} changes at frame {g} ({g / fps:.2f} s) where nothing starts')
    exact = sum(1 for f in want if f in got)
    return bad, exact


def duration(film, stream):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', stream, '-show_entries',
                          'stream=duration', '-of', 'csv=p=0', str(film)], capture_output=True, text=True).stdout
    return float(out.strip() or 0)


def main(film):
    film = pathlib.Path(film)
    info = json.loads(film.with_suffix('.cuts.json').read_text())
    fps, frames_plan, pics = info['fps'], info['frames'], info['pictures']
    size = info.get('size', [1920, 1080])
    frames, scale = decode(film, size)
    bad = []

    # Animated graphics move on every frame of their shot: only their first
    # frame (the cut) can be checked; everything inside them is skipped.
    moving = info.get('moving') or []
    still = lambda f: not any(a < f < a + n for a, n in moving)
    want = [frames_plan[i][0] for i in range(1, len(frames_plan)) if pics[i] != pics[i - 1]]
    # With subtitles, the picture is judged above them: a new subtitle line
    # is big enough on an upright film to look like a picture change.
    box = list(info.get('picture_box') or [0, 0, *size])
    if info.get('caption_box'):
        box[3] = min(box[3], info['caption_box'][1])
    got = [g for g in changes(frames, box, scale, 2.0) if still(g)]
    b, exact = compare(want, got, 'picture', fps)
    bad += b
    report = f'{len(want)} picture changes, {exact} on the exact frame'
    if moving:
        report += f' ({len(moving)} animated graphic(s), checked at their first frame)'

    if info.get('caption_box'):
        wantc = [f for f in info['word_frames'] if f > 0 and still(f)]
        gotc = [g for g in changes(frames, info['caption_box'], scale, 0.3) if still(g)]
        b, exactc = compare(wantc, gotc, 'subtitle', fps)
        bad += b
        report += f'; {len(wantc)} subtitle changes, {exactc} on the exact frame'

    expected = sum(c for _, c in frames_plan)
    if abs(len(frames) - expected) > 1:
        bad.append(f'film has {len(frames)} frames, the shots add up to {expected}')
    v, a = duration(film, 'v:0'), duration(film, 'a:0')
    if abs(v - a) > 0.1:
        bad.append(f'picture is {v:.2f} s and sound {a:.2f} s')
    for x in bad:
        print('FAIL ' + x)
    print(report + ('' if not bad else f'; {len(bad)} problem(s)'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
