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

Optional top level: "voice" (a Kokoro voice, default am_michael), "speed"
(0.8 to 1.3, default 1.0), "music" (a file in music/), "frame" ("16:9" or
"9:16").

    python3 engine/check_plan.py plan.json [--pictures DIR]

Prints every problem in plain words, then "ready" or "not ready". Exit 1
when not ready.
"""
import json
import pathlib
import re
import sys

WORD = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z]+)?")
PICTURE_EXT = ('.png', '.jpg', '.jpeg', '.webp')
VOICES = {'am_michael', 'am_adam', 'am_eric', 'am_liam', 'am_onyx', 'am_puck', 'am_fenrir',
          'af_heart', 'af_bella', 'af_nicole', 'af_sarah', 'af_sky', 'af_nova', 'af_river',
          'bm_george', 'bm_lewis', 'bm_daniel', 'bm_fable', 'bf_emma', 'bf_isabella', 'bf_alice', 'bf_lily'}
KEYS = {'say', 'picture', 'card', 'doodle', 'paragraph', 'note', 'prompt'}
TOP = {'title', 'shots', 'voice', 'speed', 'music', 'frame', 'character', 'style', 'description'}

# How fast the voice speaks, for the length estimate: words per second.
WPS = 2.75


def words(text):
    return WORD.findall(text or '')


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


def check(plan, pictures=None):
    """(errors, warnings) for a plan; pictures is the folder of pictures, or None."""
    errors, warnings = [], []
    if not isinstance(plan, dict):
        return ['plan.json must be an object with "title" and "shots"'], []
    for k in plan:
        if k not in TOP:
            warnings.append(f'unknown top-level key "{k}" is ignored')
    if not str(plan.get('title', '')).strip():
        errors.append('no "title"')
    shots = plan.get('shots')
    if not isinstance(shots, list) or not shots:
        return errors + ['no "shots" list'], warnings
    if plan.get('voice') is not None and plan['voice'] not in VOICES:
        errors.append(f'"voice": "{plan["voice"]}" is not a Kokoro voice this engine knows ({", ".join(sorted(VOICES))})')
    sp = plan.get('speed', 1.0)
    if not isinstance(sp, (int, float)) or not 0.8 <= sp <= 1.3:
        errors.append('"speed" must be a number from 0.8 to 1.3')
    if plan.get('frame', '16:9') not in ('16:9', '9:16'):
        errors.append('"frame" must be "16:9" or "9:16"')

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
        if len(w) > 24:
            errors.append(f'{where}: {len(w)} words is about {len(w) / WPS:.0f} s on one picture; split it (aim for 6 to 12 words)')
        elif len(w) > 16:
            warnings.append(f'{where}: {len(w)} words, about {len(w) / WPS:.0f} s on one picture; 6 to 12 keeps the pictures moving')
        elif len(w) < 3 and i != len(shots):
            warnings.append(f'{where}: {len(w)} word(s) is under a second on screen')
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
            if pictures is not None and find_picture(pictures, name) is None:
                errors.append(f'{where}: no picture "{name}" (looked for {name}.png, .jpg, .jpeg, .webp)')
    if total:
        warnings.insert(0, f'{len(shots)} shots, {total} words, about {total / WPS / 60:.1f} minutes '
                           f'(a picture every {total / WPS / len(shots):.1f} s)')
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
