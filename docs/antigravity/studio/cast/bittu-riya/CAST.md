# Bittu & Riya — the cast

## Who they are

- **Bittu** (Hindi: बिट्टू) — never "Bitto". The cheerful, romantic trouble
  magnet whose plans go wrong.
- **Riya** (Hindi: रिया) — the clever, sarcastic one who keeps things under
  control, and sometimes starts the chaos herself.

`bittu.json` and `riya.json` hold their personalities, humour, expressions,
gestures and how they behave together. Use them for the story and the lines.
Their looks sections are for checking pictures, not for pasting into
prompts.

## Their looks live in Google Flow

- Flow project: **`Bittu & Riya`** (exactly), opened from its link:
  https://flow.google.com/project/983f2d4b-d432-439c-8283-587e8c9865c9
  Every picture of a Bittu & Riya film is made in this project and no
  other. Roshan opens it in his Chrome for Flow Connector. Never create
  this project, never make new characters in it, never change its
  characters.
- Its Characters: **`Bittu`** and **`Riya`**. They are the master looks:
  if this file, a JSON file or the old model sheets disagree with the Flow
  character, the Flow character wins. Each holds a full-body front view, so
  full-body pictures keep their trousers and shoes too.
- They wear their own clothes in every era and every place. Something worn
  on top is fine, written as "wearing a fur cape over his orange shirt" or
  "a silver visor over her eyes"; never a costume instead of their clothes.
- Other people are not Flow characters (yet): see "One-off people" in
  `STORIES.md`. A new regular character is added to the project only by
  Roshan.
- A picture that shows Bittu or Riya is made with each of them **cast as a
  Flow character**: Flow Connector's `"character_refs": ["Bittu"]` (or
  `["Riya"]`, `["Bittu", "Riya"]`), from the project open in Roshan's
  Chrome. Writing their name or "@Bittu" in the prompt does NOT keep their
  look.

## In plan.json

- `"cast": "Bittu & Riya"` at the top. Leave out `"character"`.
- Every picture that shows them lists them in `"who"`: `["Bittu"]`,
  `["Riya"]` or `["Bittu", "Riya"]`, exactly those spellings. A picture that
  shows neither has no `"who"`.
- Every character the prompt names is in `"who"`, and everyone in `"who"`
  is in the picture.
- One-off people (cavemen, robots…) go in `"extras"`: see `STORIES.md`.

## In a prompt

Do not describe their faces, hair or clothes: the Flow character carries
the look.
Write, in this order:

1. the shot type (wide, medium, close-up);
2. who does what, with which expression and gesture (from the JSON lists);
3. the place, the time of day, the light;
4. the one detail that matches the shot's words;
5. the keep-line of each person in `"who"`, word for word:
   - Bittu: `Bittu keeps his orange shirt open over his beige T-shirt, blue jeans, white sneakers and wristwatch.`
   - Riya: `Riya keeps her long loose wavy hair, never tied up, her red V-neck top, black pants, white sneakers, gold hoop earrings and gold pendant.`

   Small things (earrings, pendant, watch) often vanish in wide shots; that
   is normal. Judge them only in medium shots and close-ups.
6. the style block, as `"style"`, word for word (16:9 films: change
   "upright 9:16 frame" to "wide 16:9 frame"):

> 2D illustrated cartoon, clean bold dark outlines, warm vibrant pastel
> colours, soft simple cel shading, slightly exaggerated cartoon
> proportions, warm illustrated comic setting, upright 9:16 frame, no text,
> no letters, no numbers, no signs, no watermark.

Example (`"who": ["Bittu", "Riya"]`):

> Medium shot: Bittu kneels in a busy café holding out a small ring box,
> grinning with pride, while Riya stands over him with her arms crossed and
> one eyebrow raised, trying not to laugh; warm afternoon light, people at
> other tables turning to look. Bittu keeps his orange shirt open over his
> beige T-shirt, blue jeans, white sneakers and wristwatch. Riya keeps her
> long loose wavy hair, never tied up, her red V-neck top, black pants,
> white sneakers, gold hoop earrings and gold pendant. [style]
