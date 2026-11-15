---
description: Make every picture of a film's plan.json in its own Google Flow project, one by one, into the film's folder
---

# /make-pictures

For the film I name, or the one being worked on. Its plan is
`films/<story name>/plan.json`. Never change the plan.

1. **Check the Flow tools first**, before spending anything. Look at the Flow
   Connect tools you have and tell me in three lines whether they let you:
   (a) create or open a Flow project by name, (b) choose the picture shape
   (9:16 or 16:9), (c) choose where the downloaded file is saved and what it
   is called. If (a) is not possible, stop and tell me. If (b) or (c) is
   not possible, say what you will do instead and wait for my OK.

2. **The Flow project** is named exactly the story name. If a project with
   that name exists, open it and use it. Otherwise create it. Make every
   picture of this film in that project and no other. Never create a second
   project for the same film.

3. **List the pictures**, in shot order: each shot's "picture" with its
   "prompt", and each "doodle" with its "doodle_prompt". A name listed once
   is made once. Skip every name that already has a file in
   `films/<story name>/` (.png, .jpg, .jpeg or .webp): that is how an
   interrupted run carries on. Say "N to make, M already there".

4. **Make them one at a time**, in order:
   - the prompt text exactly as written: never shorten, translate, reword or
     add to it;
   - shape: 9:16 when the plan's "layout" is "short" or its "frame" is
     "9:16", otherwise 16:9; doodles square (1:1);
   - Flow's default image model, unless I said another;
   - one image per name: if Flow makes several, keep the first;
   - wait until it is finished, download it, and save it as
     `films/<story name>/<name>.<its own extension>`: `001.jpg`, `002.jpg`...
     never `1 - Medium shot of a man.jpg`, never a second copy;
   - if Flow fails or refuses, try once more; if it fails again, note the
     name and Flow's message and go on.
   Every 25 pictures, say how many are done.

5. **Check the folder.** Every picture name in the plan has exactly one file.
   Move any other image to `films/<story name>-not-used/`. Report: how many
   were made, how many were already there, and each one that is missing with
   Flow's reason. If any is missing, stop: running /make-pictures again
   carries on from there.
