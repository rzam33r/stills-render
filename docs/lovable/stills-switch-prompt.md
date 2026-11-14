# Lovable prompt — add still-picture films to the upload page

Before pasting: on GitHub, open **Settings → Developer settings → Personal
access tokens → Fine-grained tokens**, open the token the upload page uses,
and under **Repository access** add **rzam33r/stills-render** (keep
rose-render-test). Its permissions stay **Contents: Read and write** and
**Actions: Read and write**. Save. The token's value does not change, so
nothing needs replacing in Lovable.

Copy everything below the line into Lovable's chat, in one message.

---

Add a second kind of film to this page: still-picture films, made by a
different GitHub repository. Everything that exists today stays exactly as
it is and keeps working for animated films.

1. **A switch at the top of the page**, before the upload: "Film type:
   Animated (Rose) | Still pictures". Default: Animated. Remember the last
   choice in this browser.

2. **When "Still pictures" is chosen:**
   - The ZIP holds `plan.json` and numbered pictures (`001.png`, `002.jpg`…),
     at the top or inside one folder. Do NOT cut picture sheets and do NOT
     run the animated-film plan check for it.
   - Read `plan.json` and the list of file names from the ZIP in the browser
     and run `checkStillsUpload(planText, fileNames)` (code below, add it
     unchanged). Show its `notes`. If `ok` is false, show every problem, a
     "Copy for ChatGPT" button that copies `forChatGPT`, and do not upload.
   - Show the list of shots from `plan.json` (number, the "say" words, and
     the picture thumbnail or the card's text) the same way animated films
     show their pictures.
   - Story name (slug): from `plan.title`, lower case, words joined with
     hyphens, only a-z, 0-9 and hyphens, at most 30 characters.
   - Shape: not a choice for the user. `"9:16"` if `plan.layout` is
     `"short"`, otherwise `plan.frame` if it is `"9:16"`, otherwise `"16:9"`.
     Show it as text ("Upright 9:16" / "Wide 16:9").
   - Logo: the same on/off switch as animated films.

3. **Build, for still pictures**, using the same GitHub token secret on the
   backend, but the repository **rzam33r/stills-render**:
   - Make the release `story-<slug>` if it does not exist (if GitHub answers
     422 already_exists, fetch it by tag and use it). If it already has an
     asset with the ZIP's name, delete that asset. Upload the original ZIP
     to it.
   - Then start the workflow `make-film.yml` on `main` with inputs (all as
     strings): `slug`, `deliver: "true"`, `frame` (from above), `logo`
     (`"true"`/`"false"`), `build: "b001"`, `ignore_plan_errors: "false"`,
     `keep_pictures: "false"`.
   - Progress, from that run's jobs, the same way as animated films:
     job `prepare` → "Plan checked and pictures uploaded"; job `voice` →
     "Voice recorded"; job `render` → "Video made"; job whose name contains
     `deliver` → "Sent to Google Drive". A failed job shows red with its
     name. Always show "Open the GitHub run" linking to the run's page
     (the run page also shows the music credit to paste into YouTube).

4. Never send the GitHub token to the browser. Log backend failures with
   the step and GitHub's message (never the token).

```javascript
// Checks a still-picture film's ZIP before upload. Same rules as
// engine/check_plan.py where it matters for the upload: plan.json is valid,
// it has shots, every shot has words and one picture or card, and every
// picture it names is in the ZIP.
// planText: the text of plan.json. fileNames: every file name in the ZIP.
// Returns { ok, problems: [..], notes: [..], forChatGPT }.
function checkStillsUpload(planText, fileNames) {
  const problems = [], notes = [];
  let plan;
  try { plan = JSON.parse(planText.replace(/^﻿/, '')); }
  catch (e) { return done([`plan.json is not valid JSON: ${e.message}`]); }
  if (!plan || typeof plan !== 'object' || !Array.isArray(plan.shots) || !plan.shots.length)
    return done(['plan.json has no "shots" list (is this a Rose plan? use the Rose switch)']);
  if (!String(plan.title || '').trim()) problems.push('plan.json has no "title"');
  const have = new Set();
  for (const f of fileNames) {
    const base = f.split('/').pop();
    const m = base.match(/^(.+)\.(png|jpe?g|webp)$/i);
    if (m) have.add(m[1]);
  }
  plan.shots.forEach((s, i) => {
    const n = i + 1;
    if (!s || typeof s !== 'object') { problems.push(`shot ${n}: not an object`); return; }
    if (!String(s.say || '').trim()) problems.push(`shot ${n}: no "say" words`);
    const pic = 'picture' in s, card = 'card' in s;
    if (pic === card) problems.push(`shot ${n}: needs exactly one of "picture" or "card"`);
    for (const key of ['picture', 'doodle']) {
      if (s[key] == null) continue;
      if (!have.has(String(s[key]))) problems.push(`shot ${n}: picture "${s[key]}" is not in the ZIP (looked for ${s[key]}.png, .jpg, .jpeg, .webp)`);
    }
  });
  const words = plan.shots.reduce((a, s) => a + String((s && s.say) || '').replace(/\*/g, ' ').split(/\s+/).filter(Boolean).length, 0);
  notes.push(`${plan.shots.length} shots, ${words} words, about ${(words / 2.75 / 60).toFixed(1)} minutes`);
  return done(problems);

  function done(p) {
    return { ok: p.length === 0, problems: p, notes,
      forChatGPT: p.length ? 'The plan checker rejected this plan. Fix only these, keep everything else, and send the corrected plan.json.\n' + p.map(x => '- ' + x).join('\n') : '' };
  }
}
if (typeof module !== 'undefined') module.exports = { checkStillsUpload };
```

Test it and tell me the result of each:
- Switch to Still pictures and upload a ZIP with `plan.json` and all its
  pictures: the shots list appears, Build uploads to rzam33r/stills-render
  and the progress steps move.
- Remove one picture from that ZIP: the page names the missing picture and
  does not upload.
- Upload an animated-film ZIP while "Still pictures" is chosen: it says
  there is no "shots" list.
- Switch back to Animated: everything works as before.
