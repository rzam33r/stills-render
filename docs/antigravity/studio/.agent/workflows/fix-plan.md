---
description: Fix a film's plan.json from the problems the upload page or the GitHub run reported, then upload again
---

# /fix-plan

I paste the problems the upload page or the GitHub run reported.

1. Read `films/<story name>/plan.json` and the guide file each problem is
   about.
2. Fix only what the problems name. Keep every other line of the plan
   exactly as it is. Never change the words of a "say" unless a problem is
   about those words, and then tell me the old and the new words.
3. If a fix changes a picture's prompt or adds a picture, say which pictures
   must be made again; move their old files to
   `films/<story name>-not-used/` and run /make-pictures for them.
4. Show me what changed, line by line, and wait for my OK.
5. Run /upload-film.
