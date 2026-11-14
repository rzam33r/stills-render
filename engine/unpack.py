"""Unpack an uploaded story ZIP into plan.json + pictures/.

    python3 engine/unpack.py STORY.zip OUT_DIR

The ZIP holds plan.json and the pictures it names (001.png, 002.jpg...),
at the top or inside one folder. Every picture is copied flat into
OUT_DIR/pictures/ under its own name; plan.json goes to OUT_DIR/plan.json.
Paths that try to leave the folder, and files that are not pictures or the
plan, are ignored. Two pictures with the same name are an error.
"""
import pathlib
import shutil
import sys
import zipfile

PICTURE_EXT = {'.png', '.jpg', '.jpeg', '.webp'}


def main(zip_path, out_dir):
    out = pathlib.Path(out_dir)
    pics = out / 'pictures'
    if out.exists():
        shutil.rmtree(out)
    pics.mkdir(parents=True)
    plans, names = [], {}
    with zipfile.ZipFile(zip_path) as z:
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
                if name in names:
                    print(f'ERROR two pictures named {name} ({names[name]} and {info.filename})')
                    return 1
                names[name] = info.filename
                with z.open(info) as src, open(pics / name, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
        if not plans:
            print('ERROR the ZIP has no plan.json')
            return 1
        plans.sort(key=lambda p: p[0])
        with z.open(plans[0][1]) as src, open(out / 'plan.json', 'wb') as dst:
            shutil.copyfileobj(src, dst)
    print(f'unpacked plan.json and {len(names)} picture(s)')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
