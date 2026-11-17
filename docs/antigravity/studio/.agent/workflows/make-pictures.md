---
description: Make every picture of a film's plan.json with Flow Connector in its Google Flow project, one by one, into the film's folder, with Bittu and Riya cast as Flow characters
---

# /make-pictures

For the film I name, or the one being worked on. Its plan is
`films/<story name>/plan.json`. Never change the plan.

**Pictures are made only with Flow Connector** (its tools `flow_status`,
`flow_generate`, `flow_get_job`, `flow_list_jobs`), in the Flow tab open in
my Chrome. Never use your own browser for Flow: it is far slower, and your
browser is only for the upload page. (17 Nov 2026: Flow Connector cast
Bittu from the project with `character_refs` and made a 768 × 1376 picture.)

1. **Check Flow Connector first**, before spending anything: call
   `flow_status`. If it is not connected, or says the Flow tab is closed,
   tell me and stop. If it says a daily allowance is used up, tell me and
   stop.

2. **The Flow project.** Every picture of this film is made in one project
   and in no other. Flow Connector makes pictures in the project open in my
   Chrome, so tell me which one to open, and wait for "ready":
   - a Bittu & Riya film: "In Chrome, open the `Bittu & Riya` project from
     its link, keep the tab open and visible, and say ready":
     https://flow.google.com/project/983f2d4b-d432-439c-8283-587e8c9865c9
     (the link is in `cast/bittu-riya/CAST.md`). Never create the project.
     If Flow asks me to sign in, I do it myself;
   - any other film: "In Chrome, create or open the Flow project
     `<story name>`, keep the tab open and visible, and say ready". Never a
     second project for the same film.
   - Either way: if `flow_status` tells which project is open, check its
     name before the first picture and again every 25 pictures; if it does
     not, ask me to confirm the name when I say ready.

3. **List the pictures**, in shot order: each shot's "picture" with its
   "prompt", and each "doodle" with its "doodle_prompt". A name listed once
   is made once. Skip every name that already has a file in
   `films/<story name>/` (.png, .jpg, .jpeg or .webp): that is how an
   interrupted run carries on. Say "N to make, M already there".

4. **Make them one at a time**, in order, each with one `flow_generate`
   call:
   - `"mode": "flow-text-to-image"`;
   - `"prompt"`: the prompt text exactly as written: never shorten,
     translate, reword or add to it;
   - `"aspect_ratio"`: `"9:16"` when the plan's "layout" is "short" or its
     "frame" is "9:16", otherwise `"16:9"`; doodles `"1:1"`;
   - `"character_refs"`: a shot with "who" (Bittu & Riya films) gets exactly
     its "who" list, in that order, like `["Bittu", "Riya"]`. A shot
     without "who" gets none. Never make a picture of Bittu or Riya
     without them in `"character_refs"`: writing their name or "@Bittu" in
     the prompt does not keep their look. If Flow Connector refuses a
     character name, stop and tell me;
   - `"image_model"`: `"nano-banana-pro"` for every picture of the film
     (the model the Flow characters were made with), unless I said
     another. Never change models in the middle of a film;
   - `"outputs": 1`;
   - `"folder"`: the story name, so its downloads land together in
     Chrome's download folder under `<story name>/`.
   Then wait with `flow_get_job` until it is finished and downloaded. Take
   the downloaded file's path from the job. If the job does not give it,
   take the newest image in that download folder that appeared after the
   request, once its size stays the same for 2 seconds (no `.crdownload`
   or `.tmp` file left); never a file that was there before. Move it (do
   not copy) to `films/<story name>/<name>.<its own extension>`: `001.jpg`,
   `002.jpg`... never `1 - Medium shot of a man.jpg`, never a second copy.
   Any other new image for the same request goes to
   `films/<story name>-not-used/`.
   If Flow fails or refuses, try once more; if it fails again, note the
   name and Flow's message and go on. If Flow Connector says the allowance
   is used up, stop and say how many are done: running /make-pictures
   again later carries on.
   Every 25 pictures, say how many are done.
   **Bittu & Riya films, first time:** if the film's folder had no pictures
   when this run started, stop after the first 2 pictures that show Bittu or
   Riya. Show them to me next to the cast's Flow characters and say, for each
   person in them: same face, same hair, same clothes: yes or no; in a
   medium shot or close-up also earrings and pendant (Riya), watch
   (Bittu). Also say each one's file (`films/<story name>/001.jpg`…) and
   its width × height (taller than wide for 9:16, wider than tall for
   16:9), read from the file itself. Wait for my OK before the rest.

5. **Check the folder.** Every picture name in the plan has exactly one file.
   Move any other image to `films/<story name>-not-used/`. Report: how many
   were made, how many were already there, how many were cast with
   `character_refs` (Bittu & Riya films), and each one that is missing with
   Flow's reason. If any is missing, stop: running /make-pictures again
   carries on from there.
