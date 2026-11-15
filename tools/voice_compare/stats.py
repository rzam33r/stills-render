"""How many people use each Hindi-capable voice model, from Hugging Face.

    python stats.py OUT.json
"""
import json
import sys
import urllib.parse
import urllib.request

MODELS = ['hexgrad/Kokoro-82M', 'ResembleAI/chatterbox', 'ResembleAI/Chatterbox-Multilingual-hi',
          'ai4bharat/indic-parler-tts', 'SPRINGLab/Indic-Mio', 'ai4bharat/IndicF5', 'facebook/mms-tts-hin',
          'rhasspy/piper-voices', 'maya-research/veena-tts']
SEARCH = ['maya2', 'maya-2-native']
FIELDS = ['downloads', 'downloadsAllTime', 'likes', 'gated', 'cardData', 'lastModified', 'createdAt']


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'stills-render'}), timeout=30) as r:
        return json.loads(r.read())


def info(repo):
    q = '&'.join(f'expand[]={f}' for f in FIELDS)
    try:
        d = get(f'https://huggingface.co/api/models/{repo}?{q}')
    except Exception as e:  # noqa: BLE001
        return {'id': repo, 'error': str(e)}
    card = d.get('cardData') or {}
    return {'id': repo, 'downloads_last_30_days': d.get('downloads'), 'downloads_all_time': d.get('downloadsAllTime'),
            'likes': d.get('likes'), 'gated': d.get('gated'), 'licence': card.get('license'),
            'created': (d.get('createdAt') or '')[:10], 'updated': (d.get('lastModified') or '')[:10]}


rows = [info(m) for m in MODELS]
for term in SEARCH:
    try:
        found = get(f'https://huggingface.co/api/models?search={urllib.parse.quote(term)}&sort=downloads&limit=5')
    except Exception:  # noqa: BLE001
        found = []
    for m in found:
        if m['id'] not in {r['id'] for r in rows}:
            rows.append(info(m['id']))
rows.sort(key=lambda r: -(r.get('downloads_all_time') or r.get('downloads_last_30_days') or 0))
json.dump(rows, open(sys.argv[1], 'w'), indent=1)
for r in rows:
    print(r)
