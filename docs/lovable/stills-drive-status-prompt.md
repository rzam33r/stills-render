On the **Still-picture films** tab, fix step 4 "Sent to Google Drive" in
the Build box. Change nothing else.

**What is wrong.** Run 43921652522 (story how-royal-enfield-became-a-leg)
never sent the film to Drive: its `deliver` job was **skipped**. The page
still said "Delivered, but the link is not ready yet. The video is already
in Drive." That sentence is false whenever the delivery job did not succeed,
and it would hide a film that never arrived.

**Before you change anything,** tell me in one line what the page checks
today to decide it says "Delivered, but the link is not ready yet".

**The rule (backend, repository `rzam33r/stills-render`):**

1. Step 4 depends only on the run's job named exactly `deliver / deliver`.
   Ignore `deliver / blocked`; it only runs when a delivery is refused.
2. While the run is still going: step 4 waits, as now.
3. `deliver / deliver` concluded **success** → tick step 4, "Sent to Google
   Drive". Then read `delivered/<slug>.json` from branch `main` with the
   contents API and the server-side token. Show its `web_view_link` as
   "Watch in Google Drive". If the file is not there yet, say "Sent to
   Drive — the link appears in a minute", and try again every 15 seconds
   for up to 2 minutes.
4. Run finished but `deliver / deliver` did **not** succeed (skipped,
   failed, cancelled, or missing) → step 4 in red: "Made, but NOT sent to
   Google Drive". Keep "Open the GitHub run". Never say "Delivered" in this
   case.

**Tests (add them, and run them):**

- Run 43921652522: its delivery was skipped, so step 4 must show "Made, but
  NOT sent to Google Drive".
- Run 43843413592 (bharat-mein-badhti-mehngai): its delivery succeeded, so
  step 4 is ticked and links to
  https://drive.google.com/file/d/12EzGnAczgGpqyazwwoJ6ZkhsTNItogh8/view?usp=drivesdk
- A run with `deliver / deliver` failed: shows "Made, but NOT sent to
  Google Drive".

Reply with the one line about today's check, then what you changed and the
test results.
