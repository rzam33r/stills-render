# 5 — SHORT films, and Hindi

A SHORT film is upright (9:16). Every picture fills the whole frame, with
no bands, no title and no subtitles, and changes every 2 to 4 words.
Everything in files 1 to 4 holds unless this file says otherwise.

## Length

- About 2.5 spoken words a second.
- Under 60 seconds: 40 to 140 words, 20 to 60 pictures.
- 1 to 3 minutes: 150 to 450 words, 60 to 180 pictures.

## The narration

- Start inside the idea: the first line is the question or the first step
  of a pattern, never a greeting.
- Build on a pattern the viewer can predict, then break it. Repeat one
  sentence shape three times with new subjects, and make the fourth line
  the turn ("The sun gives light to the leaf. The leaf gives food to the
  deer. The deer gives life to the forest. And what do we give?").
- One idea per line, said in the fewest words. Short lines, often without a
  verb.
- End on the turn or a one-line truth the viewer will repeat, then stop.
  No summary, no "like and subscribe" in films under a minute.

## Shots

- 1 to 5 words a shot. Change the picture every 2 to 4 words: on every new
  noun or action.
- Tell the story in steps: consecutive pictures can be the same place a
  moment later, or the same subject changing (a cub, then the same cub
  grown into a lion).
- Cards are rare in SHORT films. Use one only for the closing truth.

## Flow prompts for SHORT films

- Upright: end every prompt with a style block that says "tall upright 9:16
  frame", and make the pictures in Flow at 9:16.
- Compose for a phone held upright: one clear subject, in the middle of the
  frame, with room above and below.
- A bright, warm cartoon look reads best on a phone:

> Bright hand-drawn cartoon illustration, clean bold dark outlines, warm
> saturated colours, soft shading, simple detailed background, tall
> upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark.

## Hindi films

- `"language": "hi"`. The voice is Azure's Hindi voice `hi-IN-MadhurNeural`
  (male); `hi-IN-SwaraNeural` is a female voice.
- Write every `say` in Hindi script (Devanagari). Words people say in English
  ("value", "phone") may stay in English letters.
- Numbers in words, as a person says them ("बीस हज़ार").
- End sentences with "।" or a question mark.
- Flow prompts stay in English. Settings and people should fit the story:
  for an Indian audience, Indian villages, homes, streets and clothing.

## Complete SHORT example (English)

```json
{
  "title": "Where Does Rain Come From?",
  "layout": "short",
  "language": "en",
  "voice": "am_michael",
  "speed": 1.0,
  "character": "a cheerful cartoon boy of about ten with spiky black hair, round face, big expressive eyes, wearing a plain orange t-shirt and blue shorts",
  "style": "Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark.",
  "shots": [
    {
      "say": "A single drop",
      "picture": "001",
      "prompt": "Close-up of a single shining water drop rising from the surface of a blue sea, sunlight sparkling. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "leaves the sea,",
      "picture": "002",
      "prompt": "Wide view of a calm blue sea under a hot sun with faint wisps of mist rising from the water. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "rises as mist,",
      "picture": "003",
      "prompt": "Many tiny water drops floating upward as soft white mist over the sea, towards the sky. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "becomes a cloud,",
      "picture": "004",
      "prompt": "A big fluffy white cloud forming in a bright blue sky above the sea. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "and falls",
      "picture": "005",
      "prompt": "A dark grey rain cloud over green mountains, the first raindrops starting to fall. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "on the mountains.",
      "picture": "006",
      "prompt": "Rain falling on steep green mountains, a cheerful cartoon boy of about ten with spiky black hair, round face, big expressive eyes, wearing a plain orange t-shirt and blue shorts standing under a big leaf like an umbrella, smiling. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "It runs down as a river,",
      "picture": "007",
      "prompt": "A sparkling river winding down from the mountains through a green valley. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "waters the fields,",
      "picture": "008",
      "prompt": "Green rice fields being watered by a small canal from the river, a cheerful cartoon boy of about ten with spiky black hair, round face, big expressive eyes, wearing a plain orange t-shirt and blue shorts splashing barefoot in the water, laughing. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "and finds its way",
      "picture": "009",
      "prompt": "The river widening as it flows past a small village towards the coast. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "back to the sea.",
      "picture": "010",
      "prompt": "A river mouth meeting the open blue sea at sunset, waves gently rolling in. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "Water never runs out.",
      "card": "Water never runs out.",
      "doodle": "011",
      "doodle_prompt": "Minimal black ink doodle icon of a water drop with a circular arrow around it, thick simple lines, centred on a pure white background, square, no text, no letters, no shading."
    },
    {
      "say": "It only changes shape.",
      "picture": "012",
      "prompt": "a cheerful cartoon boy of about ten with spiky black hair, round face, big expressive eyes, wearing a plain orange t-shirt and blue shorts looking up in wonder at a sky with a cloud, a raindrop and a snowflake floating side by side. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    }
  ]
}
```

## Complete SHORT example (Hindi)

```json
{
  "title": "Ek boond ka safar",
  "layout": "short",
  "language": "hi",
  "voice": "hi-IN-MadhurNeural",
  "speed": 1.0,
  "character": "a cheerful cartoon boy of about ten with spiky black hair, round face, big expressive eyes, wearing a plain orange t-shirt and blue shorts",
  "style": "Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark.",
  "shots": [
    {
      "say": "समंदर से उठी",
      "picture": "001",
      "prompt": "Close-up of a single shining water drop rising from the surface of a blue sea, sunlight sparkling. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "एक बूंद,",
      "picture": "002",
      "prompt": "Wide view of a calm blue sea under a hot sun with faint wisps of mist rising from the water. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "बादल बनी,",
      "picture": "003",
      "prompt": "A big fluffy white cloud forming in a bright blue sky above the sea. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "पहाड़ों पर बरसी,",
      "picture": "004",
      "prompt": "Rain falling on steep green mountains, a cheerful cartoon boy of about ten with spiky black hair, round face, big expressive eyes, wearing a plain orange t-shirt and blue shorts standing under a big leaf like an umbrella, smiling. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "नदी बनकर बही,",
      "picture": "005",
      "prompt": "A sparkling river winding down from the mountains through a green valley. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "खेतों को सींचा,",
      "picture": "006",
      "prompt": "Green rice fields being watered by a small canal from the river, a cheerful cartoon boy of about ten with spiky black hair, round face, big expressive eyes, wearing a plain orange t-shirt and blue shorts splashing barefoot in the water, laughing. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "और फिर",
      "picture": "007",
      "prompt": "The river widening as it flows past a small village towards the coast. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "वापस समंदर में मिल गई।",
      "picture": "008",
      "prompt": "A river mouth meeting the open blue sea at sunset, waves gently rolling in. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "पानी कभी खत्म नहीं होता,",
      "card": "पानी कभी खत्म नहीं होता",
      "doodle": "009",
      "doodle_prompt": "Minimal black ink doodle icon of a water drop with a circular arrow around it, thick simple lines, centred on a pure white background, square, no text, no letters, no shading."
    },
    {
      "say": "बस रूप बदलता है।",
      "picture": "010",
      "prompt": "a cheerful cartoon boy of about ten with spiky black hair, round face, big expressive eyes, wearing a plain orange t-shirt and blue shorts looking up in wonder at a sky with a cloud, a raindrop and a snowflake floating side by side. Bright hand-drawn cartoon illustration, clean bold dark outlines, warm saturated colours, soft shading, simple detailed background, tall upright 9:16 frame, no text, no letters, no numbers, no signs, no watermark."
    }
  ]
}
```
