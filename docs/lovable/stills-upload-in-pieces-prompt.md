# Lovable prompt — send still-picture ZIPs to GitHub in 8 MB pieces

On 16 Nov 2026 a 34.7 MB ZIP failed at "uploading the ZIP to GitHub" with
"TypeError: Failed to fetch" and no HTTP answer: the whole ZIP went through
the backend in one request, and the backend function (256 MB memory, 2 s of
CPU, 150 s) was cut off before it could answer. The engine on GitHub now
accepts a ZIP in pieces and joins them, checking size and SHA-256
(engine/join_upload.py). Small pieces stay far from every limit at any film
length, up to the hundreds of MB a 45-minute film needs.

Copy everything below the line into Lovable's chat, in one message.

---

Change how the **"Still-picture films"** tab sends its ZIP to GitHub. The
"Animated films" tab stays exactly as it is (its engine expects one ZIP).

1. **Fingerprint.** After the ZIP's bytes are read (they are already read
   once into memory when chosen), compute its size and SHA-256 in the
   browser with `crypto.subtle.digest('SHA-256', bytes)`, as lowercase hex.

2. **Clear the release.** Make or reuse the release `story-<slug>` on
   `rzam33r/stills-render` as now, and delete every asset already on it, as
   now.

3. **Send the ZIP in pieces of exactly 8 MB** (8 × 1024 × 1024 bytes; the
   last piece is smaller). Do this for every ZIP, small ones too (one piece),
   so there is only one way to upload.
   - Piece `i` (from 1) is uploaded as the release asset
     `<zip file name>.part<i as 3 digits>`, for example
     `royal-enfield-legend-india.zip.part001`, with
     `Content-Type: application/octet-stream`.
   - Each piece is its own request from the browser to the backend, and the
     backend sends that piece's raw bytes straight on to GitHub's upload URL
     for the release. Never base64 or JSON-wrap the bytes, in either step.
   - One piece at a time, in order. Show "Uploading piece 2 of 5".
   - If a piece fails (no answer, 429 or 5xx), wait 2, 5, then 10 seconds and
     send that piece again; on 422 already_exists, delete that asset and send
     it again. After 3 failed tries of one piece, stop and show the error with
     the piece number.

4. **Then the parts list**, as the asset `<zip file name>.parts.json`
   (`Content-Type: application/json`):
   `{"name": "<zip file name>", "size": <bytes>, "sha256": "<hex>", "parts": <count>}`

5. **Only then** start `make-film.yml` exactly as now (same inputs).

6. **Errors.** "Copy error details" adds the piece number and the number of
   pieces to what it shows now.

Test it and tell me the result of each:
- A small still-picture ZIP (under 8 MB): one piece and a parts list arrive,
  and the film is made.
- A ZIP over 30 MB: several pieces arrive, "Uploading piece N of M" moves,
  and the film is made.
- The "Animated films" tab uploads exactly as before.
