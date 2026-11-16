---
description: Make every picture of a film's plan.json in its own Google Flow project, one by one, into the film's folder
---

# /make-pictures

For the film I name, or the one being worked on. Its plan is
`films/<story name>/plan.json`. Never change the plan.

1. **Check the Flow tools first**, before spending anything: can they
   (a) create or open a Flow project by name, (b) choose the picture shape,
   (c) save a picture where and as you choose. If (b) is not possible, stop
   and tell me. (On 16 Nov 2026 Roshan's Flow Connect could do (b) only.)

2. **The Flow project** is named exactly the story name, and every picture
   of this film is made in it and in no other.
   - If the tools can create or open a project by name, do that (open it if
     it exists; never make a second one for the same film).
   - If they cannot, tell me: "In Flow, create or open the project
     `<story name>` and say ready." Wait for "ready". If the tools can tell
     which project is open, check its name is the story name before the first
     picture and again every 25 pictures; if they cannot, ask me to confirm
     the name when I say ready.

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
   - wait until it is finished and download it, then save it as
     `films/<story name>/<name>.<its own extension>`: `001.jpg`, `002.jpg`...
     never `1 - Medium shot of a man.jpg`, never a second copy.
     If the tools cannot choose where it is saved, it lands in the browser's
     download folder: note the time just before asking Flow for the picture,
     wait until the download has finished (no `.crdownload` or `.tmp` file
     left, and the size stays the same for 2 seconds), and take only an image
     file that appeared after that time. Move it (do not copy) to the film's
     folder under the picture's name. If more than one new image appeared,
     take the first and move the others to `films/<story name>-not-used/`.
     Never take a file that was there before the request;
   - if Flow fails or refuses, try once more; if it fails again, note the
     name and Flow's message and go on.
   Every 25 pictures, say how many are done.

5. **Check the folder.** Every picture name in the plan has exactly one file.
   Move any other image to `films/<story name>-not-used/`. Report: how many
   were made, how many were already there, and each one that is missing with
   Flow's reason. If any is missing, stop: running /make-pictures again
   carries on from there.
