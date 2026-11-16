"""Join a ZIP the upload page sent in pieces, and prove it arrived whole.

    python3 engine/join_upload.py DIR OUT_DIR

The upload page sends a story's ZIP in pieces of 8 MB (NAME.zip.part001,
NAME.zip.part002, ...) and then NAME.zip.parts.json:

    {"name": "NAME.zip", "size": 36391208, "sha256": "...", "parts": 5}

Why: on 16 Nov 2026 a 35 MB ZIP sent in one request died in the page's
backend (a Supabase Edge Function: 256 MB memory, 2 s of CPU, 150 s) with
"Failed to fetch" and nothing uploaded. Small pieces stay far from every
limit at any film length, and a failed piece is sent again on its own.

DIR holds what was downloaded from the story's release. If it has a
parts.json, the pieces are joined in order into OUT_DIR/NAME.zip, and the
size and SHA-256 must match the page's, or nothing is unpacked. A ZIP sent
whole (older uploads) is copied as it is.
"""
import hashlib
import json
import pathlib
import re
import shutil
import sys


def main(src, out):
    src, out = pathlib.Path(src), pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    manifests = sorted(src.glob('*.parts.json'))
    if len(manifests) > 1:
        print(f'ERROR more than one parts list: {[m.name for m in manifests]}')
        return 1
    if not manifests:
        zips = sorted(src.glob('*.zip'))
        if len(zips) != 1:
            print(f'ERROR expected one ZIP or a parts list, found {[z.name for z in zips] or "nothing"}')
            return 1
        shutil.copyfile(zips[0], out / zips[0].name)
        print(f'one ZIP sent whole: {zips[0].name}')
        return 0
    m = json.loads(manifests[0].read_text(encoding='utf-8'))
    name = pathlib.PurePath(str(m['name'])).name
    if not name.lower().endswith('.zip'):
        print(f'ERROR the parts list names "{name}", not a ZIP')
        return 1
    n = int(m['parts'])
    found = {}
    for p in src.iterdir():
        mm = re.fullmatch(re.escape(name) + r'\.part(\d+)', p.name)
        if mm:
            found[int(mm.group(1))] = p
    missing = [i for i in range(1, n + 1) if i not in found]
    extra = sorted(i for i in found if i > n)
    if missing or extra:
        print(f'ERROR pieces missing: {missing}' + (f'; pieces that should not be there: {extra}' if extra else '')
              + '. Upload the story again.')
        return 1
    digest, size = hashlib.sha256(), 0
    target = out / name
    with open(target, 'wb') as f:
        for i in range(1, n + 1):
            data = found[i].read_bytes()
            digest.update(data)
            size += len(data)
            f.write(data)
    if size != int(m['size']) or digest.hexdigest() != str(m['sha256']).lower():
        target.unlink()
        print(f'ERROR the joined ZIP is not the one the page sent: {size} bytes, sha256 {digest.hexdigest()[:12]}..., '
              f'the page said {m["size"]} bytes, {str(m["sha256"])[:12]}... Upload the story again.')
        return 1
    print(f'joined {n} pieces into {name}: {size / 1e6:.1f} MB, fingerprint matches')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
