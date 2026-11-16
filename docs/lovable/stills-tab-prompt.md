# Lovable prompt — a separate "Still-picture films" tab

The GitHub token the upload page uses must reach **rzam33r/stills-render**
as well as rose-render-test (Settings → Developer settings → Fine-grained
tokens → Repository access). Its value does not change, so nothing needs
replacing in Lovable.

Copy everything below the line into Lovable's chat, in one message.

---

Add a second tab to this website for still-picture films, made by a
different GitHub repository. The animated-film page that exists today must
keep working exactly as it does now.

1. **Two tabs at the top of every page, after sign-in:** "Animated films"
   (today's page, unchanged, at its current address) and "Still-picture
   films" (new, at `/stills`). The current tab is highlighted. Opening
   `/stills` directly works, and both tabs need the same sign-in.

2. **One uploader, not two.** Do not copy today's upload code into the new
   tab. Turn the existing ZIP upload, GitHub release upload, workflow start,
   progress display and error reporting into shared pieces that take the
   film type as a setting, and have both tabs use them. A fix to uploading
   must fix both tabs at once.

3. **The backend chooses the repository, never the browser.** The browser
   sends only the film type, `"animated"` or `"stills"`. The backend maps it:
   - `animated` → `rzam33r/rose-render-test`, exactly as today;
   - `stills` → `rzam33r/stills-render`, workflow `make-film.yml` on `main`.
   Any other value is refused. Keep checking the signed-in user on every
   request, keep the GitHub token on the server only, and never log it.

4. **Wrong-tab guard on both tabs.** Add `filmKind(planText)` from the code
   below. When a ZIP is chosen, read its `plan.json` in the browser:
   - on "Animated films", if `filmKind` says `"stills"`, show "This is a
     still-picture film. Use the Still-picture films tab." and do not
     upload. Change nothing else on that tab;
   - on "Still-picture films", `checkStillsUpload` already refuses animated
     plans with the matching message.

5. **The Still-picture films tab:**
   - The ZIP holds the pictures, at the top or inside one folder, named
     `001.png`, `002.jpg`… or as Google Flow saves them (`1 - Medium shot of
     a man.jpg`). `plan.json` is pasted in a box or sits inside the ZIP. Do NOT cut picture sheets
     and do NOT run the animated-film plan check.
   - Run `checkStillsUpload(planText, fileNames)` (code below, add it
     unchanged) with the text of `plan.json` and every file name in the ZIP.
     Show every line of `notes`. If `ok` is false, list every problem, show a
     "Copy for ChatGPT" button that copies `forChatGPT`, and do not upload.
   - Show the shots from `plan.json`: number, the `say` words, and the
     picture's thumbnail or the card's text.
   - The story name is `slug` from the check's result. Shape (`frame`),
     language and voice also come from the result and are shown as text,
     not choices.
   - One switch: Logo on/off, the same as on the animated tab.
   - A "Make the film" button.

6. **Making a still-picture film** (backend, repository
   `rzam33r/stills-render`), using the shared upload code:
   - Make the release `story-<slug>` if it does not exist (if GitHub answers
     422 already_exists, fetch it by tag and use it). If it already has an
     asset with the ZIP's name, delete that asset. Upload the original ZIP.
   - Start `make-film.yml` on `main` with these inputs, all as strings:
     `slug`, `deliver: "true"`, `frame` (`"9:16"` or `"16:9"`), `logo`
     (`"true"`/`"false"`), `build: "b001"`, `ignore_plan_errors: "false"`,
     `keep_pictures: "false"`.
   - Progress from that run's jobs: `prepare` → "Plan checked and pictures
     uploaded"; `voice` → "Voice recorded"; `render` → "Video made"; the job
     whose name contains `deliver` → "Sent to Google Drive". A failed job
     shows red with its name and GitHub's message. Always show "Open the
     GitHub run", linking to the run's page (it also shows the music credit
     to paste into YouTube).

7. **Recent films on each tab.** If today's page lists recent builds, the
   new tab lists its own from `rzam33r/stills-render` (runs of
   `make-film.yml`) in the same way. Each tab shows only its own films.

```javascript
// Upload checks for the "Still-picture films" tab of the upload page.
// Same rules as engine/check_plan.py where they matter before uploading;
// GitHub runs the full check again in the "prepare" job.
//
// filmKind(planText) -> 'stills' | 'animated' | 'unknown'
//   Still-picture plans have a "shots" list, animated (Rose) plans a
//   "scenes" list. Both tabs call it so a ZIP dropped on the wrong tab is
//   stopped with a clear message instead of failing on GitHub.
//
// checkStillsUpload(planText, fileNames)
//   planText: the pasted plan, or the text of plan.json from the ZIP.
//   fileNames: every file name in the ZIP.
//   Returns { ok, problems: [..], notes: [..], forChatGPT, slug, frame,
//   language, voice }.

const STILLS_DEFAULT_VOICE = { en: 'am_michael', hi: 'chatterbox-hi' };

function parsePlan(planText) {
  return JSON.parse(String(planText).replace(/^﻿/, ''));
}

function filmKind(planText) {
  let plan;
  try { plan = parsePlan(planText); } catch (e) { return 'unknown'; }
  if (!plan || typeof plan !== 'object') return 'unknown';
  if (Array.isArray(plan.shots)) return 'stills';
  if (Array.isArray(plan.scenes)) return 'animated';
  return 'unknown';
}

function stillsSlug(title) {
  return String(title || '').toLowerCase().replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '').slice(0, 30).replace(/-+$/g, '');
}

function checkStillsUpload(planText, fileNames) {
  const problems = [], notes = [];
  // Problems with the ZIP itself (no plan, missing pictures, wrong tab) are
  // not ChatGPT's to fix; only plan problems go into forChatGPT. On 16 Nov
  // 2026 an empty ZIP showed "plan.json is not valid JSON: Unexpected end of
  // JSON input" with a "Copy for ChatGPT" button, though the plan was fine.
  const zipProblems = new Set();
  const zipProblem = (msg) => { zipProblems.add(msg); problems.push(msg); };
  let plan, slug = '';
  if (!String(planText == null ? '' : planText).replace(/^\uFEFF/, '').trim()) {
    const n = (fileNames || []).filter(f => /\.(png|jpe?g|webp)$/i.test(String(f))).length;
    zipProblem(`This ZIP has no plan.json, or it is empty (${n} picture${n === 1 ? '' : 's'} found). Check you chose the right ZIP: a film's ZIP holds plan.json and its pictures, usually tens of MB.`);
    return done(problems);
  }
  try { plan = parsePlan(planText); }
  catch (e) { return done([`plan.json is not valid JSON: ${e.message}`]); }
  if (!plan || typeof plan !== 'object') return done(['plan.json is not a plan']);
  if (!Array.isArray(plan.shots) && Array.isArray(plan.scenes)) {
    zipProblem('This is an animated (Rose) film. Use the "Animated films" tab.');
    return done(problems);
  }
  if (!Array.isArray(plan.shots) || !plan.shots.length)
    return done(['plan.json has no "shots" list']);
  if (!String(plan.title || '').trim()) problems.push('plan.json has no "title"');
  slug = stillsSlug(plan.title);
  if (!slug && String(plan.title || '').trim()) {
    const d = new Date(), two = n => String(n).padStart(2, '0');
    slug = `film-${d.getFullYear()}${two(d.getMonth() + 1)}${two(d.getDate())}-${two(d.getHours())}${two(d.getMinutes())}`;
    notes.push(`The title has no English letters, so this film is named ${slug}. Write titles in English letters (Hinglish is fine) to get a readable name.`);
  }

  const language = plan.language == null ? 'en' : plan.language;
  if (language !== 'en' && language !== 'hi') problems.push('"language" must be "en" or "hi"');
  const voice = plan.voice || STILLS_DEFAULT_VOICE[language] || 'am_michael';
  const hindiVoice = /^(hm_|hf_|hi-IN-|chatterbox-hi$)/.test(String(voice));
  if (/^[a-z]{2}-[A-Z]{2}-[A-Za-z]+Neural$/.test(String(voice)))
    notes.push(`${voice} is an Azure voice. Without the Azure key the film uses ${STILLS_DEFAULT_VOICE[language] || 'am_michael'} instead.`);
  if (language === 'hi' && !hindiVoice) problems.push(`a Hindi film needs a Hindi voice (leave "voice" out for Chatterbox), not "${voice}"`);
  if (language === 'en' && hindiVoice) problems.push(`"${voice}" is a Hindi voice; set "language": "hi" or choose an English voice`);

  // Same matching as engine/unpack.py: a file keeps its name when the plan
  // uses it; otherwise "1 - Medium shot of a man.jpg" (as Google Flow and
  // Flow Connect save them) stands for the plan's "001".
  const wanted = new Set();
  plan.shots.forEach(s => { if (s && typeof s === 'object') for (const k of ['picture', 'doodle']) if (s[k] != null) wanted.add(String(s[k])); });
  const have = new Map();
  for (const f of fileNames) {
    const base = String(f).split('/').pop();
    if (base.startsWith('.') || String(f).includes('__MACOSX')) continue;
    const m = base.match(/^(.+)\.(png|jpe?g|webp)$/i);
    if (!m) continue;
    let name = m[1];
    const lead = name.trim().match(/^(\d{1,4})(?!\d)/);
    if (!wanted.has(name) && lead) {
      for (const w of wanted) if (/^\d+$/.test(w) && Number(w) === Number(lead[1])) { name = w; break; }
    }
    if (have.has(name)) zipProblem(`two files for picture "${name}": "${have.get(name)}" and "${f}"`);
    else have.set(name, String(f));
  }
  plan.shots.forEach((s, i) => {
    const n = i + 1;
    if (!s || typeof s !== 'object') { problems.push(`shot ${n}: not an object`); return; }
    if (!String(s.say || '').trim()) problems.push(`shot ${n}: no "say" words`);
    const pic = 'picture' in s, card = 'card' in s;
    if (pic === card) problems.push(`shot ${n}: needs exactly one of "picture" or "card"`);
    for (const key of ['picture', 'doodle']) {
      if (s[key] == null) continue;
      if (!have.has(String(s[key]))) zipProblem(`shot ${n}: picture "${s[key]}" is not in the ZIP (looked for ${s[key]}.png, .jpg, .jpeg, .webp)`);
    }
  });

  const frame = plan.layout === 'short' ? '9:16' : (plan.frame === '9:16' ? '9:16' : '16:9');
  const words = plan.shots.reduce((a, s) => a + String((s && s.say) || '').replace(/\*/g, ' ').split(/\s+/).filter(Boolean).length, 0);
  const seconds = Math.round(words / 2.75);
  notes.push(`${plan.shots.length} shots, ${words} words, about ${seconds < 90 ? seconds + ' seconds' : (seconds / 60).toFixed(1) + ' minutes'}`);
  notes.push(`${frame === '9:16' ? 'Upright 9:16' : 'Wide 16:9'} · ${language === 'hi' ? 'Hindi' : 'English'} · voice ${voice}`);
  if (voice === 'chatterbox-hi') {
    // Chatterbox needs about 12 minutes of GitHub work per minute of speech;
    // a long film records parts of up to 12 minutes at the same time.
    const minutes = Math.ceil(Math.min(seconds, 720) / 60 * 12) + 8;
    notes.push(`The Hindi voice takes about ${minutes < 90 ? minutes + ' minutes' : (minutes / 60).toFixed(1) + ' hours'} on GitHub; the "Voice recorded" step will look slow.`);
  }
  return done(problems);

  function done(p) {
    return {
      ok: p.length === 0, problems: p, notes,
      forChatGPT: p.some(x => !zipProblems.has(x)) ? 'The plan checker rejected this plan. Fix only these, keep everything else, and send the corrected plan.json.\n' + p.filter(x => !zipProblems.has(x)).map(x => '- ' + x).join('\n') : '',
      slug: typeof slug === 'string' ? slug : '',
      frame: plan && typeof plan === 'object' ? (plan.layout === 'short' ? '9:16' : (plan.frame === '9:16' ? '9:16' : '16:9')) : '',
      language: plan && typeof plan === 'object' ? (plan.language || 'en') : '',
      voice: plan && typeof plan === 'object' ? (plan.voice || STILLS_DEFAULT_VOICE[plan.language || 'en'] || '') : '',
    };
  }
}

if (typeof module !== 'undefined') module.exports = { checkStillsUpload, filmKind, stillsSlug };
```

Test it and tell me the result of each:
- On "Still-picture films", upload a ZIP with `plan.json` and all its
  pictures: the notes and shots appear, "Make the film" uploads to
  rzam33r/stills-render and the progress steps move.
- Remove one picture from that ZIP: the page names the missing picture and
  does not upload.
- Drop an animated-film ZIP on "Still-picture films", then a still-picture
  ZIP on "Animated films": both are refused with the "use the other tab"
  message.
- Make an animated film on "Animated films": it works exactly as before.
