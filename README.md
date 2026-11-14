# stills-render

Narrated films made of still pictures, FACT HUBZZZ style: a new picture for
every idea, each one appearing on the exact frame its first word is spoken.

Two layouts, chosen in the plan:

- **wide** (16:9): explainers of several minutes; each picture fills the
  frame, about one every 3 seconds; cards for chapter titles and punchlines.
- **short** (9:16): upright, every picture filling the whole frame and
  changing every 2 to 4 words. English or Hindi.

Subtitles are off; a plan can turn them on with `"captions": true` (words
appear as they are spoken, *marked* words yellow).

Voices: Kokoro (free, on the runner) for English; Azure neural voices for
Hindi (`hi-IN-MadhurNeural`), which need the secrets `AZURE_SPEECH_KEY` and
`AZURE_SPEECH_REGION`.

## How a film is made

1. **ChatGPT** writes the script and splits it into shots of about 6 to 12
   words (about 3 seconds each). Every shot is either a **picture** (a Flow
   prompt) or a **card** (a short line in capitals, drawn by the engine,
   with an optional small doodle). See `docs/chatgpt/`.
2. **Google Flow** makes the pictures, named by shot number: `001.png`, `002.png`…
3. The **upload page** sends `plan.json` and the pictures in one ZIP, as a
   release tagged `story-<slug>`, and runs **Make a film**.
4. **GitHub** speaks the narration with Kokoro (voice `am_michael`), takes
   the time of every word, starts each picture on its shot's first word,
   lays a credited music track under the voice, checks every cut in the
   finished film, and sends it to the Drive folder.

## The plan

```json
{
  "title": "How Did Sailors Find Their Way Before GPS?",
  "shots": [
    {"say": "It's midnight on the open sea, and the coast vanished three days ago.", "picture": "001"},
    {"say": "No map shows where you are.", "card": "No map.", "doodle": "002"},
    {"say": "The star that never moves.", "card": "The star that never moves.", "paragraph": true}
  ]
}
```

A full example: `examples/north-star-plan.json`. `python3 engine/check_plan.py plan.json --pictures DIR`
checks one.

## Pieces

| | |
|---|---|
| `engine/check_plan.py` | checks a plan, in plain words |
| `engine/voice.py` | speaks the narration, records every word's time |
| `engine/timing.py` | lines the spoken words up with the shots |
| `engine/frames.py` | fills the frame with a picture, or draws a card |
| `engine/typeset.py` | sets Hindi, English and emoji text for subtitles (when turned on) |
| `engine/render.py` | makes the film, each shot exactly as many frames as it is on screen |
| `engine/check_sync.py` | checks, in the finished film, that every cut and subtitle word is on its word |
| `engine/pick_music.py` | chooses a credited track and prints its credit |
| `music/` | tracks and their credits (CC BY only) |
| `locks/` | exact versions of everything a film installs |

## Needed once

Repository secrets: `UPLOAD_TOKEN` and `DRIVE_ENDPOINT_URL` for the Drive
delivery (the same values as in rose-render-test), and `AZURE_SPEECH_KEY` and
`AZURE_SPEECH_REGION` for Hindi films.

## Rules carried over from the Rose engine

- Every job runs on `ubuntu-24.04`, never `ubuntu-latest`.
- Every install comes from `locks/`.
- Pictures, ZIPs and films never go into the repository's history.
- Music only with a CC BY licence, and its credit is printed on every run.
