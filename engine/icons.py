"""The icon library: 1,600+ Google Noto emoji pictures (Apache License 2.0),
looked up by everyday name and fetched when a film needs them.

    python3 engine/icons.py fetch PLAN.json ICON_DIR   # the icons a plan uses
    python3 engine/icons.py list [category]            # every name, by category

An icon is named in a plan by its name ("apple", "cut of meat", "world map",
"chart increasing"), by the emoji itself ("🍎"), or as "U+1F34E". icons.json
holds the names and the Noto commit the pictures come from; a picture is
downloaded once from GitHub into ICON_DIR and reused. Standard library only,
so the plan check can use it anywhere.
"""
import json
import os
import re
import pathlib
import shutil
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
INDEX = json.loads((HERE / 'icons.json').read_text(encoding='utf-8'))
NAMES = INDEX['names']
CODES = set(NAMES.values())
RAW = 'https://raw.githubusercontent.com/googlefonts/noto-emoji/{commit}/{path}'


def lookup(name):
    """The icon's code ("1f34e") for a name, emoji or "U+…", or None."""
    if not isinstance(name, str) or not name.strip():
        return None
    s = name.strip()
    if s.upper().startswith('U+'):
        code = '_'.join(p.lower() for p in re.split(r'(?i)u\+|[\s_]+', s) if p)
        return code if code in CODES else None
    if any(ord(ch) > 0x2000 for ch in s) and not any(ch.isalpha() and ord(ch) < 0x2000 for ch in s):
        code = '_'.join(f'{ord(ch):x}' for ch in s if ord(ch) != 0xFE0F)
        return code if code in CODES else None
    key = ' '.join(s.lower().replace('_', ' ').replace('-', ' ').split())
    return NAMES.get(key)


def icon_names(graphic):
    """Every icon name a "graphic" uses."""
    if not isinstance(graphic, dict):
        return []
    out = []
    for key in ('icon', 'from'):
        if isinstance(graphic.get(key), str):
            out.append(graphic[key])
    if isinstance(graphic.get('icons'), list):
        out += [n for n in graphic['icons'] if isinstance(n, str)]
    return out


# Icons a graphic adds by itself.
BUILT_IN = {'map': ['round pushpin']}


def fetch(codes, icon_dir):
    """Make sure each icon's picture is in icon_dir; returns {code: path}.
    NOTO_DIR, if set, is a local copy of the Noto repository to copy from."""
    icon_dir = pathlib.Path(icon_dir)
    icon_dir.mkdir(parents=True, exist_ok=True)
    local = os.environ.get('NOTO_DIR')
    out = {}
    for code in sorted(set(codes)):
        rel = INDEX['path'].format(code=code)
        dest = icon_dir / pathlib.Path(rel).name
        if not dest.exists():
            if local and (pathlib.Path(local) / rel).exists():
                shutil.copyfile(pathlib.Path(local) / rel, dest)
            else:
                url = RAW.format(commit=INDEX['commit'], path=rel)
                with urllib.request.urlopen(url, timeout=60) as r:
                    data = r.read()
                if data[:8] != b'\x89PNG\r\n\x1a\n':
                    raise SystemExit(f'icon {code}: {url} did not give a PNG')
                tmp = dest.with_suffix('.part')
                tmp.write_bytes(data)
                tmp.replace(dest)
        out[code] = dest
    return out


def plan_codes(plan):
    """The icon codes a plan's graphics need (unknown names are skipped)."""
    codes = set()
    for s in plan.get('shots') or []:
        g = s.get('graphic') if isinstance(s, dict) else None
        if not isinstance(g, dict):
            continue
        for n in icon_names(g) + BUILT_IN.get(g.get('kind'), []):
            c = lookup(n)
            if c:
                codes.add(c)
    return codes


def main(argv):
    if argv[:1] == ['fetch'] and len(argv) == 3:
        plan = json.loads(pathlib.Path(argv[1]).read_text(encoding='utf-8-sig'))
        got = fetch(plan_codes(plan), argv[2])
        print(f'{len(got)} icon(s) ready in {argv[2]}')
        return 0
    if argv[:1] == ['list']:
        want = ' '.join(argv[1:]).lower()
        for cat, names in INDEX['categories'].items():
            if not want or want in cat.lower():
                print(f'## {cat} ({len(names)})\n' + ', '.join(names) + '\n')
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
