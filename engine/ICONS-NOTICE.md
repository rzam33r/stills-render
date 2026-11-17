# The icon library

`icons.json` names 1,600+ pictures from **Google's Noto Emoji**
(https://github.com/googlefonts/noto-emoji, commit in `icons.json`), whose
image resources are under the **Apache License, Version 2.0**
(https://www.apache.org/licenses/LICENSE-2.0). The pictures are not kept in
this repository: `engine/icons.py fetch` downloads the ones a film uses at
that commit, and the film workflow caches them.

The everyday names come from **emoji-datasource 15.1.2** (MIT licence,
`fonts/emoji/LICENSE-emoji-datasource.txt`).

`graphics.py` gives each picture a white ring and a dark outline and
animates it; the charts, gauge, counter, road, footprints and map pin around
them are drawn by `graphics.py` itself.
