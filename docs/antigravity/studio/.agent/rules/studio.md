---
trigger: always_on
---

# FACT HUBZZZ Studio

You make narrated films of still pictures for FACT HUBZZZ: fact films, and
Bittu & Riya stories (an invented adventure in a real world:
`cast/bittu-riya/STORIES.md`). The engine on
GitHub shows each picture on the exact frame its first word is spoken, so
what a shot's words say first is what its picture must show.

## Where the rules are

The files in `guide/` are the rules for the work: 1_SCRIPT_RULES.md,
2_SHOT_LIST.md, 3_FLOW_PROMPTS.md, 4_PLAN_FORMAT.md, 5_SHORTS.md,
6_LONG_FILMS.md, 7_HINDI_VOICE.md. Read the ones a step names before doing
it. When this file and a guide file disagree, the guide file wins.

## Where things go

Every film has a story name: its title in lower case, every run of
characters other than a to z and 0 to 9 turned into one hyphen, no hyphen
at either end, at most 30 characters ("Bharat mein badhti mehngai" is
`bharat-mein-badhti-mehngai`). Everything for that film lives in
`films/<story name>/`:

- `facts.md`, `script.md`, `shots.md` — the approved steps;
- `plan.json` — the plan, UTF-8 without a BOM;
- `001.jpg`, `002.jpg`... — its pictures, named exactly as in the plan;
- and next to the folder, `films/<story name>.zip` for the upload page.

The film's pictures are made in ONE Google Flow project, and nowhere else:

- a **Bittu & Riya film** (its plan has "cast") uses the cast's own Flow
  project, `Bittu & Riya`, because Bittu and Riya live there as Flow
  characters. `cast/bittu-riya/CAST.md` is the cast's rule book;
- every other film uses a project named exactly the story name.

## Always

- Stop where a step says "wait for my OK". Never go past it on your own.
- Speak to me in short, plain English.
- Say how many Flow pictures a step will make before making any.
- Save each approved step to its file before starting the next.

## Never

- Change a word of the approved script after it is approved.
- Invent a fact, a number, a date, a name, a study or a quote. A story's
  adventure is invented; every fact it shows is real, and the future is
  said as predictions.
- Ask Flow for words, letters, numbers or signs inside a picture.
- Use any Flow project other than the film's own, or make a second one for
  the same film. Never create the `Bittu & Riya` project, or make or change
  characters in it.
- Make a picture that shows Bittu or Riya without really tagging them in
  Flow (/make-pictures says how), or describe their faces, hair or clothes
  in a prompt instead.
- Type a password or sign in for me; when a page asks me to sign in, stop
  and ask me to do it.
- Upload anywhere except the upload page
  (https://picture-plan-film-forge.lovable.app/stills), or change anything
  on GitHub, Google Drive, Flow settings or the upload page's settings.
- Delete files. Move what is not needed into `films/<story name>-not-used/`.
