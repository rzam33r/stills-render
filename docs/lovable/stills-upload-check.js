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
