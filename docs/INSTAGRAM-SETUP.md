# Give GitHub a key to the Bittu Ki Riya Instagram

Done once, by Roshan, on a computer (done 26 Nov 2026). After it, every
**upright** Bittu Ki Riya film is posted on Instagram as a Reel, with the
plan's caption and hashtags, right after its Drive copy. Wide films stay on
YouTube only.

The keys go straight into GitHub's secret settings and nowhere else: never
into a chat, an email, a note you share or a file in this repository. You
type every login and password yourself, on Meta's or Instagram's own page.

Since 2026 Meta gives new apps **"API setup with Unified login"** only (the
page says "API setup with Instagram login is not available for newer
apps"). That route needs a Facebook login and a business portfolio, but no
Facebook Page, and its key never expires. These steps follow it.

## 1. Instagram is a professional account

Your Instagram is already a Creator or Business account (24 Nov 2026), and
it needs no Facebook Page. Nothing to do.

## 2. A Meta app and a business portfolio

1. Open https://developers.facebook.com and log in with your **personal**
   Facebook profile (a work-platform account cannot create apps). If Meta
   says the account is "too new to create a business", wait a day.
2. **My Apps** → **Create app**. App name: `Bittu Ki Riya uploader`.
3. Use case: **Manage messaging & content on Instagram**.
4. When asked for a business portfolio, create one (`Bittu Ki Riya`);
   "Verify later" is fine. **Create app**.

## 3. The Instagram key

1. In the app: **Use cases** → Instagram API → **Customize** → **API setup
   with Unified login**.
2. **Permissions and features:** add `instagram_basic` and
   `instagram_content_publish` (Meta's own template also adds others; they
   are not used).
3. **App roles** → **Roles** → add the Instagram account as an **Instagram
   Tester**; then, in Instagram (Settings → Website permissions → Apps and
   websites → Tester invites, or instagram.com/accounts/manage_access),
   accept the invite.
4. Back in **API setup with Unified login**:
   - Section **1. Configure your app** → **Create new configuration** →
     **Create from template** ("System-user access token", "Token will
     never expire").
   - Section **2. Generate access tokens** → the account is listed (else
     **Add account**) → **Generate token**. A pop-up opens: log in as the
     Bittu Ki Riya account if asked, choose it, and allow. You may untick
     "Allow access to messages"; posting does not need it.
   - Tick **I understand**, press **Copy**. Meta shows it only once; if it
     is lost, press Generate token again.

The key starts with "EA". The app stays in "Development" mode, and "Complete
App Review" can be ignored: a tester account may post to itself.

## 4. The key and the account into GitHub

1. Open https://github.com/rzam33r/stills-render/settings/secrets/actions
   (in the browser; the GitHub phone app cannot do this).
2. Press **New repository secret** twice:

   | Name | Secret |
   |---|---|
   | `INSTAGRAM_TOKEN` | the key from step 3 |
   | `INSTAGRAM_ACCOUNT` | the Instagram username: `bittu.ki.riya` |

   GitHub refuses to post if the key belongs to any other account.

The account's number at Meta (`INSTAGRAM_USER_ID`, 17841436806102076 for
@bittu.ki.riya) is already written into the workflows; it is shown under the
account's name in step 3's list. Only a different account would need it
changed.

## 5. Renewing the key: nothing to do

This key never expires, so `GH_SECRETS_TOKEN` is **not** needed. Every
Wednesday GitHub checks the key; if Meta ever gives one that expires, that
check fails 14 days before the end, GitHub emails you, and you redo steps 3
and 4.

Only if you ever use the older Instagram-login key (it starts "IG" and
lasts 60 days) does GitHub renew it by itself, and then it needs a GitHub
key that may change this repository's secrets:

1. https://github.com/settings/personal-access-tokens/new (as **rzam33r**).
2. Name `Instagram key renewal`; longest expiration; **Only select
   repositories** → **stills-render**; **Repository permissions** →
   **Secrets** → **Read and write**; nothing else.
3. **Generate token**, and add it as one more repository secret named
   `GH_SECRETS_TOKEN`.

## 6. Check the key (posts nothing)

1. Open https://github.com/rzam33r/stills-render/actions/workflows/instagram-check.yml
2. **Run workflow** → **Run workflow**.
3. Green, naming your account and "it never expires": done. Red: open the
   run; it says which step above to redo.

## Later

- **Every upright film:** the GitHub run's summary shows the Reel's link,
  or "NOT POSTED" and what to do. To remove a Reel, delete it in the
  Instagram app.
- **"The Instagram key no longer works":** redo steps 3 and 4 (a new key
  into `INSTAGRAM_TOKEN`), then step 6. Removing the app from Instagram's
  "Apps and websites", or the tester role, withdraws the key.
- **Instagram's limit:** 50 posts a day through apps, far above one film a
  day.
- **To stop posting:** delete the secret `INSTAGRAM_TOKEN`. Films then go to
  Drive and YouTube only.
