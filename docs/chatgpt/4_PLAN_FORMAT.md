# 4 — plan.json, exactly

Deliver one JSON object. Nothing before or after it in the file.

## Top level

| key | required | what |
|---|---|---|
| `title` | yes | the film's title, in English letters (Hinglish for a Hindi film); it names the film in Drive |
| `character` | yes, except Bittu & Riya films | the lead character's description, pasted into every prompt that shows them |
| `style` | yes | the style block, ending every picture prompt |
| `cast` | Bittu & Riya films | `"Bittu & Riya"`, the Flow project holding the characters; then leave out `character` |
| `extras` | Bittu & Riya films, if needed | each one-off person's short name and fixed look, pasted after their name in every prompt that shows them |
| `shots` | yes | the shots, in order |
| `youtube` | Bittu & Riya films | what the film says on YouTube: below |
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
| `graphic` | graphic shots | an animated graphic the engine draws: `8_GRAPHICS.md` |
| `card`, `doodle` | retired | old plans only; use a picture or a graphic |
| `paragraph` | chapter titles | `true`: the voice takes a breath before this shot |

A shot has `picture` or `graphic`, never both. Numbers run 001, 002, 003…
in the order pictures first appear, with no gaps.

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
      "picture": "002",
      "prompt": "Medium shot of a simple stick-figure man with a large round white head, two small black dot eyes, simple expressive eyebrows and mouth, a thin black stick body and limbs, wearing a short rough linen tunic, standing at an empty wooden table on the deck of a small boat by lantern light, holding up both open empty hands, puzzled; dark open sea at night. Hand-drawn cartoon illustration, ink outlines with soft watercolour colouring, muted natural colours, simple clear composition, wide 16:9 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "No machine tells you which way is home.",
      "picture": "003",
      "prompt": "Close-up of a simple stick-figure man with a large round white head, two small black dot eyes, simple expressive eyebrows and mouth, a thin black stick body and limbs, wearing a short rough linen tunic, kneeling on the bare wooden deck at night and searching an empty wooden chest with both hands, worried; a single lantern glowing beside him. Hand-drawn cartoon illustration, ink outlines with soft watercolour colouring, muted natural colours, simple clear composition, wide 16:9 frame, no text, no letters, no numbers, no signs, no watermark."
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
      "picture": "006",
      "prompt": "Medium shot of a simple stick-figure man with a large round white head, two small black dot eyes, simple expressive eyebrows and mouth, a thin black stick body and limbs, wearing a short rough linen tunic, sitting on the deck of a small wooden boat with one hand on his chin and the other on the deck, looking up at a sky full of stars, wondering; calm dark sea. Hand-drawn cartoon illustration, ink outlines with soft watercolour colouring, muted natural colours, simple clear composition, wide 16:9 frame, no text, no letters, no numbers, no signs, no watermark."
    },
    {
      "say": "The star that never moves.",
      "graphic": {
        "kind": "icons",
        "icons": [
          "glowing star"
        ]
      },
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

## The `youtube` section

A Bittu & Riya film is posted on the Bittu Ki Riya YouTube channel, publicly,
as soon as it is made. These are its words:

```json
"youtube": {
  "title": "Chaand Gayab Ho Gaya! 🌙 Kya Hota Agar...?",
  "caption": "Bittu ne Riya ko chaand gift kar diya... aur duniya ulti ho gayi 🌊",
  "question": "Aap Bittu ki jagah hote toh kya karte?",
  "hashtags": ["#KyaHotaAgar", "#Moon", "#Science"]
}
```

- `title`: Hinglish, at most 60 characters (phones cut longer ones), one
  emoji at most, the hook as a promise or a surprise. Not the plan's title
  word for word if a catchier one exists.
- `caption`: one line, the story's tease. It is the first line of the
  description and all most viewers read.
- `question`: one question the viewer can answer in a comment.
- `hashtags`: 2 to 4: the series tag first (`#KyaHotaAgar`,
  `#TimeMachine`, `#ScienceKaJadoo`, `#DesiItihaas`, `#DuniyaKeAjoobe`,
  `#SharirKeRaaz`, `#JanwarAurKudrat`, `#SpaceKiSair`,
  `#TyohaarAurRishtey`), then the film's topics. No spaces inside a
  hashtag. `#BittuKiRiya` and `#Shorts` are added by the engine; do not
  write them.
- `category`: leave out (Entertainment), or `"education"`.

The engine keeps YouTube's rules itself (at most 100 characters, at most 6
hashtags, the hashtags on the description's last line, not made for kids)
and the plan check says what it changed.
