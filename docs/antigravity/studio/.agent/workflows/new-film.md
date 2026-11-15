---
description: Make a FACT HUBZZZ film from a topic, step by step: format, hooks, facts, script, shots, plan.json, then the pictures and the upload
---

# /new-film

Read `guide/1_SCRIPT_RULES.md`, `guide/2_SHOT_LIST.md`,
`guide/3_FLOW_PROMPTS.md` and `guide/4_PLAN_FORMAT.md` first. Read
`guide/5_SHORTS.md` for a film under 3 minutes, `guide/6_LONG_FILMS.md` for
3 minutes or more, and `guide/7_HINDI_VOICE.md` for a Hindi film.

1. **Topic and format.** If I gave no topic, ask for one. Ask the shape
   (upright 9:16 or wide 16:9), the length, and the language (English or
   Hindi), unless I said. Then say in one line how big the film is: words,
   pictures, and Flow generations (`guide/6_LONG_FILMS.md` has the table).
   A film under 3 minutes is upright at the fast pace (`guide/5_SHORTS.md`).
   Wait for my OK.

2. **Hooks.** Three possible opening lines, one sentence each, with a
   one-line promise for each. Wait for my choice.

3. **Facts.** The 8 to 15 facts the film rests on (for a film of 10 minutes
   or more: first the chapter outline from `guide/6_LONG_FILMS.md`, wait for
   my OK, then 5 to 10 facts per chapter). Check every fact with a web
   search and give each one: how sure it is (well established / widely
   believed / debated) and one source link. Drop or hedge anything you
   cannot find a good source for. Save to `films/<story name>/facts.md`.
   Wait for my OK.

4. **Script.** Write the narration by the guide files: whole for a film under
   10 minutes, one chapter at a time for a longer one (wait for my OK after
   each chapter). Plain paragraphs, no headings inside the narration. For
   Hindi, check it against the last section of `guide/7_HINDI_VOICE.md`
   before showing it. Save to `films/<story name>/script.md`. Wait for my OK
   or changes.

5. **Shots.** Split the approved script into shots by `guide/2_SHOT_LIST.md`
   without changing a word. Show a numbered table: number, words spoken,
   picture or card, what the picture shows. Save it to
   `films/<story name>/shots.md`. Wait for my OK.

6. **plan.json.** Write the Flow prompt for every picture and doodle by
   `guide/3_FLOW_PROMPTS.md`, then write `films/<story name>/plan.json` exactly
   as `guide/4_PLAN_FORMAT.md` describes. Then report this checklist, each
   line done or not:
   - words in all "say" fields = words in the approved script (both counts);
   - shots outside their word range (`guide/2_SHOT_LIST.md`, file 5 or 6);
   - cards: count and share of all shots;
   - pictures: count, numbered without gaps, each with a "prompt";
   - every prompt describes the lead character the same way and ends with
     the style block;
   - no prompt asks for text;
   - "title" in English letters; "voice" and "speed" left out;
   - Hindi: the checks at the end of `guide/7_HINDI_VOICE.md`.
   If Python is installed, also run
   `python tools/check_plan.py films/<story name>/plan.json` and show what it
   says; fix anything it calls an error.
   Then say how many pictures Flow will make and wait for my OK.

7. **Pictures.** Run /make-pictures for this film.

8. **Upload.** When every picture is there, run /upload-film for this film.

If I come back to a film later, read its folder first and carry on from the
first step whose file is missing.
