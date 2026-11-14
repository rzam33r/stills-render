"""The music a film may use, and the credit each track needs.

Every track in music/ is free only on condition that the artist is credited
in the video's description. The render picks only tracks listed in
music/credits.json and prints that credit at the top of the run's page.
This fails if:

  - a track is in music/ with no credit, or a credit has no track;
  - a credit line does not name the track, the artist and the licence;
  - a licence is not plain attribution (CC BY). ShareAlike makes the whole
    film share-alike, NonCommercial forbids a monetised channel, and
    NoDerivatives forbids putting it under a picture at all;
  - the music picker stops using only credited tracks or printing the credit.

    python3 tools/test_music.py
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MUSIC = ROOT / 'music'
bad = []

tracks = {p.name for p in MUSIC.iterdir() if p.suffix.lower() in ('.mp3', '.m4a', '.wav', '.ogg')}
credits = json.loads((MUSIC / 'credits.json').read_text())
for name in sorted(tracks - set(credits)):
    bad.append(f'{name}: in music/ with no credit in credits.json, so it would never be used')
for name in sorted(set(credits) - tracks):
    bad.append(f'{name}: has a credit but no file in music/')
for name, c in credits.items():
    for key in ('title', 'artist', 'license', 'source', 'credit'):
        if not c.get(key):
            bad.append(f'{name}: no "{key}"')
    if not re.fullmatch(r'CC BY [34]\.0', c.get('license', '')):
        bad.append(f'{name}: licence "{c.get("license")}" is not plain attribution (CC BY 3.0 or 4.0)')
    line = c.get('credit', '')
    if c.get('title', '').lower() not in line.lower():
        bad.append(f'{name}: credit line does not name the track')
    if c.get('artist', '').replace('-', '').replace(' ', '').lower() not in line.replace('-', '').replace(' ', '').lower():
        bad.append(f'{name}: credit line does not name the artist')
    if 'creativecommons.org/licenses/by/' not in line or re.search(r'by-(sa|nc|nd)', line):
        bad.append(f'{name}: credit line does not link the CC BY licence')
    if not re.fullmatch(r'[a-z0-9-]+\.mp3', name):
        bad.append(f'{name}: name it plainly, lower case with hyphens')

pick = (ROOT / 'engine' / 'pick_music.py').read_text()
if 'credits.json' not in pick or 'GITHUB_STEP_SUMMARY' not in pick:
    bad.append('pick_music.py does not choose only credited tracks and print the credit')

for b in bad:
    print('FAIL ' + b)
print(f'{len(credits)} tracks, each with its credit' if not bad else f'\n{len(bad)} failing')
sys.exit(1 if bad else 0)
