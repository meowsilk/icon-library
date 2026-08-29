---
name: pick-icon-or-font
description: Picks the best icon or font from this local library and applies its UI references so work does not look like generic AI slop. Use when choosing a UI icon, overlay glyph, weapon/equipment art, FA/Remix class, a typeface, or when building UI that should use Grainient, Animate UI, Transitions, or Bklit as references.
---

# Pick an icon or font

Read `README.md` for usage. Read `catalog/refs.json` before designing UI.

Do not invent icon names. Search this library first.

```bash
python tools/search.py <what the user needs>
```

Add `--json` when you need structured output. Use `--kind font` for typefaces. Use `--collection cs2` (or another id from `catalog/icons.json`) to narrow.

Then read `catalog/icons.json` or `catalog/fonts.json` only if the ranking is ambiguous.

## Prefer, in order

1. CS2 equipment art → `cs2` collection, path `icons/cs2/equipment/<name>.svg`
2. Custom overlay pack (crosshair, eye, globe, weapon, sliders, gear) → `dopamina` / `icons/custom/dopamina.ttf`, codes `A`–`F` in `icons/custom/defs.txt`
3. General UI → `fa-7.3.0` solid, class `fa-solid fa-<name>`
4. Brand logos → `fa-brands fa-<name>`
5. Line/fill UI when Remix names fit better → `remix` / `icons/remix/remixicon.ttf`
6. Type: Montserrat or Inter for UI, League Spartan / Oswald / Syne for titles, Tahoma Bold or Verdana for dense small text, JetBrains Mono or Fira Code for code. Search `typefaces/` via `python tools/search.py --kind font`

Do not pick FA 6 or FA 5 unless the consuming project is pinned to that version.

When building UI, open the sites in `catalog/refs.json` / `catalog/Websites.txt`. Do not invent purple glass, glow borders, or fake dashboards.

## Return

- collection id
- icon or font name
- class and/or path
- unicode when it is an icon font
- a one-line usage snippet
