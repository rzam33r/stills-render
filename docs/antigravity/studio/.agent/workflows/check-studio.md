---
description: Check a new or reinstalled FACT HUBZZZ Studio is ready, before making any film. Changes nothing and makes nothing.
---

# /check-studio

Check everything a film needs, and report. Do not make any picture, do not
upload anything, and do not create or change any file.

1. **The folder.** The open folder must hold `.agent/rules/studio.md`, the
   five workflows in `.agent/workflows/` (new-film, make-pictures,
   upload-film, fix-plan, check-studio), `guide/1_SCRIPT_RULES.md` to
   `guide/7_HINDI_VOICE.md`, `tools/check_plan.py` and `films/`. If `.agent`
   sits inside a subfolder instead, tell me to open that subfolder with
   File → Open Folder, and stop.

2. **The rules.** Read `.agent/rules/studio.md` and the seven guide files.
   Tell me in three lines: the shapes and lengths a film can have, which
   voice reads English and which reads Hindi, and what a plan must leave out.

3. **Flow Connect.** Look at the Flow tools you have, without using them, and
   answer yes or no to each: can you (a) create or open a Flow project by
   name, (b) choose the picture shape, 9:16 and 16:9, (c) choose where a
   downloaded picture is saved and what it is called. For any "no", say what
   /make-pictures would do instead.

4. **Python.** Run `python --version` (or `py --version` on Windows). Say
   whether the plan check in `tools/` can run. It is optional.

5. **The upload page.** Open https://picture-plan-film-forge.lovable.app/stills
   in the browser. Say whether I am signed in and whether the "Still-picture
   films" tab shows its upload box. If it asks me to sign in, ask me to do it
   in that window and wait; never type an email or a password yourself. Do
   not upload or press anything else.

6. **Report**, one line each: folder, rules, Flow Connect (a, b, c), Python,
   upload page — each "ready" or what to fix. Then give the command to start
   the first film:
   `/new-film <topic> — upright or wide, length, English or Hindi`
