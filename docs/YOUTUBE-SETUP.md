# Give GitHub a key to the Bittu Ki Riya channel

Done once, by Roshan, in about 15 minutes. Use a computer (or a phone's
browser in "desktop site" mode). Sign in to Google with the account that owns
the Bittu Ki Riya channel.

The key has three parts: a **client ID**, a **client secret** and a
**refresh token**. They go straight into GitHub's secret settings and
nowhere else: never into a chat, an email, a note you share or a file in
this repository. Anyone who has all three can post videos on the channel.
The key can upload and look up the channel's name. It cannot delete or edit
existing videos.

## 1. A Google Cloud project with YouTube switched on

1. Open https://console.cloud.google.com/projectcreate
2. Project name: `Bittu Ki Riya uploader`. Press **Create**. Agree to the
   terms if asked.
3. Open https://console.cloud.google.com/apis/library/youtube.googleapis.com
4. Check the project name at the top says `Bittu Ki Riya uploader`, then
   press **Enable**.

## 2. The sign-in screen, set to "In production"

1. Open https://console.cloud.google.com/auth/overview and press
   **Get started**.
2. App name: `Bittu Ki Riya uploader`. User support email: yours. **Next**.
3. Audience: **External**. **Next**.
4. Contact email: yours. **Next**. Tick the agreement, **Continue**,
   **Create**.
5. In the left menu, **Audience** → **Publish app** → **Confirm**.
   The page must now say **In production**. If it says "Testing", the key
   stops working after 7 days.

## 3. The client ID and client secret

1. In the left menu, **Clients** → **Create client**.
2. Application type: **Web application**. Name: `GitHub`.
3. Under **Authorized redirect URIs**, press **Add URI** and paste
   `https://developers.google.com/oauthplayground`
4. Press **Create**. A box shows the **Client ID** and the **Client
   secret**. Keep that box open (or press **Download JSON**): Google may not
   show the secret again.

## 4. The refresh token

1. In a new tab, open https://developers.google.com/oauthplayground
2. Press the **gear** icon (top right). Tick **Use your own OAuth
   credentials**. Paste the Client ID and the Client secret. **Close**.
3. On the left, in the box **Input your own scopes**, paste exactly this
   (one line, with the space in the middle):

   `https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly`

4. Press **Authorize APIs**.
5. Choose your Google account. If Google asks which channel or account to
   use, choose **Bittu Ki Riya**. (If the key belongs to any other channel,
   GitHub refuses to post and says so.)
6. "Google hasn't verified this app": press **Advanced**, then **Go to
   Bittu Ki Riya uploader**. It is your own app.
7. Allow both permissions and press **Continue**.
8. Back in the Playground, under **Step 2**, press **Exchange authorization
   code for tokens**. Copy the **Refresh token** (it starts with `1//`).

## 5. The three parts into GitHub

1. Open https://github.com/rzam33r/stills-render/settings/secrets/actions
   (the GitHub phone app cannot do this; use the browser).
2. Press **New repository secret** three times:

   | Name | Secret |
   |---|---|
   | `YOUTUBE_CLIENT_ID` | the Client ID from step 3 |
   | `YOUTUBE_CLIENT_SECRET` | the Client secret from step 3 |
   | `YOUTUBE_REFRESH_TOKEN` | the Refresh token from step 4 |

   Paste each value exactly, with no spaces before or after.

## 6. Check the key (posts nothing)

1. Open https://github.com/rzam33r/stills-render/actions/workflows/youtube-check.yml
2. Press **Run workflow**, then the green **Run workflow**.
3. Green, saying the key belongs to "Bittu Ki Riya": done. Every film made
   from now on goes public on the channel a few minutes after it reaches
   Drive.
4. Red: open the run. It says in one sentence which step above to redo.

## Worth doing once

Verify the channel with your phone number at https://www.youtube.com/verify
so the 15-minute specials and custom thumbnails are allowed.

## Later

- **Every film:** the GitHub run's summary shows the YouTube link, or
  "NOT POSTED" and what to do. The film is always in Drive as well. To
  remove a film, delete it in YouTube Studio.
- **"The YouTube key no longer works":** check step 2 still says "In
  production", then redo step 4 and replace `YOUTUBE_REFRESH_TOKEN` (step 5),
  then step 6.
- **A film shows "Private (locked)" in YouTube Studio:** Google has locked
  uploads from apps it has not reviewed. Tell Claude: the fix is Google's
  review form for the YouTube API.
- **To stop posting:** delete the secret `YOUTUBE_REFRESH_TOKEN`. Films then
  go to Drive only.
