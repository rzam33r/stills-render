---
description: Make every picture of a Stills Studio plan with Google Flow, save it next to plan.json, and pack both into one ZIP for the upload page
---

# /stills-pictures

You make the pictures for a still-picture film. The plan is the JSON that
ChatGPT (Stills Studio) wrote. If I have not pasted it with the command, ask
me to paste it and wait. Never change the plan.

1. **Read the plan.** It must be valid JSON with a "title" and a "shots"
   list. If not, tell me what is wrong and stop.

2. **Name the story** from the title: lower case; every run of characters
   other than a to z and 0 to 9 becomes one hyphen; no hyphen at the start or
   end; at most 30 characters (cut at 30, then drop a trailing hyphen).
   "Bharat mein badhti mehngai" becomes `bharat-mein-badhti-mehngai`. If that
   leaves nothing (a title in Hindi script), ask me for a short English name
   and wait.

3. **The folder** is `Downloads/<story name>`. Make it if it does not exist.
   If it exists, keep using it: that is how an interrupted run continues.

4. **Save plan.json first**, before any picture: the plan exactly as pasted,
   UTF-8 without a BOM, named exactly `plan.json` (not `plan.json.txt`).

5. **List the pictures**, in shot order: each shot's "picture" with its
   "prompt", and each "doodle" with its "doodle_prompt". A name already
   listed is made once.

6. **Make each picture** with Google Flow (the Flow Connect tools):
   - If the folder already has that name as .png, .jpg, .jpeg or .webp, skip
     it.
   - Use the prompt text exactly as written. Do not shorten, translate,
     reword or add to it.
   - Shape: 9:16 when the plan's "layout" is "short" or its "frame" is
     "9:16", otherwise 16:9. Doodles are square (1:1).
   - One image per name. If Flow gives several, keep only the first.
   - Save it as the plan's name with the image's own extension: `001.jpg`,
     `002.jpg`... Never `1 - Medium shot of a man.jpg`, never a second copy
     like `001 (1).jpg`.
   - If Flow fails or refuses, try once more. If it fails again, note the
     name and the reason, and go on to the next.

7. **Check the folder.** Every picture name in the plan has exactly one file.
   Move any other image out of the folder into `Downloads/<story name>-not-used`.

8. **If anything is missing**, do not make the ZIP. Tell me which names are
   missing and why, and that running /stills-pictures again with the same
   plan continues from there.

9. **If everything is there**, make `Downloads/<story name>.zip` holding the
   folder's files (plan.json and the pictures) and nothing else, replacing an
   older ZIP of the same name. On Windows:
   `Compress-Archive -Path "$HOME\Downloads\<story name>\*" -DestinationPath "$HOME\Downloads\<story name>.zip" -Force`

10. **Report** in a few lines: the ZIP's full path, how many pictures were
    made and how many were already there, and any picture Flow refused. If the
    plan's "voice" ends in "Neural", add: "The plan asks for an Azure voice;
    the film will use the Kokoro voice instead (hm_omega for Hindi). Update
    the ChatGPT project files."

Do not upload anything, do not open other websites, and do not edit
plan.json. Uploading is done on the upload page's "Still-picture films" tab.
