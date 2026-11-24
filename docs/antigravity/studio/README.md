# FACT HUBZZZ Studio (Antigravity)

Antigravity plans and writes the film, makes its pictures in Google Flow
through Flow Connector, and starts it on the upload page. GitHub makes the
film, puts it in your Google Drive folder and posts it, publicly, on the
Bittu Ki Riya YouTube channel with the title, caption and hashtags from the
plan.

## Set up once

1. Unzip this folder somewhere you keep work, for example
   `Documents\FACT HUBZZZ Studio`.
2. In Antigravity: **File → Open Folder** and choose it.
3. Make sure Flow Connector is connected: the Chrome extension, with its
   setup prompt pasted into Antigravity once. Keep a Flow tab open in Chrome.
4. In the agent panel, type `/`. You should see **check-studio**,
   **new-film**, **make-pictures**, **upload-film** and **fix-plan**. If they
   are not there, the folder you opened is not the one holding `.agent`
   (File → Open Folder → `FACT HUBZZZ Studio`).
5. Type `/check-studio`. It checks the folder, Flow Connector and the upload
   page, changes nothing, and tells you what to fix before your first film.

## Make a film

Type `/new-film` and the topic, for example:
`/new-film why prices keep rising in India — upright, 1 minute, Hindi`

or, with Bittu and Riya:
`/new-film Bittu & Riya: Bittu's surprise birthday plan — upright, 1 minute, Hindi`

Antigravity stops for your OK after the format, the hooks, the facts, the
script, the shot list and the plan, just like the ChatGPT project. After
your OK on the plan it makes the pictures and uploads the film.

- `/make-pictures` makes (or finishes) a film's pictures.
- `/upload-film` zips a finished film and starts it on the upload page.
- `/fix-plan` fixes a plan from the problems the upload page or GitHub
  reported.

## What is in this folder

- `.agent/` — the studio's rules and the five workflows.
- `guide/` — the writing rules (the same files the ChatGPT project uses).
- `tools/` — the engine's own plan check (needs Python; optional).
- `films/` — one folder per film, and its ZIP.
- `cast/bittu-riya/` — Bittu and Riya: who they are, and how their pictures
  are made with their Flow characters (project `Bittu & Riya`).

## Updating

The newest version is always at
https://github.com/rzam33r/stills-render/releases/download/chatgpt-pack/FACT-HUBZZZ-Studio.zip
Unzip it over this folder: it replaces `.agent`, `guide` and `tools` and
never touches `films`.
