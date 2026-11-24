# Give GitHub a key to the Bittu Ki Riya Instagram

Done once, by Roshan, in about 20 minutes, on a computer. After it, every
**upright** Bittu Ki Riya film is posted on Instagram as a Reel, with the
plan's caption and hashtags, right after its Drive copy. Wide films stay on
YouTube only.

The keys go straight into GitHub's secret settings and nowhere else: never
into a chat, an email, a note you share or a file in this repository.

## 1. Instagram is a professional account

Your Instagram is already a Creator or Business account (24 Nov 2026), and
it needs no Facebook Page. Nothing to do.

## 2. A Meta app

1. Open https://developers.facebook.com and log in. Meta asks for a
   Facebook login here; your personal Facebook profile is fine. No Page is
   needed.
2. Press **My Apps** → **Create app**.
3. App name: `Bittu Ki Riya uploader`. Your email. **Next**.
4. Use case: **Manage messaging & content on Instagram**. **Next**.
5. If asked about a business portfolio, choose not to connect one now.
   **Next** until **Create app**, then confirm with your Facebook password
   if asked (on Meta's own page; never anywhere else).

## 3. The Instagram key

1. In the app, open the Instagram use case: **Use cases** → **Manage
   messaging & content on Instagram** → **Customize** (or **API setup with
   Instagram login**).
2. Under **Permissions**, make sure these two are added:
   `instagram_business_basic` and `instagram_business_content_publish`.
3. Under **Generate access tokens**, press **Add account** and log in to
   Instagram as the **Bittu Ki Riya** account. Allow what it asks.
4. Press **Generate token** next to that account, tick the box, and copy
   the token. It is good for 60 days; GitHub renews it from then on
   (step 5).

The app stays in "Development" mode: that is fine for posting to your own
account. If Instagram ever says the app is not allowed to post, tell Claude.

## 4. The key and the account name into GitHub

1. Open https://github.com/rzam33r/stills-render/settings/secrets/actions
   (in the browser; the GitHub phone app cannot do this).
2. Press **New repository secret** twice:

   | Name | Secret |
   |---|---|
   | `INSTAGRAM_TOKEN` | the token from step 3 |
   | `INSTAGRAM_ACCOUNT` | the Instagram username, for example `bittukiriya` |

   GitHub refuses to post if the key belongs to any other account.

## 5. Let GitHub renew the key by itself

Instagram's key stops after 60 days. Every Wednesday GitHub renews it, and
when Instagram hands back a new one GitHub saves it over the old
`INSTAGRAM_TOKEN`. For that it needs a GitHub key that may change this
repository's secrets, and nothing else:

1. Open https://github.com/settings/personal-access-tokens/new (signed in as
   **rzam33r**).
2. Token name: `Instagram key renewal`. Expiration: the longest offered.
3. Repository access: **Only select repositories** → **stills-render**.
4. Permissions → **Repository permissions** → **Secrets** → **Read and
   write**. Leave everything else as it is.
5. **Generate token**, copy it, and add it as one more repository secret
   (step 4's page) named `GH_SECRETS_TOKEN`.

When that GitHub key nears its expiry date, GitHub emails you; make a new
one the same way and replace `GH_SECRETS_TOKEN`.

## 6. Check the key (posts nothing)

1. Open https://github.com/rzam33r/stills-render/actions/workflows/instagram-check.yml
2. **Run workflow** → **Run workflow**.
3. Green, naming your account: done. Red: open the run; it says which step
   above to redo.

## Later

- **Every upright film:** the GitHub run's summary shows the Reel's link,
  or "NOT POSTED" and what to do. To remove a Reel, delete it in the
  Instagram app.
- **"The Instagram key no longer works":** redo steps 3 and 4 (a new token
  into `INSTAGRAM_TOKEN`), then step 6.
- **Instagram's limit:** 50 posts a day through apps, far above one film a
  day.
- **To stop posting:** delete the secret `INSTAGRAM_TOKEN`. Films then go to
  Drive and YouTube only.
