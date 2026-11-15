# 7 — Hindi that the voice says clearly

The Hindi voice reads exactly what is written, letter by letter. These rules
come from the first Hindi film, where some words came out wrong. The engine
already fixes the most common ones; writing this way fixes the rest.

## Spelling for the voice

- **Nukta for f and z sounds.** Write फ़ when the word is said with f, and ज़
  when it is said with z: फ़ीस, फ़सल, रफ़्तार, सिर्फ़, तरफ़, साफ़, ज़्यादा,
  ज़रूरत, बाज़ार, रोज़, चीज़, हज़ार. Without the nukta the voice says
  "pheez", "raphtaar", "jyaada".
- Keep फ without a nukta only where people really say ph: फिर, फल, फूल.
- **Numbers in words**, as a person says them: सौ, एक सौ दस, बीस हज़ार,
  दो हज़ार चौबीस. Never digits.
- **No abbreviations or symbols.** "प्रतिशत", not "%". GDP becomes
  "जीडीपी", RBI "आरबीआई" (in Devanagari, letter by letter).
- English words people use in Hindi are written in Devanagari: फ़ोन,
  पेट्रोल, बजट, ऑफ़िस.

## Words the voice handles well

- Everyday Hindustani over formal Sanskrit Hindi: ज़्यादा not अतिरिक्त,
  कीमत not मूल्य, ज़रूरी not आवश्यक, शुरू not प्रारंभ.
- Short, common words. A word a viewer would have to think about is a word
  the voice may stumble on.

## Sentences

- Short: 4 to 10 words. One idea each.
- Every sentence ends with "।" or "?". The voice pauses there; without it
  sentences run into each other.
- A comma where a speaker would breathe inside a longer sentence.
- No sentence split across a "।" in the middle of a thought: the pause
  would break it.

## In plan.json

- `"language": "hi"`, and leave `"voice"` and `"speed"` out. The engine uses
  Kokoro's `hm_omega` voice.
- `"title"` in English letters (Hinglish): "Bharat mein badhti mehngai".
- Every `say` in Devanagari. Flow prompts stay in English.

## Before delivering a Hindi plan

Check every `say` once more for: a word with an f or z sound written
without the nukta; a digit or a symbol; a sentence longer than 10 words; a
sentence without "।" or "?" at its end.
