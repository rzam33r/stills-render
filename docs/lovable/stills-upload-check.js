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
  let plan, slug = '';
  try { plan = parsePlan(planText); }
  catch (e) { return done([`plan.json is not valid JSON: ${e.message}`]); }
  if (!plan || typeof plan !== 'object') return done(['plan.json is not a plan']);
  if (!Array.isArray(plan.shots) && Array.isArray(plan.scenes))
    return done(['This is an animated (Rose) film. Use the "Animated films" tab.']);
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
    if (have.has(name)) problems.push(`two files for picture "${name}": "${have.get(name)}" and "${f}"`);
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
      if (!have.has(String(s[key]))) problems.push(`shot ${n}: picture "${s[key]}" is not in the ZIP (looked for ${s[key]}.png, .jpg, .jpeg, .webp)`);
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
      forChatGPT: p.length ? 'The plan checker rejected this plan. Fix only these, keep everything else, and send the corrected plan.json.\n' + p.map(x => '- ' + x).join('\n') : '',
      slug: typeof slug === 'string' ? slug : '',
      frame: plan && typeof plan === 'object' ? (plan.layout === 'short' ? '9:16' : (plan.frame === '9:16' ? '9:16' : '16:9')) : '',
      language: plan && typeof plan === 'object' ? (plan.language || 'en') : '',
      voice: plan && typeof plan === 'object' ? (plan.voice || STILLS_DEFAULT_VOICE[plan.language || 'en'] || '') : '',
    };
  }
}

if (typeof module !== 'undefined') module.exports = { checkStillsUpload, filmKind, stillsSlug };
