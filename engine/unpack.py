"""Unpack an uploaded story ZIP into plan.json + pictures/.

    python3 engine/unpack.py STORY.zip OUT_DIR [--plan PLAN.json]

The ZIP holds the pictures the plan names, at the top or inside folders, and
usually plan.json too. A plan pasted on the upload page arrives as its own
file (--plan) and wins over one inside the ZIP.

Pictures are copied flat into OUT_DIR/pictures/. A picture keeps its name
when the plan uses that name. Otherwise a name that starts with a number is
matched by that number, so the files Google Flow and Flow Connect save
("1 - Medium shot of a man.jpg", "12_market.png") become 001.jpg and
012.png when the plan names "001" and "012". (On 15 Nov 2026 the first real
film's 43 Flow pictures were all named like that and none would have been
found.) Two files for the same picture are an error that names both.
Paths that try to leave the folder, and files that are not pictures or the
plan, are ignored.
"""
import json
import pathlib
import re
import shutil
import sys
import zipfile

PICTURE_EXT = {'.png', '.jpg', '.jpeg', '.webp'}
LEADING_NUMBER = re.compile(r'^(\d{1,4})(?!\d)')


def wanted_names(plan):
    """Every picture name the plan uses (pictures and doodles)."""
    names = set()
    for s in plan.get('shots') or []:
        if isinstance(s, dict):
            for key in ('picture', 'doodle'):
                if s.get(key) is not None:
                    names.add(str(s[key]))
    return names


def target_name(stem, wanted):
    """The plan name a picture file stands for, or its own stem."""
    if stem in wanted:
        return stem
    m = LEADING_NUMBER.match(stem.strip())
    if m:
        number = int(m.group(1))
        for name in wanted:
            if name.isdigit() and int(name) == number:
                return name
    return stem


def main(zip_path, out_dir, plan_path=None):
    out = pathlib.Path(out_dir)
    pics = out / 'pictures'
    if out.exists():
        shutil.rmtree(out)
    pics.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as z:
        entries, plans = [], []
        for info in z.infolist():
            if info.is_dir():
                continue
            parts = pathlib.PurePosixPath(info.filename.replace('\\', '/')).parts
            if not parts or '..' in parts or parts[0].startswith('/') or any(p.startswith('__MACOSX') for p in parts):
                continue
            name = parts[-1]
            if name.startswith('.'):
                continue
            suffix = pathlib.PurePosixPath(name).suffix.lower()
            if name.lower() == 'plan.json':
                plans.append((len(parts), info))
            elif suffix in PICTURE_EXT:
                entries.append((info, pathlib.PurePosixPath(name).stem, suffix))

        if plan_path:
            plan_bytes = pathlib.Path(plan_path).read_bytes()
            source = 'the pasted plan'
        elif plans:
            plans.sort(key=lambda p: p[0])
            plan_bytes = z.read(plans[0][1])
            source = 'plan.json in the ZIP'
        else:
            print('ERROR there is no plan: put plan.json in the ZIP or paste it on the upload page')
            return 1
        (out / 'plan.json').write_bytes(plan_bytes)
        try:
            wanted = wanted_names(json.loads(plan_bytes.decode('utf-8-sig')))
        except (ValueError, AttributeError):
            wanted = set()   # the plan check reports a broken plan

        taken, renamed = {}, 0
        for info, stem, suffix in entries:
            name = target_name(stem, wanted)
            if name in taken:
                print(f'ERROR two files for picture {name}: "{taken[name]}" and "{info.filename}"')
                return 1
            taken[name] = info.filename
            renamed += name != stem
            with z.open(info) as src, open(pics / f'{name}{suffix}', 'wb') as dst:
                shutil.copyfileobj(src, dst)
    print(f'unpacked {source} and {len(taken)} picture(s)'
          + (f', {renamed} matched by the number at the start of their name' if renamed else ''))
    return 0


if __name__ == '__main__':
    args = sys.argv[1:]
    plan = None
    if '--plan' in args:
        i = args.index('--plan')
        plan = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(args[0], args[1], plan))
