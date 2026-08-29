# ff0l icon library

Full usage guide: [README.md](README.md). UI references: [catalog/refs.json](catalog/refs.json) and the preview **Refs** tab.

## Preview

```bash
python serve.py
```

Opens `http://127.0.0.1:8765/preview/`.

Rebuild the catalog after adding assets:

```bash
python tools/build_catalog.py
```

## Pick an asset

Agents should use this, not guess names:

```bash
python tools/search.py settings
python tools/search.py awp
python tools/search.py --kind font title
python tools/search.py gear --json
```

Read `catalog/icons.json` for collection rules and every icon. Fonts are in `catalog/fonts.json`.

## Default picks

1. CS2 weapons, grenades, armor, kits → `cs2/equipment/<name>.svg`
2. Custom overlay set (crosshair, eye, globe, weapon, sliders, gear) → `CustomIconPackDOPAMINA.ttf` (`A`–`F`, see `defs.txt`)
3. General UI icons → Font Awesome 7.3 solid: `fa-solid fa-<name>`
4. Brand logos → `fa-brands fa-<name>`
5. Lighter line/fill icons → `remixicon.ttf`
6. UI text → Montserrat or Inter. Titles → League Spartan, Oswald, or Syne. Dense small UI → Tahoma Bold or Verdana. Code → JetBrains Mono or Fira Code. More faces in `typefaces/`
7. Do not use FA 6/5 unless the consuming project is pinned to that version

C++ embeds live in `fonts/*.hpp`. Extracted copies are in `preview/extracted/`.
