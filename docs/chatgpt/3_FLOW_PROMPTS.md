# 3 — Google Flow prompts

Every picture is made in Google Flow from its prompt in plan.json. The look
holds together only if every prompt describes the lead character the same
way and ends with the same style block.

## The lead character

Write the character description once at the top of plan.json as
`"character"`, and paste it word for word into every prompt that shows
them. The default lead:

> a simple stick-figure man with a large round white head, two small black
> dot eyes, simple expressive eyebrows and mouth, a thin black stick body
> and limbs

plus clothing that fits the setting (for prehistory: "wearing a short
ragged brown animal-hide tunic"; today: "wearing a plain blue t-shirt and
grey trousers"). Keep the head, face and body the same in every picture.
In Flow, use the same reference image of the character for every picture.

## Bittu & Riya films

Bittu and Riya are Flow characters in the Flow project `Bittu & Riya`, and
their pictures are made in Antigravity, which casts them as Flow characters
through Flow Connector. For these
films, follow `cast/bittu-riya/CAST.md` in the studio instead of this
section: no `"character"`, no description of their faces, hair or clothes,
and each picture lists who is in it in `"who"`.

## The style block

Write it once as `"style"` in plan.json and end every picture prompt with
it, word for word:

> Hand-drawn cartoon illustration, ink outlines with soft watercolour
> colouring, muted natural colours, simple clear composition, wide 16:9
> frame, no text, no letters, no numbers, no signs, no watermark.

## A picture prompt

One or two sentences in this order:
1. the shot type (wide view, medium shot, close-up, split picture);
2. the lead character, what they are doing, and how they feel;
3. the place, the time of day, the light;
4. the one object or detail that matches the shot's words;
5. the style block.

Example, for "If animals avoided a particular pool, humans learned to avoid it too":

> Medium shot of [character], wearing a short ragged brown animal-hide
> tunic, standing at the edge of a still green pool with one hand raised,
> looking uneasy, while a deer on the far bank turns away from the water;
> dry grassland in afternoon light. [style]

**Hands.** Say what each person's hands do, and give one person at most two
things to hold, one per hand. Image models add a third hand to hold a third
thing (17 Nov 2026: a boy with a hammer, a blade and a stone grew a third
arm). "Holds a hammer in one hand and a black stone in the other" is safe;
"holds a hammer, a blade and a stone" is not.

## Never

- Text, labels, signs, letters or numbers inside a picture (a number is an
  animated graphic: `8_GRAPHICS.md`).
- A different face, head shape or body for the lead character.
- More than two things held by one person, or hands not said.
- Photographic, 3D or anime styles.
- Gore. Danger is shown by situation and expression, not injury.
