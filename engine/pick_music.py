"""Choose the music bed for a film and say how to credit it.

    python3 engine/pick_music.py plan.json SEED

Prints the chosen file's path (or nothing when there is no music). Only a
track listed with a credit in music/credits.json is ever chosen: these
tracks are free only with that credit in the video's description. The plan
may name one with "music": "file.mp3"; otherwise the seed (the run number)
picks one, so the same run always gets the same track. When it runs in
GitHub, the credit is written at the top of the run's page.
"""
import json
import os
import pathlib
import random
import sys

MUSIC = pathlib.Path(__file__).resolve().parent.parent / 'music'


def pick(plan, seed):
    try:
        credits = json.loads((MUSIC / 'credits.json').read_text())
    except Exception:
        return None, None
    beds = sorted(n for n in credits if (MUSIC / n).is_file())
    if not beds:
        return None, None
    named = plan.get('music')
    if named and named not in beds:
        print(f'plan asks for music "{named}", which is not in music/ with a credit; choosing another', file=sys.stderr)
    choice = named if named in beds else random.Random(str(seed)).choice(beds)
    return MUSIC / choice, credits[choice]


def main(plan_path, seed):
    plan = json.loads(pathlib.Path(plan_path).read_text(encoding='utf-8-sig'))
    path, credit = pick(plan, seed)
    if not path:
        return 0
    print(path)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a') as f:
            f.write('## Music credit -- paste this into the YouTube description\n\n'
                    f"```\n{credit['credit']}\n```\n\n"
                    f'Track: `{path.name}`. Free, even monetised, only with this credit in the description.\n\n')
    print(f"music: {path.name} -- {credit['credit']}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ''))
