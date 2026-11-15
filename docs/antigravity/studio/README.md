# FACT HUBZZZ Studio (Antigravity)

Antigravity plans and writes the film, makes its pictures in Google Flow
through Flow Connect, and starts it on the upload page. GitHub makes the
film and puts it in your Google Drive folder.

## Set up once

1. Unzip this folder somewhere you keep work, for example
   `Documents\FACT HUBZZZ Studio`.
2. In Antigravity: **File → Open Folder** and choose it.
3. Make sure Flow Connect is connected (agent panel **…** → MCP servers).
4. In the agent panel, type `/`. You should see **new-film**,
   **make-pictures**, **upload-film** and **fix-plan**. If they are not
   there, open the agent panel's **…** → **Customizations** → **Workflows**
   and check the workspace workflows are listed.

## Make a film

Type `/new-film` and the topic, for example:
`/new-film why prices keep rising in India — upright, 1 minute, Hindi`

Antigravity stops for your OK after the format, the hooks, the facts, the
script, the shot list and the plan, just like the ChatGPT project. After
your OK on the plan it makes the pictures and uploads the film.

- `/make-pictures` makes (or finishes) a film's pictures.
- `/upload-film` zips a finished film and starts it on the upload page.
- `/fix-plan` fixes a plan from the problems the upload page or GitHub
  reported.

## What is in this folder

- `.agent/` — the studio's rules and the four workflows.
- `guide/` — the writing rules (the same files the ChatGPT project uses).
- `tools/` — the engine's own plan check (needs Python; optional).
- `films/` — one folder per film, and its ZIP.

## Updating

The newest version is always at
https://github.com/rzam33r/stills-render/releases/download/chatgpt-pack/FACT-HUBZZZ-Studio.zip
Unzip it over this folder: it replaces `.agent`, `guide` and `tools` and
never touches `films`.
