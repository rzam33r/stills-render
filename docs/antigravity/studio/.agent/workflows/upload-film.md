---
description: Zip a finished film's plan.json and pictures and start the film on the upload page's Still-picture films tab
---

# /upload-film

For the film I name, or the one being worked on.

1. **Check it is complete.** `films/<story name>/plan.json` exists, and every
   picture and doodle it names has exactly one file in the folder. If not,
   say what is missing and stop (run /make-pictures).

2. **Make the ZIP** `films/<story name>.zip` holding the folder's plan.json
   and pictures and nothing else (not facts.md, script.md or shots.md),
   replacing an older ZIP of the same name. On Windows, in PowerShell:
   `Compress-Archive -Path "films\<story name>\plan.json","films\<story name>\*.jpg","films\<story name>\*.png","films\<story name>\*.webp" -DestinationPath "films\<story name>.zip" -Force`
   (leave out any extension the folder has no files of). Say its size in
   MB. Above 100 MB, add: "Uploads this big have not been tried on the
   upload page yet."

3. **Open the upload page** in the browser:
   https://picture-plan-film-forge.lovable.app/stills
   If it asks me to sign in, stop and ask me to sign in in that window, and
   wait until I say I have. Never type an email or a password yourself.

4. **Upload.** On the "Still-picture films" tab, choose
   `films/<story name>.zip` in the ZIP upload. If the page has a box for
   pasting a plan, leave it empty: the plan is inside the ZIP. Wait for the
   page's check.
   - If it lists problems, copy them exactly, stop, and show them to me
     (then /fix-plan).
   - If it shows its notes (shots, words, seconds, shape, language, voice),
     check they match the plan and tell me.
   If the browser cannot attach the file, stop and give me the ZIP's full
   path so I can upload it myself.

5. **Start the film** with the page's button that starts it (for example
   "Make the film"), once. Never press it twice for the same ZIP.

6. **Watch it** until the last step says "Sent to Google Drive" or a step
   turns red: every minute for an English film, every 5 minutes for a Hindi
   one (its voice takes about 12 minutes per minute of narration, up to 3
   hours for a long film; the page says how long). Tell me the result and the "Open the
   GitHub run" link. If a step failed, give its name and the message the
   page shows. Do nothing else on the page.
