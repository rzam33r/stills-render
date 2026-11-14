"""Check, in the finished film itself, that every picture lands on its word.

    python3 engine/check_sync.py FILM.mp4

Reads FILM.cuts.json (written by render.py: each shot's first frame and
which picture it shows), decodes the film, finds every frame where the
picture changes, and compares. Fails if any change is more than one frame
from where the voice says it belongs, if a picture changes where no shot
starts, or if the sound and the picture differ in length.
"""
import json
import pathlib
import subprocess
import sys

import numpy as np

TOLERANCE = 1      # frames
W, H = 96, 54


def changes(film):
    """Frame numbers where the picture changes."""
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(film), '-vf', f'scale={W}:{H}',
                          '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.int16)
    diff = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))
    return [int(i) + 1 for i in np.nonzero(diff > 2.0)[0]], len(frames)


def duration(film, stream):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', stream, '-show_entries',
                          'stream=duration', '-of', 'csv=p=0', str(film)], capture_output=True, text=True).stdout
    return float(out.strip() or 0)


def main(film):
    film = pathlib.Path(film)
    info = json.loads(film.with_suffix('.cuts.json').read_text())
    fps, frames, pics = info['fps'], info['frames'], info['pictures']
    want = [frames[i][0] for i in range(1, len(frames)) if pics[i] != pics[i - 1]]
    got, n = changes(film)
    bad = []
    for f in want:
        near = min(got, key=lambda g: abs(g - f), default=None)
        if near is None or abs(near - f) > TOLERANCE:
            bad.append(f'picture should change at frame {f} ({f / fps:.2f} s), '
                       f'nearest change is {"none" if near is None else f"frame {near}"}')
    extra = [g for g in got if all(abs(g - f) > TOLERANCE for f in want)]
    for g in extra[:10]:
        bad.append(f'picture changes at frame {g} ({g / fps:.2f} s) where no shot starts')
    expected = sum(c for _, c in frames)
    if abs(n - expected) > 1:
        bad.append(f'film has {n} frames, the shots add up to {expected}')
    v, a = duration(film, 'v:0'), duration(film, 'a:0')
    if abs(v - a) > 0.1:
        bad.append(f'picture is {v:.2f} s and sound {a:.2f} s')
    for b in bad:
        print('FAIL ' + b)
    exact = sum(1 for f in want if f in got)
    print(f'{len(want)} picture changes, {exact} on the exact frame, '
          f'{len(want) - exact - len([b for b in bad if "should change" in b])} one frame off'
          + ('' if not bad else f'; {len(bad)} problem(s)'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
