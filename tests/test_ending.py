"""Every film ends with the Bittu Ki Riya ending, upright or wide.

    python3 tests/test_ending.py

Films made the way render.py makes them (same encoding, -14 LUFS sound) get
brand/ending-upright.mp4 joined on: the film keeps its length and picture,
the ending follows at the film's size, its pops are heard, the whole thing
decodes cleanly, and an upright film never passes 3 minutes because of it.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
import ending  # noqa: E402

bad = 0


def say(ok, msg):
    global bad
    bad += not ok
    print(('ok   ' if ok else 'FAIL ') + msg)


def make_film(path, size, seconds):
    """A stand-in film, encoded exactly as render.py encodes one."""
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=c=0x3a6ea5:s={size}:d={seconds}:r=30',
                    '-f', 'lavfi', '-i', f'sine=f=330:d={seconds}:sample_rate=48000',
                    '-af', 'aformat=channel_layouts=stereo,volume=-12dB']
                   + ending.VIDEO + ending.AUDIO + ['-movflags', '+faststart', str(path)], check=True)


def colour(path, at):
    """The average colour of one frame, as (r, g, b)."""
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(at), '-i', str(path), '-frames:v', '1',
                          '-vf', 'scale=1:1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    return tuple(raw[:3])


def loudest(path, start):
    err = subprocess.run(['ffmpeg', '-nostats', '-ss', str(start), '-i', str(path), '-af', 'volumedetect',
                          '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(err.split('max_volume:')[1].split('dB')[0])


if not shutil.which('ffmpeg'):
    print('skip: no ffmpeg here')
    sys.exit(0)

tail = ending.probe(ending.ENDING)
say(tail['h'] > tail['w'] and 4 <= tail['seconds'] <= 8 and tail['audio'],
    f'the ending is upright, {tail["seconds"]:.1f} s, with sound')
work = pathlib.Path(tempfile.mkdtemp())
for name, size in (('upright', '1080x1920'), ('wide', '1920x1080')):
    film = work / f'{name}.mp4'
    make_film(film, size, 6)
    said = ending.add(film)
    got = ending.probe(film)
    w, h = (int(x) for x in size.split('x'))
    say((got['w'], got['h']) == (w, h) and abs(got['seconds'] - (6 + tail['seconds'])) < 0.2,
        f'{name}: {said}')
    say(ending.decodes(film), f'{name}: the joined film decodes from start to end without an error')
    blue = colour(film, 3)
    say(blue[2] > 150 and blue[0] < 90, f'{name}: the film itself is untouched before the ending {blue}')
    end = colour(film, 6 + tail['seconds'] - 0.3)
    say(end != blue and end[0] > end[2], f'{name}: the last frames are the warm Bittu Ki Riya ending {end}')
    pops = loudest(film, 6.2)
    say(-12 <= pops <= -1.5, f'{name}: the ending\'s pops are heard, and stay below -1.5 dB ({pops} dB)')

say(ending.fits(170, True, 4.7) and not ending.fits(176, True, 4.7) and ending.fits(900, False, 4.7),
    'an upright film near 3 minutes gets no ending (it would stop being a Short); a wide one always does')
long_short = work / 'long.mp4'
make_film(long_short, '1080x1920', 177)
before = ending.probe(long_short)['seconds']
said = ending.add(long_short)
say(ending.probe(long_short)['seconds'] == before and 'Short' in said, f'a 177 s upright film is left as it is: {said}')

print('\nall good' if not bad else f'\n{bad} failing')
sys.exit(1 if bad else 0)
