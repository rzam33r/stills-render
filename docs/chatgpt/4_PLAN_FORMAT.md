# 4 — plan.json, exactly

Deliver one JSON object. Nothing before or after it in the file.

## Top level

| key | required | what |
|---|---|---|
| `title` | yes | the film's title, in English letters (Hinglish for a Hindi film); it names the film in Drive |
| `character` | yes, except Bittu & Riya films | the lead character's description, pasted into every prompt that shows them |
| `style` | yes | the style block, ending every picture prompt |
| `cast` | Bittu & Riya films | `"Bittu & Riya"`, the Flow project holding the characters; then leave out `character` |
| `shots` | yes | the shots, in order |
| `layout` | no | `"wide"` (default, normal pace) or `"short"` (fast pace, under 3 minutes, always upright) |
| `frame` | no | the shape: `"16:9"` (default) or `"9:16"` for an upright film at normal pace (file 6) |
| `language` | no | `"en"` (default) or `"hi"` |
| `captions` | no | leave out (no subtitles) |
| `voice` | no | leave out: English uses Kokoro's `"am_michael"`, Hindi Chatterbox's `"chatterbox-hi"` |
| `speed` | no | leave out (0.8 to 1.3; the default is 1.0) |

## A shot

| key | when | what |
|---|---|---|
| `say` | always | the exact words spoken while this shot is on screen |
| `picture` | picture shots | the picture's number: `"001"`, `"002"`… (the file will be 001.png) |
| `prompt` | picture shots | the Flow prompt for that picture |
| `who` | Bittu & Riya films | who is in the picture: `["Bittu"]`, `["Riya"]` or `["Bittu", "Riya"]`; left out when neither is |
| `card` | card shots | the short line the engine draws (at most 8 words) |
| `doodle` | optional, card shots | the doodle picture's number |
| `doodle_prompt` | with `doodle` | the Flow prompt for the doodle |
| `paragraph` | chapter titles | `true`: the voice takes a breath before this shot |

A shot has `picture` or `card`, never both. Numbers run 001, 002, 003… in
the order pictures and doodles first appear, with no gaps.

## The ZIP

`plan.json` plus every picture, named by its number: `001.png`, `002.png`…
(`.jpg` and `.webp` also work). WIDE: Flow pictures at 16:9, at least
1280 × 720. SHORT: upright 9:16, at least 720 × 1280.

## Complete example

```json
{
  "title": "How Did Sailors Find Their Way Before GPS?",
  "character": "a simple stick-figure man with a large round white head, two small black dot eyes, simple expressive eyebrows and mouth, a thin black stick body and limbs",
  "style": "Hand-drawn cartoon illustration, ink outlines with soft watercolour colouring, muted natural colours, simple clear composition, wide 16:9 frame, no text, no letters, no numbers, no signs, no watermark.",
  "shots": [
    {
      "say": "It's midnight on the open sea, and the coast vanished three days ago.",
      "picture": "001",
      "prompt": "Wide view of a small wooden sailing boat alone on a dark open sea at midnight, a simple stick-figure man with a large round white head, two small black dot eyes, simple expressive eyebrows and mouth, a thin black stick body and limbs, wearing a short rough linen tunic, standing at the bow looking out, uneasy; a few stars and a calm black horizon. Hand-drawn cartoon illustration, ink outlines with soft watercolour colouring, muted natural colours, simple clear composition, wide 16:9 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "No map shows where you are.",
      "card": "No map.",
      "doodle": "002",
      "doodle_prompt": "Minimal black ink doodle icon of a rolled paper map, crossed out, thick simple lines, centred on a pure white background, square, no text, no letters, no shading."
    },
    {
      "say": "No machine tells you which way is home.",
      "card": "No machine.",
      "doodle": "003",
      "doodle_prompt": "Minimal black ink doodle icon of a simple compass dial with a question mark, thick simple lines, centred on a pure white background, square, no text, no letters, no shading."
    },
    {
      "say": "One wrong guess, and the water runs out before the land appears.",
      "picture": "004",
      "prompt": "Close-up of a simple stick-figure man with a large round white head, two small black dot eyes, simple expressive eyebrows and mouth, a thin black stick body and limbs, wearing a short rough linen tunic, holding up an almost empty clay water jar inside the boat, worried; empty sea all around in grey dawn light. Hand-drawn cartoon illustration, ink outlines with soft watercolour colouring, muted natural colours, simple clear composition, wide 16:9 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "And yet, for thousands of years, sailors crossed oceans like this and came back.",
      "picture": "005",
      "prompt": "Wide view of three small wooden sailing boats crossing a wide ocean towards a distant green island, a simple stick-figure man with a large round white head, two small black dot eyes, simple expressive eyebrows and mouth, a thin black stick body and limbs, wearing a short rough linen tunic, waving from the nearest boat, hopeful; bright morning light. Hand-drawn cartoon illustration, ink outlines with soft watercolour colouring, muted natural colours, simple clear composition, wide 16:9 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "So how did they find their way with nothing but the sky?",
      "card": "Nothing but the sky.",
      "doodle": "006",
      "doodle_prompt": "Minimal black ink doodle icon of a night sky with a few stars and a small question mark, thick simple lines, centred on a pure white background, square, no text, no letters, no shading."
    },
    {
      "say": "The star that never moves.",
      "card": "The star that never moves.",
      "paragraph": true
    },
    {
      "say": "Every star you see at night slowly wheels across the sky.",
      "picture": "007",
      "prompt": "Wide view of a starry night sky over a calm sea with long curved star trails circling a single point, a simple stick-figure man with a large round white head, two small black dot eyes, simple expressive eyebrows and mouth, a thin black stick body and limbs, wearing a short rough linen tunic, lying on the deck of a small boat looking up, amazed. Hand-drawn cartoon illustration, ink outlines with soft watercolour colouring, muted natural colours, simple clear composition, wide 16:9 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "Except one. In the north, a single star barely moves at all.",
      "picture": "008",
      "prompt": "Medium shot of a simple stick-figure man with a large round white head, two small black dot eyes, simple expressive eyebrows and mouth, a thin black stick body and limbs, wearing a short rough linen tunic, pointing up at one bright star low in the northern night sky while the other stars are faint; small boat, calm sea. Hand-drawn cartoon illustration, ink outlines with soft watercolour colouring, muted natural colours, simple clear composition, wide 16:9 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "Find it, and you know which way is north.",
      "picture": "009",
      "prompt": "Medium shot of a simple stick-figure man with a large round white head, two small black dot eyes, simple expressive eyebrows and mouth, a thin black stick body and limbs, wearing a short rough linen tunic, steering the boat's wooden tiller with the bright north star straight ahead over the bow, confident; night sea. Hand-drawn cartoon illustration, ink outlines with soft watercolour colouring, muted natural colours, simple clear composition, wide 16:9 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "Measure how high it sits above the horizon, and you know how far north you are.",
      "picture": "010",
      "prompt": "Close-up of a simple stick-figure man with a large round white head, two small black dot eyes, simple expressive eyebrows and mouth, a thin black stick body and limbs, wearing a short rough linen tunic, holding out an arm with fingers stacked to measure the height of the bright north star above the sea horizon, concentrating; night. Hand-drawn cartoon illustration, ink outlines with soft watercolour colouring, muted natural colours, simple clear composition, wide 16:9 frame, no text, no letters, no numbers, no signs, no watermark."
    }
  ]
}
```
