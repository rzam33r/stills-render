---
description: Make every picture of a film's plan.json in its Google Flow project, one by one, into the film's folder, with Bittu and Riya really tagged
---

# /make-pictures

For the film I name, or the one being worked on. Its plan is
`films/<story name>/plan.json`. Never change the plan.

1. **Check the Flow tools first**, before spending anything: can they
   (a) create or open a Flow project by name, (b) choose the picture shape,
   (c) save a picture where and as you choose. If (b) is not possible, stop
   and tell me. (On 16 Nov 2026 Roshan's Flow Connect could do (b) only.)
   For a Bittu & Riya film (the plan has "cast"), also (d): put a Flow
   character into the prompt as a **real tag**: the character's tag with its
   little picture in the prompt box, the same as typing @ and choosing it
   from Flow's list. The text "@Bittu" is not a tag. If Flow Connect cannot
   do (d), use the browser on the open Flow tab: click in the prompt box,
   type @, choose the character from the list Flow shows. If neither works,
   stop and tell me what happened. Never make a picture of Bittu or Riya
   without their tags.

2. **The Flow project.** Every picture of this film is made in one project
   and in no other:
   - a Bittu & Riya film: the project named exactly as the plan's "cast",
     `Bittu & Riya`. Open it from its link in `cast/bittu-riya/CAST.md`, in
     the browser (or with Flow Connect, if it can open a link). If Flow asks
     me to sign in, stop and ask me to. Never create the project: if the
     link does not open it, tell me: "In Flow, open the project
     `Bittu & Riya` and say ready." Wait for "ready". Then check its
     Characters include `Bittu` and `Riya`;
   - any other film: the project named exactly the story name. If the tools
     can create or open a project by name, do that (open it if it exists;
     never make a second one for the same film). If they cannot, tell me:
     "In Flow, create or open the project `<story name>` and say ready."
     Wait for "ready".
   - Either way: if the tools can tell which project is open, check its
     name is that name before the first picture and again every 25
     pictures; if they cannot, ask me to confirm the name when I say ready.

3. **List the pictures**, in shot order: each shot's "picture" with its
   "prompt", and each "doodle" with its "doodle_prompt". A name listed once
   is made once. Skip every name that already has a file in
   `films/<story name>/` (.png, .jpg, .jpeg or .webp): that is how an
   interrupted run carries on. Say "N to make, M already there".

4. **Make them one at a time**, in order:
   - a shot with "who" (Bittu & Riya films): first put each character it
     names into the prompt box as a real tag (step 1 (d)), in the order
     listed, then the prompt text. Tag no one who is not in "who". Before
     asking Flow for the picture, look at the prompt box: every name in
     "who" shows as a tag with its little picture, and nothing shows as
     plain "@Bittu" or "@Riya" text. If it is wrong, clear the box and try
     again; if it is wrong twice, stop and tell me. Never ask Flow for the
     picture with a tag missing;
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
   **Bittu & Riya films, first time:** if the film's folder had no pictures
   when this run started, stop after the first 2 pictures that show Bittu or
   Riya. Show them to me next to the cast's Flow characters and say, for each
   person in them: same face, same hair, same clothes: yes or no; in a
   medium shot or close-up also earrings and pendant (Riya), watch
   (Bittu). Wait for my OK before the rest.

5. **Check the folder.** Every picture name in the plan has exactly one file.
   Move any other image to `films/<story name>-not-used/`. Report: how many
   were made, how many were already there, how many were made with their
   tags checked (Bittu & Riya films), and each one that is missing with
   Flow's reason. If any is missing, stop: running /make-pictures again
   carries on from there.
