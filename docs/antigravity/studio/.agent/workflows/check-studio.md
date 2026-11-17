---
description: Check a new or reinstalled FACT HUBZZZ Studio is ready, before making any film. Changes nothing and makes nothing.
---

# /check-studio

Check everything a film needs, and report. Do not make any picture, do not
upload anything, and do not create or change any file.

1. **The folder.** The open folder must hold `.agent/rules/studio.md`, the
   five workflows in `.agent/workflows/` (new-film, make-pictures,
   upload-film, fix-plan, check-studio), `guide/1_SCRIPT_RULES.md` to
   `guide/7_HINDI_VOICE.md`, `tools/check_plan.py`, `films/` and
   `cast/bittu-riya/` (CAST.md, bittu.json, riya.json). If `.agent`
   sits inside a subfolder instead, tell me to open that subfolder with
   File → Open Folder, and stop.

2. **The rules.** Read `.agent/rules/studio.md` and the seven guide files.
   Tell me in three lines: the shapes and lengths a film can have, which
   voice reads English and which reads Hindi, and what a plan must leave out.

3. **Flow Connector.** Call `flow_status` and read `flow_generate`'s
   options, without making anything. Answer yes or no: (a) it is connected
   to a Flow tab in my Chrome, (b) `flow_generate` takes `aspect_ratio`
   with 9:16 and 16:9, (c) it takes `character_refs`, (d) it takes
   `folder`. A "no" for (a) means: open Flow in Chrome and keep the
   tab open. A "no" for (b) or (c) means pictures cannot be made as
   /make-pictures says: tell me. Never use your own browser for Flow.

4. **Python.** Run `python --version` (or `py --version` on Windows). Say
   whether the plan check in `tools/` can run. It is optional.

5. **The upload page.** Open https://picture-plan-film-forge.lovable.app/stills
   in the browser. Say whether I am signed in and whether the "Still-picture
   films" tab shows its upload box. If it asks me to sign in, ask me to do it
   in that window and wait; never type an email or a password yourself. Do
   not upload or press anything else.

6. **Report**, one line each: folder, rules, Flow Connector (a, b, c, d), Python,
   upload page — each "ready" or what to fix. Then give the command to start
   the first film:
   `/new-film <topic> — upright or wide, length, English or Hindi`
