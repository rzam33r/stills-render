"""Add the Bittu Ki Riya ending (Like, Follow, Subscribe) after a finished film.

    python3 engine/ending.py FILM.mp4 [--ending brand/ending-upright.mp4]

The film is changed in place: FILM.mp4 then ends with the ending.

- The ending is brand/ending-upright.mp4 (4.7 s, 1080 x 1920), made by
  Roshan on 24 Nov 2026. An upright film gets it as it is. A wide film gets
  it in the middle of the frame over a blurred, darkened copy of itself.
- Its sound (four soft pops) is brought up to sit just under the
  narration's -14 LUFS, so the pops are heard without startling anyone.
- The ending is encoded exactly like the film, and the two are joined
  without re-encoding the film (no quality lost, a few seconds' work). The
  joined film is decoded once from start to end; if anything is wrong, the
  join is made again the slow, sure way.
- An upright film stays a YouTube Short only up to 3 minutes. If the ending
  would push it over, the ending is left off and the film is told so.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ENDING = ROOT / 'brand' / 'ending-upright.mp4'
SHORT_LIMIT = 180.0          # seconds: longer upright films are not Shorts
MARGIN = 0.5
TARGET_LUFS = -16.0          # just under the narration's -14
PEAK = -1.5                  # dB: the loudest pop stays below this
FPS = 30
# The film's own settings (render.py): the ending must match them exactly to
# be joined without re-encoding the film.
VIDEO = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-tune', 'stillimage', '-pix_fmt', 'yuv420p',
         '-r', str(FPS), '-video_track_timescale', str(FPS * 1000), '-g', str(FPS * 10)]
AUDIO = ['-ar', '48000', '-ac', '2', '-c:a', 'aac', '-b:a', '192k']


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def probe(path):
    out = json.loads(run(['ffprobe', '-v', 'error', '-show_entries',
                          'format=duration:stream=codec_type,width,height,sample_rate,channels',
                          '-of', 'json', str(path)]).stdout)
    v = next(s for s in out['streams'] if s['codec_type'] == 'video')
    a = next((s for s in out['streams'] if s['codec_type'] == 'audio'), None)
    return {'w': int(v['width']), 'h': int(v['height']), 'seconds': float(out['format']['duration']),
            'audio': a is not None}


def fits(film_seconds, upright, ending_seconds):
    """Whether the ending may be added: never push a Short past 3 minutes."""
    return not upright or film_seconds + ending_seconds <= SHORT_LIMIT - MARGIN


def gain(path):
    """dB to add to the ending's sound: towards TARGET_LUFS, never past PEAK."""
    err = subprocess.run(['ffmpeg', '-nostats', '-i', str(path), '-af', 'ebur128=peak=sample', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    m = re.findall(r'I:\s+(-?[\d.]+) LUFS', err)
    p = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', err)
    if not m:
        return 0.0
    loud = float(m[-1])
    peak = float(p[-1]) if p else 0.0
    return round(max(0.0, min(TARGET_LUFS - loud, PEAK - peak)), 1)


def prepare(ending, size, out):
    """The ending, at the film's size and in the film's exact encoding."""
    w, h = size
    if w > h:     # a wide film: the upright ending over a blurred copy of itself
        picture = (f'[0:v]fps={FPS},split[a][b];'
                   f'[a]scale={w}:-2,crop={w}:{h},boxblur=24:2,eq=brightness=-0.12[bg];'
                   f'[b]scale=-2:{h}[fg];[bg][fg]overlay=(W-w)/2:0,setsar=1,format=yuv420p[v]')
    else:
        picture = (f'[0:v]fps={FPS},scale={w}:{h}:force_original_aspect_ratio=decrease,'
                   f'pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[v]')
    db = gain(ending)
    sound = f'[0:a]aresample=48000,volume={db}dB,alimiter=limit={10 ** (PEAK / 20):.3f}:level=0[a]'
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(ending), '-filter_complex', f'{picture};{sound}',
         '-map', '[v]', '-map', '[a]'] + VIDEO + AUDIO + ['-movflags', '+faststart', str(out)])
    return db


def decodes(path):
    """True when the whole file decodes without a single error."""
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'null', '-'], capture_output=True, text=True)
    return r.returncode == 0 and not r.stderr.strip()


def add(film, ending=ENDING):
    """Join the ending onto the film, in place. Returns a sentence saying what happened."""
    film, ending = pathlib.Path(film), pathlib.Path(ending)
    if not ending.exists():
        return f'no ending added: {ending} is missing'
    f = probe(film)
    e = probe(ending)
    upright = f['h'] > f['w']
    if not fits(f['seconds'], upright, e['seconds']):
        return (f'no ending added: the film is {f["seconds"]:.1f} s, and with the {e["seconds"]:.1f} s ending it '
                f'would pass 3 minutes and stop being a YouTube Short')
    if not f['audio']:
        return 'no ending added: the film has no sound track to join it to'
    work = pathlib.Path(tempfile.mkdtemp())
    tail = work / 'ending.mp4'
    db = prepare(ending, (f['w'], f['h']), tail)
    joined = work / 'joined.mp4'
    (work / 'list.txt').write_text(f"file '{film.resolve()}'\nfile '{tail}'\n")
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(work / 'list.txt'),
         '-c', 'copy', '-movflags', '+faststart', str(joined)])
    want = f['seconds'] + probe(tail)['seconds']
    how = 'joined without re-encoding the film'
    if not decodes(joined) or abs(probe(joined)['seconds'] - want) > 0.25:
        run(['ffmpeg', '-v', 'error', '-y', '-i', str(film), '-i', str(tail), '-filter_complex',
             '[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]', '-map', '[v]', '-map', '[a]']
            + VIDEO + AUDIO + ['-movflags', '+faststart', str(joined)])
        how = 're-encoded, because the quick join did not decode cleanly'
    shutil.move(str(joined), str(film))
    shutil.rmtree(work, ignore_errors=True)
    shape = 'upright' if upright else 'wide, over a blurred background'
    return (f'ending added ({shape}): {f["seconds"]:.1f} s + {e["seconds"]:.1f} s = {probe(film)["seconds"]:.1f} s, '
            f'its sound raised {db} dB, {how}')


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 2
    ending = argv[argv.index('--ending') + 1] if '--ending' in argv else ENDING
    print(add(argv[0], ending))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
