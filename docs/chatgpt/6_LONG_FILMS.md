# 6 — Films from 3 to 45 minutes, in either shape

Any length works in either shape: upright 9:16 or wide 16:9. Files 1 to 4
hold; this file adds what changes when a film runs longer than 3 minutes.

## Shape and pace are two choices

| | upright 9:16 | wide 16:9 |
|---|---|---|
| under 3 minutes | `"layout": "short"` (file 5) | `"layout": "wide"`, `"frame": "16:9"` |
| 3 minutes and more | `"layout": "wide"`, `"frame": "9:16"` | `"layout": "wide"`, `"frame": "16:9"` |

`"layout": "short"` is the fast pace (a picture every 2 to 4 words) and is
always upright. Longer films use the normal pace in either shape.

An upright film of any length ends every prompt's style block with "tall
upright 9:16 frame" and its pictures are made at 9:16; a wide film says
"wide 16:9" and is made at 16:9.

## How big the film is

The voice says about 165 words a minute in English and about 200 in Hindi
(with its pauses between sentences).

| length | English words | pictures (a new one every 4 to 5 seconds) |
|---|---|---|
| 5 minutes | about 850 | 60 to 75 |
| 10 minutes | about 1,650 | 120 to 150 |
| 20 minutes | about 3,300 | 240 to 300 |
| 30 minutes | about 5,000 | 360 to 450 |
| 45 minutes | about 7,400 | 540 to 680 |

Every picture is a Flow generation. Before writing a film of 10 minutes or
more, say how many pictures it will need and get an OK.

## Writing a long film

1. **Outline first.** Chapters of 3 to 5 minutes each: a 10-minute film has
   3 or 4, a 45-minute film 10 to 14. For each: its spoken title, one line
   saying what it shows, its minutes. Wait for the OK.
2. **Facts per chapter.** 5 to 10 facts for each chapter, each with how sure
   it is and where it comes from. Wait for the OK on each chapter's facts
   before writing it.
3. **One chapter at a time.** Write a chapter, show it, wait for the OK,
   then the next. Never write a whole long film in one reply.
4. Each chapter opens with its spoken title (a card with
   `"paragraph": true`) and ends with a hand-off line into the next one.
5. Every 10 minutes or so, one or two sentences remind the viewer where the
   story stands. Never a summary of everything said so far.

## Shots in a long film

- 8 to 14 words a shot (a picture every 3 to 5 seconds). Up to 16 when the
  image genuinely stays the same.
- Cards: 15 to 25 percent of the shots.
- Show progress through the story: the same place at a new time, the same
  character a step further, before moving somewhere new.
- Pictures are numbered across the whole film: `"001"` to `"680"` in a
  45-minute film. Numbers have three digits up to 999.
