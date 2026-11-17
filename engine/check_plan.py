"""Check a still-picture film's plan.json before anything is made.

A film is a list of shots, in the order they are seen and heard:

    {
      "title": "How Did Ancient Humans Survive Without Clean Water?",
      "shots": [
        {"say": "It's early morning and you're crouched beside a river.",
         "picture": "001"},
        {"say": "They had no filters,", "card": "No filters.", "doodle": "002"},
        {"say": "The silent killer they couldn't see.",
         "card": "The silent killer they couldn't see.", "paragraph": true}
      ]
    }

- "say": the exact words spoken while this shot is on screen. The shot
  appears on the frame its first word is spoken and stays until the next
  shot's first word.
- "picture": the file (001.png, .jpg or .webp) filling the frame, or
- "card": a short line drawn on a white card by the engine (no spelling
  mistakes from an image model), with an optional small "doodle" picture
  under it.
- "paragraph": true starts a new paragraph: the voice takes a breath first.

Optional top level:
  "layout"    "wide" (16:9, a picture about every 3 seconds; the default) or
              "short" (9:16 upright, a picture every 2 to 4 words); in both,
              every picture fills the whole frame
  "language"  "en" (default) or "hi"
  "captions"  true for word-by-word subtitles over the pictures (default off)
  "voice"     leave out: English is read by Kokoro (am_michael), Hindi by
              Chatterbox (chatterbox-hi). Kokoro voices may be named (English,
              or Hindi hm_omega, hm_psi, hf_alpha, hf_beta); or an Azure voice
  "speed"     0.8 to 1.3, default 1.0
  "music"     a file in music/
  "frame"     "16:9" or "9:16" for the wide layout

In "say", *asterisks* mark words to show in yellow when subtitles are on;
the voice does not read them.

    python3 engine/check_plan.py plan.json [--pictures DIR]

Prints every problem in plain words, then "ready" or "not ready". Exit 1
when not ready.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from voices import AZURE, CHATTERBOX_VOICES, KOKORO_VOICES, is_hindi_voice  # noqa: E402

PICTURE_EXT = ('.png', '.jpg', '.jpeg', '.webp')
VOICES = KOKORO_VOICES | CHATTERBOX_VOICES
KEYS = {'say', 'picture', 'card', 'doodle', 'paragraph', 'note', 'prompt', 'doodle_prompt', 'who'}
TOP = {'title', 'shots', 'voice', 'speed', 'music', 'frame', 'character', 'style', 'description',
       'layout', 'language', 'captions', 'cast', 'extras'}
# A cast film's characters live in a Flow project; "who" names them per picture.
CASTS = {'Bittu & Riya': ('Bittu', 'Riya')}
# The line each prompt carries for each cast member in it (CAST.md, word for word).
KEEP = {
    'Bittu': 'Bittu keeps his warm brown wavy hair, his orange shirt open over his beige T-shirt, blue jeans, white sneakers and wristwatch.',
    'Riya': 'Riya keeps her long loose wavy hair, never tied up, her red V-neck top, black pants, white sneakers, gold hoop earrings and gold pendant.',
}
# Words per shot: (aim low, aim high, warn above, refuse above).
SHOT_WORDS = {'wide': (6, 12, 16, 24), 'short': (1, 5, 7, 10)}

# How fast the voice speaks, for the length estimate: words per second.
# Hindi is Chatterbox: 152 words in 46.4 s and 134 in 39.8 s (Nov 2026).
WPS_BY_LANGUAGE = {'en': 2.75, 'hi': 3.3}
WPS = WPS_BY_LANGUAGE['en']


def words(text):
    """The words of a line, any script: what sits between spaces and has a
    letter or digit in it (Hindi vowel signs count as part of the word)."""
    import unicodedata
    out = []
    for w in (text or '').replace('*', ' ').split():
        core = ''.join(c for c in w if unicodedata.category(c)[0] in 'LMN')
        if core:
            out.append(core)
    return out


def find_picture(folder, name):
    """The file for a picture name ("001"), or None."""
    if folder is None:
        return None
    folder = pathlib.Path(folder)
    for ext in PICTURE_EXT:
        for cand in (folder / f'{name}{ext}', folder / f'{name}{ext.upper()}'):
            if cand.is_file():
                return cand
    return None


def image_size(path):
    """(width, height) of a PNG, JPEG or WebP file from its header, or None."""
    try:
        with open(path, 'rb') as f:
            head = f.read(64)
            if head[:8] == b'\x89PNG\r\n\x1a\n':
                return int.from_bytes(head[16:20], 'big'), int.from_bytes(head[20:24], 'big')
            if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
                kind = head[12:16]
                if kind == b'VP8 ':
                    return (int.from_bytes(head[26:28], 'little') & 0x3FFF,
                            int.from_bytes(head[28:30], 'little') & 0x3FFF)
                if kind == b'VP8L':
                    b0 = int.from_bytes(head[21:25], 'little')
                    return (b0 & 0x3FFF) + 1, ((b0 >> 14) & 0x3FFF) + 1
                if kind == b'VP8X':
                    return int.from_bytes(head[24:27], 'little') + 1, int.from_bytes(head[27:30], 'little') + 1
                return None
            if head[:2] == b'\xff\xd8':
                f.seek(2)
                while True:
                    m = f.read(2)
                    if len(m) < 2 or m[0] != 0xFF:
                        return None
                    if m[1] in (0xD8, 0x01) or 0xD0 <= m[1] <= 0xD7:
                        continue
                    n = int.from_bytes(f.read(2), 'big')
                    if 0xC0 <= m[1] <= 0xCF and m[1] not in (0xC4, 0xC8, 0xCC):
                        seg = f.read(5)
                        return int.from_bytes(seg[3:5], 'big'), int.from_bytes(seg[1:3], 'big')
                    f.seek(n - 2, 1)
    except OSError:
        return None
    return None


# A picture whose shorter side is under this many pixels looks blurry in the
# film (1080 wide). 17 Nov 2026: a 286 x 512 preview was saved instead of the
# 768 x 1376 picture.
MIN_SIDE = 600


def check(plan, pictures=None):
    """(errors, warnings) for a plan; pictures is the folder of pictures, or None."""
    errors, warnings = [], []
    # Problems with how pictures are to be made (cast, "who", "extras") stop a
    # plan before its pictures exist; once they do (GitHub, with --pictures),
    # they cannot change the pictures, so they never stop the film.
    making = []
    if not isinstance(plan, dict):
        return ['plan.json must be an object with "title" and "shots"'], []
    for k in plan:
        if k not in TOP:
            warnings.append(f'unknown top-level key "{k}" is ignored')
    if not str(plan.get('title', '')).strip():
        errors.append('no "title"')
    elif not re.search(r'[A-Za-z0-9]', str(plan['title'])):
        warnings.append('the "title" has no English letters, so the film gets a date for a name; '
                        'write titles in English letters (Hinglish is fine)')
    shots = plan.get('shots')
    if not isinstance(shots, list) or not shots:
        return errors + ['no "shots" list'], warnings
    layout = plan.get('layout', 'wide')
    lang = plan.get('language', 'en')
    wps = WPS_BY_LANGUAGE.get(lang, WPS)
    if layout not in SHOT_WORDS:
        errors.append('"layout" must be "wide" or "short"')
        layout = 'wide'
    if lang not in ('en', 'hi'):
        errors.append('"language" must be "en" or "hi"')
    voice = plan.get('voice')
    if voice is not None and voice not in VOICES and not AZURE.match(str(voice)):
        errors.append(f'"voice": "{voice}" is neither a Kokoro voice ({", ".join(sorted(VOICES))}) '
                      'nor an Azure neural voice like hi-IN-MadhurNeural')
    if voice is not None:
        hindi_voice = is_hindi_voice(voice)
        if lang == 'hi' and not hindi_voice:
            errors.append(f'a Hindi film needs a Hindi voice (leave "voice" out for Chatterbox), not "{voice}"')
        if lang == 'en' and hindi_voice:
            errors.append(f'"{voice}" is a Hindi voice; set "language": "hi" or choose an English voice')
    if layout == 'short' and plan.get('frame', '9:16') != '9:16':
        warnings.append('a short film is always 9:16; "frame" is ignored')
    sp = plan.get('speed', 1.0)
    if not isinstance(sp, (int, float)) or not 0.8 <= sp <= 1.3:
        errors.append('"speed" must be a number from 0.8 to 1.3')
    frame = '9:16' if layout == 'short' or plan.get('frame') == '9:16' else '16:9'
    if plan.get('frame', '16:9') not in ('16:9', '9:16'):
        errors.append('"frame" must be "16:9" or "9:16"')
    cast = plan.get('cast')
    members = ()
    if cast is not None:
        if cast not in CASTS:
            making.append(f'"cast": "{cast}" is not a cast; the casts are: ' + ', '.join(f'"{c}"' for c in CASTS))
        else:
            members = CASTS[cast]
            if 'character' in plan:
                warnings.append(f'a "{cast}" film leaves out "character": the Flow characters carry the looks')
            if not any(isinstance(s, dict) and s.get('who') for s in (plan.get('shots') or [])):
                warnings.append(f'a "{cast}" film with no "who" anywhere: no picture will be tagged')
    extras = plan.get('extras')
    if extras is None:
        extras = {}
    elif (not isinstance(extras, dict)
          or not all(isinstance(k, str) and k.strip() and isinstance(v, str) and len(words(v)) >= 4
                     for k, v in extras.items())):
        making.append('"extras" must map each one-off person\'s short name to their look, like '
                      '{"Ugg": "a tall stone-age man with a bushy black beard and a brown fur wrap"}')
        extras = {}
    for k in extras:
        if k in members:
            making.append(f'"extras": {k} is in the cast; the Flow character carries their look')
    unused = set(extras)

    used = {}
    total = 0
    for i, s in enumerate(shots, 1):
        where = f'shot {i}'
        if not isinstance(s, dict):
            errors.append(f'{where}: must be an object')
            continue
        for k in s:
            if k not in KEYS:
                warnings.append(f'{where}: unknown key "{k}" is ignored')
        say = s.get('say')
        w = words(say)
        if not isinstance(say, str) or not w:
            errors.append(f'{where}: "say" must hold the words spoken during this shot')
            continue
        total += len(w)
        snippet = ' '.join(w[:6])
        where = f'shot {i} ("{snippet}…")'
        lo, hi, warn, refuse = SHOT_WORDS[layout]
        if len(w) > refuse:
            errors.append(f'{where}: {len(w)} words is about {len(w) / wps:.0f} s on one picture; split it (aim for {lo} to {hi} words)')
        elif len(w) > warn:
            warnings.append(f'{where}: {len(w)} words, about {len(w) / wps:.0f} s on one picture; {lo} to {hi} keeps the pictures moving')
        elif len(w) < 3 and layout == 'wide' and i != len(shots):
            warnings.append(f'{where}: {len(w)} word(s) is under a second on screen')
        if say.count('*') % 2:
            warnings.append(f'{where}: an odd number of * marks; a highlight is not closed')
        has_pic, has_card = 'picture' in s, 'card' in s
        if has_pic == has_card:
            errors.append(f'{where}: give exactly one of "picture" or "card"')
            continue
        if has_card:
            card = s['card']
            if not isinstance(card, str) or not words(card):
                errors.append(f'{where}: "card" must be the short line to show')
            elif len(card) > 70 or len(words(card)) > 10:
                errors.append(f'{where}: card "{card}" is too long for a card (at most 10 words)')
        if 'who' in s:
            who = s['who']
            if not has_pic:
                making.append(f'{where}: "who" goes only with a picture')
            elif cast is None:
                making.append(f'{where}: "who" names cast members, so the plan needs "cast" at the top')
            elif (not isinstance(who, list) or not who or len(set(map(str, who))) != len(who)
                  or any(m not in members for m in who)):
                if members:
                    making.append(f'{where}: "who" must list who is in the picture, from '
                                  + ', '.join(f'"{m}"' for m in members) + ', each once, like ["' + members[0] + '"]')
        if has_pic and members:
            listed = s.get('who') if isinstance(s.get('who'), list) else []
            for m in members:
                # "Bittu's drawing" only mentions him; any other use of the name
                # may mean he is in the picture, so ask, never block.
                if m not in listed and re.search(rf'\b{re.escape(m)}\b(?![\'’]s\b)', str(s.get('prompt', ''))):
                    warnings.append(f'{where}: the prompt names {m} but "who" leaves {m} out: if the picture '
                                    f'shows {m}, add {m} to "who" so {m} is cast; if it only mentions {m}, leave it')
        prompt = str(s.get('prompt', ''))
        if has_pic and members and isinstance(s.get('who'), list):
            for m in s['who']:
                if m in KEEP and KEEP[m] not in prompt:
                    warnings.append(f'{where}: the prompt lacks {m}\'s keep-line (CAST.md), word for word')
        if has_pic:
            for k, look in extras.items():
                if re.search(rf'\b{re.escape(k)}\b', prompt):
                    unused.discard(k)
                    if look not in prompt:
                        warnings.append(f'{where}: the prompt shows {k} without their look from "extras", '
                                        'word for word, so they will look different')
        if has_pic and not str(s.get('prompt', '')).strip():
            warnings.append(f'{where}: picture with no "prompt" for Flow')
        if s.get('doodle') is not None and not str(s.get('doodle_prompt', '')).strip():
            warnings.append(f'{where}: doodle with no "doodle_prompt" for Flow')
        names = [('picture', s.get('picture'))] if has_pic else []
        if s.get('doodle') is not None:
            if has_pic:
                errors.append(f'{where}: "doodle" goes only with a card')
            names.append(('doodle', s['doodle']))
        for key, name in names:
            if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,40}', name):
                errors.append(f'{where}: "{key}" must be a file name without extension, like "001"')
                continue
            if name in used:
                warnings.append(f'{where}: picture "{name}" is also used by shot {used[name]}')
            used.setdefault(name, i)
            found = find_picture(pictures, name) if pictures is not None else None
            if pictures is not None and found is None:
                errors.append(f'{where}: no picture "{name}" (looked for {name}.png, .jpg, .jpeg, .webp)')
            elif found is not None and key == 'picture':
                size = image_size(found)
                if size and min(size) < MIN_SIDE:
                    warnings.append(f'{where}: picture "{name}" is only {size[0]} x {size[1]}, so it will look '
                                    f'blurry; make it again at full size')
                elif size and (size[0] > size[1]) != (frame == '16:9') and size[0] != size[1]:
                    warnings.append(f'{where}: picture "{name}" is {size[0]} x {size[1]}, the wrong shape for a '
                                    f'{frame} film, so much of it will be cut off; make it again in {frame}')
    nums = [n for n in used if re.fullmatch(r'\d{3}', n)]
    if nums and len(nums) == len(used):
        seq = [int(n) for n in sorted(used, key=lambda n: used[n])]
        if seq != list(range(1, len(seq) + 1)):
            warnings.append('pictures are not numbered 001, 002, 003... in the order they appear')
    for k in sorted(unused):
        warnings.append(f'"extras": {k} is in no picture prompt')
    if pictures is None:
        errors += making
    else:
        warnings += [f'{m} (the pictures are already made, so this does not stop the film)' for m in making]
    if total:
        warnings.insert(0, f'{len(shots)} shots, {total} words, about {total / wps / 60:.1f} minutes '
                           f'(a picture every {total / wps / len(shots):.1f} s)')
    return errors, warnings


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    path = pathlib.Path(argv[0])
    pictures = None
    if '--pictures' in argv:
        pictures = argv[argv.index('--pictures') + 1]
    try:
        plan = json.loads(path.read_text(encoding='utf-8-sig'))
    except Exception as e:
        print(f'ERROR plan.json is not valid JSON: {e}')
        print('not ready')
        return 1
    errors, warnings = check(plan, pictures)
    for w in warnings:
        print('note   ' + w)
    for e in errors:
        print('ERROR  ' + e)
    print('ready' if not errors else f'not ready: {len(errors)} problem(s)')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
