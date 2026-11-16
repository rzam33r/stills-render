# 7 — Hindi that the voice says clearly

Hindi films are read by Chatterbox's Hindi voice. It reads exactly what is
written, so how a word is spelled is how it is said. These rules come from
the first Hindi films; the engine also checks every sentence it records and
records an unclear one again.

## Spelling for the voice

- **Nukta for f and z sounds.** Write फ़ when the word is said with f, and ज़
  when it is said with z: फ़ीस, फ़सल, रफ़्तार, सिर्फ़, तरफ़, साफ़, ज़्यादा,
  ज़रूरत, बाज़ार, रोज़, चीज़, हज़ार. Without the nukta the voice may say
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
  Chatterbox's Hindi voice (`"chatterbox-hi"`). Naming `"hm_omega"` gives the
  older Kokoro Hindi voice instead.
- A Hindi voice takes longer to make: about 12 minutes of GitHub work per
  minute of narration. A 1-minute short is ready in about 20 minutes; a long
  film records its parts at the same time and takes 2 to 3 hours.
- `"title"` in English letters (Hinglish): "Bharat mein badhti mehngai".
- Every `say` in Devanagari. Flow prompts stay in English.

## Before delivering a Hindi plan

Check every `say` once more for: a word with an f or z sound written
without the nukta; a digit or a symbol; a sentence longer than 10 words; a
sentence without "।" or "?" at its end.
