---
description: Zip a finished film's plan.json and pictures and start the film on the upload page's Still-picture films tab
---

# /upload-film

For the film I name, or the one being worked on.

1. **Check it is complete.** `films/<story name>/plan.json` exists, and every
   picture and doodle it names has exactly one file in the folder. If not,
   say what is missing and stop (run /make-pictures). If Python is
   installed, run `python tools/check_plan.py films/<story name>/plan.json
   --pictures films/<story name>`: a picture it calls blurry or the wrong
   shape is made again first (/make-pictures, after moving that file to
   `films/<story name>-not-used/`).

2. **Make the ZIP** `films/<story name>.zip` holding the folder's plan.json
   and pictures and nothing else (not facts.md, script.md or shots.md),
   replacing an older ZIP of the same name. On Windows, in PowerShell:
   `Compress-Archive -Path "films\<story name>\plan.json","films\<story name>\*.jpg","films\<story name>\*.png","films\<story name>\*.webp" -DestinationPath "films\<story name>.zip" -Force`
   (leave out any extension the folder has no files of). Wait until the
   command has finished and the ZIP's size is the same twice, 3 seconds
   apart. Say its size in MB. Above 100 MB, add: "Uploads this big have not
   been tried on the upload page yet."
   From here until the film has started, never re-make, move, rename or
   delete the ZIP or the films folder: the page keeps a link to the file, and
   a changed file cannot be read ("Failed while reading the ZIP", 16 Nov
   2026).

3. **Open the upload page** in the browser:
   https://picture-plan-film-forge.lovable.app/stills
   If it asks me to sign in, stop and ask me to sign in in that window, and
   wait until I say I have. Never type an email or a password yourself.

4. **Upload.** On the "Still-picture films" tab, choose the ZIP in the ZIP
   upload by its full path (for example
   `C:\Users\<you>\Documents\FACT HUBZZZ Studio\films\<story name>.zip`),
   and check the page shows that file's name. If the page has a box for
   pasting a plan, leave it empty: the plan is inside the ZIP. Wait for the
   page's check.
   - If it lists problems, copy them exactly, stop, and show them to me
     (then /fix-plan).
   - If it shows its notes (shots, words, seconds, shape, language, voice),
     check they match the plan and tell me.
   If the browser cannot attach the file, stop and give me the ZIP's full
   path so I can upload it myself.
   If the page says "Failed while reading the ZIP" or that the ZIP changed,
   check the ZIP still exists with the same size, choose it again once and
   carry on. If it happens again, stop and give me the page's error details.

5. **Start the film** with the page's button that starts it (for example
   "Make the film"), once. Never press it twice for the same ZIP.

6. **Watch it** until the last step says "Sent to Google Drive" or a step
   turns red: every minute for an English film, every 5 minutes for a Hindi
   one (its voice takes about 12 minutes per minute of narration, up to 3
   hours for a long film; the page says how long). Tell me the result and the "Open the
   GitHub run" link. If a step failed, give its name and the message the
   page shows. Do nothing else on the page.

7. **YouTube.** A Bittu & Riya film is also posted on the Bittu Ki Riya
   YouTube channel, publicly, a few minutes after it reaches Drive, with
   the plan's "youtube" words. Tell me to check it in YouTube Studio
   (https://studio.youtube.com/channel/UCBJBFuwimmZdoB5DXbRT7kg/content)
   and delete it there if anything is wrong. Never open YouTube Studio or
   change anything on YouTube yourself.
