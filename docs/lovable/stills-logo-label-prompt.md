# Lovable prompt — the still-picture tab's logo is Bittu Ki Riya

Still-picture films carry the Bittu Ki Riya badge (stills-render,
`brand/watermark.png`); animated films keep FACT HUBZZZ (rose-render-test).
The upload page still calls the still-picture logo "FACT HUBZZZ".

Copy everything below the line into Lovable's chat, in one message.

---

On the **Still-picture films** tab only (`/stills`), the logo option is
named wrong. Change these on that tab, and nothing else:

1. Wherever the logo option says FACT HUBZZZ (the checkbox or radio label,
   its help text or tooltip, and the build line such as "Logo: on"), say
   **Bittu Ki Riya** instead, for example "Bittu Ki Riya logo" and
   "Logo: Bittu Ki Riya".
2. If the tab shows a FACT HUBZZZ logo picture, show this one instead, about
   48 pixels tall:
   https://raw.githubusercontent.com/rzam33r/stills-render/main/brand/watermark.png
3. Keep what is sent to GitHub exactly as it is: the `logo` input stays
   `true` or `false`. Only the words and the picture change.

Do not change the **Animated films** tab: its logo stays FACT HUBZZZ, with
the same label, picture and behaviour.

Then tell me:
- every place on the Still-picture tab where the text changed;
- that the Animated films tab still says FACT HUBZZZ;
- that starting a still-picture film still sends `logo: true` when the box
  is ticked.
