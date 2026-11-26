# Give GitHub a key to the Bittu Ki Riya Facebook Page

Done once, on a computer. After it, every **upright** Bittu Ki Riya film is
posted on the Bittu Ki Riya Facebook Page right after Instagram, with the
same caption and hashtags:

- **90 seconds or less:** as a Reel (Meta's Reels API takes 3 to 90 s);
- **longer:** as an ordinary Page video, shown full screen but not a Reel.

Wide films stay on YouTube only. Facebook lets apps post only to a **Page**,
never to a person's profile.

The key goes straight into GitHub's secret settings and nowhere else: never
into a chat, an email, a note you share or a file in this repository. You
type every login and password yourself, on Meta's own page.

## 1. The Page

The Page **Bittu Ki Riya** (category Digital creator) exists since 26 Nov
2026: https://www.facebook.com/profile.php?id=61596905883436 . Its number,
`61596905883436`, is written into the workflows as `FACEBOOK_PAGE_ID`.
Add the same profile picture as Instagram, from the Facebook app.

## 2. The app may post to Pages

In https://developers.facebook.com → **Bittu Ki Riya uploader** → **Use
cases**, the use case **Manage everything on your Page** is added, with
`pages_show_list`, `pages_read_engagement` and `pages_manage_posts` (done 26
Nov 2026).

## 3. A system user with the Page, and its key

A system user is a robot account inside your business portfolio. It cannot
log in, and its key never expires.

1. Open https://business.facebook.com/settings (business portfolio **Bittu
   Ki Riya**).
2. **Accounts → Pages → Add → Add a Page** → `Bittu Ki Riya`.
3. **Users → System users → Add**: name `Bittu Ki Riya uploader`, role
   **Admin**.
4. On that system user: **Assign assets** → **Pages** → Bittu Ki Riya →
   **Content: Create content** (full control is not needed) → Save. Then
   **Assign assets → Apps** → Bittu Ki Riya uploader → **Develop app**.
5. **Generate new token** → app **Bittu Ki Riya uploader** → expiry
   **Never** → permissions `pages_show_list`, `pages_read_engagement`,
   `pages_manage_posts` → **Generate token**. Copy it: Meta shows it once.

## 4. The key into GitHub

1. Open https://github.com/rzam33r/stills-render/settings/secrets/actions
   (in the browser; the GitHub phone app cannot do this).
2. **New repository secret**: name `FACEBOOK_TOKEN`, secret: the key from
   step 3.

## 5. Check the key (posts nothing)

1. Open https://github.com/rzam33r/stills-render/actions/workflows/facebook-check.yml
2. **Run workflow** → **Run workflow**.
3. Green, naming the Page: done. Red: open the run; it says which step
   above to redo.

## Later

- **Every upright film:** the GitHub run's summary shows the Facebook link
  and whether it went up as a Reel or a video, or "NOT POSTED" and what to
  do. To remove it, delete it on the Page.
- **"The Facebook key no longer works":** redo steps 3.5 and 4, then 5.
  Removing the system user or its Page access withdraws the key.
- **Facebook's limit:** 30 Reels a day through apps, far above one film a
  day.
- **To stop posting:** delete the secret `FACEBOOK_TOKEN`. Films then go to
  Drive, YouTube and Instagram only.
