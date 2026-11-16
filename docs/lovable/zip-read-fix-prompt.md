# Lovable prompt — read the ZIP once, and say why reading failed

On 16 Nov 2026 an upload failed with "Failed while reading the ZIP —
Error: [object ProgressEvent]". The page could read the ZIP when it checked
it, but not a moment later when it uploaded it: the file on the computer had
changed, moved or been deleted after it was chosen. A browser keeps a link to
the chosen file, not a copy, and refuses to read it once the file changes.
The release was made and stayed empty.

Copy everything below the line into Lovable's chat, in one message.

---

Change the shared ZIP upload used by both tabs ("Animated films" and
"Still-picture films"). Nothing else changes.

1. **Read the ZIP once, as soon as it is chosen.** When a ZIP is chosen (or
   dropped), read the whole file into memory right away with
   `await file.arrayBuffer()`, keep those bytes, and use them for everything
   after: the checks, the shots list, and the upload to GitHub. Never read the
   `File` again after that. If the file is chosen again, read it again.
   While it is being read, show "Reading the ZIP…".

2. **Say why reading failed, in plain words.** If reading throws, show the
   error's `name` and `message`, never the event object. Use these messages:
   - `NotReadableError`: "The ZIP changed, moved or was deleted after you
     chose it. Choose it again from where it is now."
   - `NotFoundError`: "The ZIP is no longer where you chose it. Choose it
     again."
   - `NotAllowedError` / `SecurityError`: "The browser was not allowed to
     read this file. Choose it again from a folder on this computer (not a
     cloud-only file)."
   - anything else: "Could not read the ZIP: <name>: <message>".
   Keep the "Copy error details" button; its text must include the error
   name, the file's name and size, and the time it was chosen.
   The same rule everywhere an error is shown: never print "[object …]" —
   show `error.name: error.message`, or `JSON.stringify` of the details.

3. **Stop a stale ZIP before uploading.** Just before "Make the film" / the
   build button sends anything, compare the chosen file's `lastModified` and
   `size` with the values taken when it was read. If either differs, do not
   upload; show "The ZIP changed on your computer after you chose it. Choose
   it again." (The bytes already read are still fine to check, but the user
   should upload the file they mean.)

4. **An empty story from a failed try is reused.** If a release
   `story-<slug>` already exists with no assets (a try that failed before
   uploading), use it as now (422 already_exists → fetch it by tag), and
   delete every asset on it before uploading, as now.

Test it and tell me the result of each:
- Choose a ZIP, then rename or delete it on the computer, then press the
  build button: the page says the ZIP changed and uploads nothing.
- Choose a ZIP and build normally on both tabs: it works as before.
- Force a read error (choose a ZIP, then delete it before the page finishes
  reading): the message names the error in plain words, not
  "[object ProgressEvent]".
