# Bittu & Riya stories

A story is an **invented adventure in a real world**: romcom, couple drama,
comedy, sci-fi, time travel, fantasy, in any mix that makes it gripping.
The adventure is made up; everything it shows about the real world is true.
Bittu among stone-age people sees how they really made fire and tools; in
the year 2600, what Bittu and Riya see is what scientists actually predict,
said as a prediction. The viewer laughs and learns one true thing after
another.

Each film stands alone, like a sitcom: nothing carries over from another
film, and nobody needs to have seen one before. Bittu, Riya, both, or
neither appear in a scene as the story needs.

`CAST.md` (next to this file) says how their pictures are made. These
steps replace /new-film steps 1 to 6; then /new-film steps 7 and 8 make the
pictures and upload the film. Wait for my OK wherever a step says so.

## 1. Format

Take from my one-liner, or ask:

- **Length:** 90 seconds, 3, 6, 9, 12 or 15 minutes.
- **Shape:** upright 9:16 or wide 16:9.
- **Language:** English or Hindi.
- **Pace:** normal (a picture every 3 to 5 seconds), unless my one-liner
  says "fast". Fast is only for 90 seconds and 3 minutes, and always
  upright: `guide/5_SHORTS.md`.

Then say in one line how big the film is, from this table, and wait for my
OK.

| length | English words | Hindi words | Flow pictures (normal pace) |
|---|---|---|---|
| 90 seconds | about 250 | about 300 | 25 to 30 |
| 3 minutes | about 500 | about 600 | 40 to 55 |
| 6 minutes | about 1,000 | about 1,200 | 75 to 100 |
| 9 minutes | about 1,500 | about 1,800 | 110 to 150 |
| 12 minutes | about 2,000 | about 2,400 | 150 to 200 |
| 15 minutes | about 2,500 | about 3,000 | 190 to 250 |

## 2. Three pitches

Three different stories from my one-liner, each in a few lines:

- title (English letters; Hinglish for a Hindi film);
- cast: Bittu, Riya or both, and any one-off people;
- genre mix;
- the setup in one line, what goes wrong, the twist, the ending;
- the 2 to 4 real facts it shows (or predictions, for the future).

Make the three differ in genre mix and twist, not just in details. Wait for
my choice. I may mix them.

## 3. Facts

The real-world facts the story shows: at least 3, about one a minute (for 6
minutes and more, listed per act). Check every one with a web search and
give how sure it is (well established / widely believed / debated) and one
source link. Anything about the future is a prediction: say who predicts it
and give the source. Drop what you cannot source. Save to
`films/<story name>/facts.md`. Wait for my OK.

## 4. Script

For 6 minutes and more, first the acts: 3 to 5 minutes each, each with its
own small goal and a pull into the next. Wait for my OK, then write one act
at a time, waiting for my OK after each. Under 6 minutes, write it whole.
Save to `films/<story name>/script.md`.

- **The first line drops the viewer into the moment**: Bittu wakes up in a
  cave; Riya's phone says the year is 2600. Never a greeting, never "once
  upon a time".
- **Shape:** hook → who and where, quickly → the plan or wish → it goes
  wrong → bigger trouble → the twist → the payoff. End on a punchline or a
  warm line the viewer will repeat, then stop.
- **One narrator**, third person, the same tense throughout. Bittu's and
  Riya's lines are told by the narrator ("Riya rolled her eyes: Bittu,
  that is a mammoth."), short and in character (`bittu.json`,
  `riya.json`).
- **Facts live inside the action:** Bittu tries to light a fire with a
  lighter that does not exist yet, then watches how it is really done.
  One fact at a time, never a lecture. Future facts are said as
  predictions ("scientists expect…").
- **Laugh often:** a funny moment every 20 to 30 seconds: exaggerated
  reactions, misunderstandings, modern Bittu against the era.
- **Heart:** when both are in it, one warm moment between them. Teasing and
  jealousy stay playful, never cruel.
- **Family-friendly:** romance is looks, hugs and holding hands; no gore,
  no swearing, no drinking or smoking.
- Hindi: `guide/7_HINDI_VOICE.md`. Their names are बिट्टू and रिया.

## 5. Shots

Split the approved script by `guide/2_SHOT_LIST.md` without changing a
word: 6 to 12 words a shot under 3 minutes, 8 to 14 from 3 minutes on
(fast pace: `guide/5_SHORTS.md`). Cards are rare: at most one shot in ten,
for a fact's number or the final line. Show a numbered table: number, words
spoken, picture or card, who is in it (Bittu, Riya, one-off people), what
it shows. Save to `films/<story name>/shots.md`. Wait for my OK.

## 6. plan.json

Write every prompt by `CAST.md`, then `films/<story name>/plan.json` by
`guide/4_PLAN_FORMAT.md`:

- `"cast": "Bittu & Riya"`, no `"character"`;
- `"layout": "wide"` and `"frame"` `"9:16"` or `"16:9"` (fast pace:
  `"layout": "short"`);
- `"who"` on every picture showing Bittu or Riya;
- `"extras"` for the one-off people (below);
- `"style"`: the style block from `CAST.md`, with the film's frame.

Then report this checklist, each line done or not:

- words in all "say" fields = words in the approved script (both counts);
- every picture has a prompt ending with the style block, and none asks
  for text;
- every picture showing Bittu or Riya lists them in "who", and its prompt
  has their keep-line and does not describe their faces, hair or clothes;
- every one-off person's description appears word for word in every
  prompt that shows them;
- "title" in English letters; "voice" and "speed" left out;
- Hindi: the checks at the end of `guide/7_HINDI_VOICE.md`.

If Python is installed, run
`python tools/check_plan.py films/<story name>/plan.json`. Fix every error,
and every warning about a keep-line or a one-off person. Then say how many
pictures Flow will make and wait for my OK.

## One-off people

Cavemen, robots, Riya's boss: anyone who is not Bittu or Riya. Each one who
appears in more than one picture gets a short name and a fixed look in
`"extras"`:

`"extras": {"Ugg": "a tall stone-age man with a bushy black beard, wild black hair, a brown fur wrap and a bone necklace"}`

Every prompt that shows them names them followed by that look, word for
word ("Ugg, a tall stone-age man with…"), so they look the same in every
picture. Never two looks for one person. A crowd or someone seen once
needs no entry. Nobody becomes a Flow character except by Roshan.
