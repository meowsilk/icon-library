# ff0l icon library

Usage: [README.md](README.md). UI references: [catalog/refs.json](catalog/refs.json) and the preview **Refs** tab.

## Preview

```bash
python serve.py
```

Opens `http://127.0.0.1:8765/preview/`.

After adding files:

```bash
python tools/build_catalog.py
```

## Pick an asset

Do not invent names. Search first:

```bash
python tools/search.py settings
python tools/search.py awp
python tools/search.py --kind font title
python tools/search.py gear --json
```

Icons: `catalog/icons.json`. Fonts: `catalog/fonts.json`.

1. Weapons, grenades, armor, kits → `icons/equipment/<name>.svg`
2. Overlay pack → `icons/custom/dopamina.ttf` (`A`–`F` in `icons/custom/defs.txt`)
3. General UI → `fa-solid fa-<name>` (`icons/ui/v7.3.0/`)
4. Brand marks → `fa-brands fa-<name>`
5. Line/fill → `icons/line/line.ttf`
6. Type: Montserrat or Inter for UI. League Spartan, Oswald, or Syne for titles. Tahoma Bold or Verdana for dense small text. JetBrains Mono or Fira Code for code. Faces in `typefaces/`
7. Stay on UI 7.3 unless the project is already on 6.7 or 5.15

C++ bytes: `embeds/*.hpp`. Extracted copies: `embeds/extracted/`.
