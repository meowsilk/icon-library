# ff0l icon library

Icons and typefaces I use for UI. Search before you invent a name or a path.

```
icons/       icon fonts and SVGs
typefaces/   text faces, one folder per family
embeds/      C++ .hpp bytes and extracted copies
catalog/     icons.json, fonts.json, refs.json
preview/     local preview
tools/       search and catalog build
```

## Preview

```bash
python serve.py
```

Opens `http://127.0.0.1:8765/preview/`. **All sets** searches every icon collection. Rebuild after adding files:

```bash
python tools/build_catalog.py
```

## Search

```bash
python tools/search.py settings
python tools/search.py awp
python tools/search.py --kind font title
python tools/search.py gear --json
python tools/search.py --collection cs2 knife
```

If ranking is unclear, read `catalog/icons.json` or `catalog/fonts.json`. Return the collection id, name, class and/or path, unicode when it is an icon font, and a one-line snippet.

### What to pick

1. Weapons, grenades, armor, kits → `icons/equipment/<name>.svg`
2. Overlay pack (crosshair, eye, globe, weapon, sliders, gear) → `icons/custom/dopamina.ttf`, keys `A`–`F` in `icons/custom/defs.txt`
3. General UI → `fa-solid fa-<name>` with `icons/ui/v7.3.0/`
4. Brand marks → `fa-brands fa-<name>`
5. Lighter line/fill → `icons/line/line.ttf` / `ri-<name>`
6. Type: Montserrat or Inter for UI. League Spartan, Oswald, or Syne for titles. Tahoma Bold or Verdana for dense small text. JetBrains Mono or Fira Code for code. Everything is under `typefaces/`
7. Stay on UI 7.3 unless the project is already on 6.7 or 5.15

## Icons

Solid UI (default):

```html
<link rel="stylesheet" href="icons/ui/v7.3.0/css/fontawesome.css">
<link rel="stylesheet" href="icons/ui/v7.3.0/css/solid.css">
<i class="fa-solid fa-gear"></i>
```

Other 7.3 styles are extra CSS plus extra classes:

- regular → `regular.css` + `fa-regular fa-gear`
- brands → `brands.css` + `fa-brands fa-github`
- sharp solid → `sharp-solid.css` + `fa-sharp fa-solid fa-gear`
- duotone → `duotone.css` + `fa-duotone fa-gear`

Webfonts sit next to the CSS in `icons/ui/v7.3.0/webfonts/`.

Line icons:

```css
@font-face { font-family: RemixIcon; src: url("icons/line/line.ttf"); }
.ri { font-family: RemixIcon; }
```

Class form: `ri-<glyph-name>` (example `ri-home-line`). Confirm the name with search.

Equipment SVGs are white and read on dark surfaces:

```html
<img src="icons/equipment/awp.svg" alt="AWP">
```

Overlay pack, `icons/custom/dopamina.ttf`:

| Key | Name |
| --- | --- |
| `A` | target / crosshair |
| `B` | eye |
| `C` | globe / earth |
| `D` | ak / weapon |
| `E` | sliders |
| `F` | gear / settings |

Type `A`–`F` in overlay code. The cmap is private-use starting at `U+F000`. Search collection `dopamina` if you need the code.

Also here:

- `icons/custom/iconsv2.ttf` — second pack. Check the glyph in the preview first.
- `icons/custom/tab.ttf` — a few glyphs.
- `icons/ui/loose/` — extra solid files. Prefer `icons/ui/v7.3.0`.
- `embeds/*.hpp` — C++ bytes. Extracted copies: `embeds/extracted/`.

## Fonts

Each family is `typefaces/<slug>/`.

| Use | Path |
| --- | --- |
| UI body | `typefaces/montserrat/` or `typefaces/inter/` |
| Titles | `typefaces/leaguespartan/`, `typefaces/oswald/`, `typefaces/syne/` |
| Dense small UI | `typefaces/tahoma/Tahoma-Bold.ttf` |
| Small body | `typefaces/verdana/Verdana-Regular.ttf` |
| Wide coverage | `typefaces/notosans/` |
| Code / logs | `typefaces/jetbrainsmono/`, `typefaces/firacode/` |

```css
@font-face {
  font-family: Montserrat;
  src: url("typefaces/montserrat/Montserrat[wght].ttf") format("truetype");
  font-weight: 100 900;
}
```

One family for UI, one for titles if you need a second. `mochi` and `pretzel` are bitmap fonts in `embeds/` — use the catalog bitmaps or the C++ bytes, not `@font-face`.

## UI references

`catalog/refs.json` and the preview **Refs** tab. Open them before you design.

| Site | Why |
| --- | --- |
| https://grainient.supply/collections | Texture, grain, dither. Not generic glass. |
| https://animate-ui.com/ | Motion with a job. |
| https://transitions.dev/ | Short, directed transitions. |
| https://bklit.com/docs/components/area-chart | How a real data component is built. |

No purple-blue gradients, glow borders, oversized glass cards, emoji-as-icons, or bounce on everything. Compact layout, hierarchical type, semantic color, rare motion.
