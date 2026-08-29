# ff0l icon library

Local Font Awesome Pro, Remix Icon, custom icon fonts, CS2 SVGs, and typefaces.

Agents: read this file before picking or using an icon or font. Do not invent names, unicode, or paths.

```bash
python serve.py
python tools/search.py <what you need>
python tools/build_catalog.py
```

Preview: `http://127.0.0.1:8765/preview/`  
In the preview, **All sets** (or **All icons** in the sidebar) searches every collection at once.  
Icons: `catalog/icons.json`  
Fonts: `catalog/fonts.json`  
UI references: `catalog/refs.json` and the **Refs** tab in the preview.

The preview is a static site (`preview/` plus `catalog/*.json` and the asset files). It does not need Python except as a local file server (`python serve.py`). GitHub Pages can host the same files later from the repo root. A project site URL would be `https://<user>.github.io/<repo>/` (redirects to `preview/`).

Do not publish yet. A private GitHub repo does **not** make a github.io site private: Free plans cannot enable Pages on private repos; Pro can, but the published site is public on the internet. Auth-gated Pages is GitHub Enterprise Cloud only. Font Awesome Pro webfonts in this tree must not go on a public Pages site.

---

## Pick, then use

1. Search. Do not guess.

```bash
python tools/search.py settings
python tools/search.py awp
python tools/search.py --kind font title
python tools/search.py gear --json
python tools/search.py --collection cs2 knife
```

2. If ranking is unclear, read `catalog/icons.json` (and `catalog/fonts.json` for type).
3. Return collection id, name, class and/or path, unicode when it is an icon font, and a one-line usage snippet.

### Default order

1. CS2 weapons, grenades, armor, kits → `cs2/equipment/<name>.svg`
2. Custom overlay set (crosshair, eye, globe, weapon, sliders, gear) → `CustomIconPackDOPAMINA.ttf` (`A`–`F` in `defs.txt`; font cmap is `U+F000`…)
3. General UI → Font Awesome 7.3 solid: `fa-solid fa-<name>`
4. Brand logos → `fa-brands fa-<name>`
5. Line/fill UI when a Remix name fits better → `remixicon.ttf` / `ri-<name>`
6. Type: Montserrat or Inter for UI, League Spartan / Oswald / Syne for titles, JetBrains Mono or Fira Code for code. More in `typefaces/`
7. Do not use FA 6 or FA 5 unless the consuming project is pinned to that version

---

## Icons

### Font Awesome Pro

Releases live under `releases/v7.3.0/`, `releases/v6.7.2/`, `releases/v5.15.4/`.

Prefer **7.3 solid** unless the project is already on another version.

```html
<link rel="stylesheet" href="releases/v7.3.0/css/fontawesome.css">
<link rel="stylesheet" href="releases/v7.3.0/css/solid.css">
<i class="fa-solid fa-gear"></i>
```

Other 7.3 styles are extra CSS plus extra classes, for example:

- regular → `regular.css` + `fa-regular fa-gear`
- brands → `brands.css` + `fa-brands fa-github`
- sharp solid → `sharp-solid.css` + `fa-sharp fa-solid fa-gear`
- duotone → `duotone.css` + `fa-duotone fa-gear`

Webfonts are next to the CSS: `releases/v7.3.0/webfonts/`.

### Remix Icon

File: `remixicon.ttf`. Names are in the `remix` collection in `catalog/icons.json` (`home-line`, `search-2-fill`, …).

```css
@font-face { font-family: RemixIcon; src: url("remixicon.ttf"); }
.ri { font-family: RemixIcon; }
```

Class form: `ri-<glyph-name>` (example `ri-home-line`). Confirm the name with search first.

### CS2 equipment

SVGs in `cs2/equipment/`. Use these for Counter-Strike weapons and utility. Do not replace them with a generic gun icon.

```html
<img src="cs2/equipment/awp.svg" alt="AWP">
```

They are white artwork. They read on dark surfaces.

### CustomIconPack DOPAMINA

File: `CustomIconPackDOPAMINA.ttf`. Intended keys from `defs.txt`:

| Key | Name |
| --- | --- |
| `A` | target / crosshair |
| `B` | eye |
| `C` | globe / earth |
| `D` | ak / weapon |
| `E` | sliders |
| `F` | gear / settings |

The font cmap stores those glyphs in the private-use area starting at `U+F000`. In overlay code, type `A`–`F` as `defs.txt` says. Search collection `dopamina` if you need the PUA code.

### Other icon fonts

- `iconsV2.ttf` — second custom pack. Inspect the glyph in the preview before using it.
- `tab_icon.ttf` — tiny, a few glyphs.
- `fa-solid-900(2).ttf` and `Font Awesome 7 Free-Solid-900.otf` — loose FA files. Prefer `releases/v7.3.0`.
- `fonts/*.hpp` — C++ embeds. Extracted copies: `preview/extracted/` (`weapons.ttf`, `pixel7.ttf`, `mochi.bdf`, `pretzel.bdf`).

---

## Fonts

Local files at the repo root stay the defaults. Extra open-source families live in `typefaces/<slug>/` (OFL / Apache / UFL, each folder keeps its license). Refresh with `python tools/download_open_fonts.py`, then `python tools/build_catalog.py`.

| Use | File | Family |
| --- | --- | --- |
| UI body / labels | `Montserrat-VariableFont_wght.ttf` or `typefaces/inter/` | Montserrat / Inter |
| UI italic | `Montserrat-Italic-VariableFont_wght.ttf` | Montserrat Italic |
| Static Montserrat cuts | `static/Montserrat-*.ttf` | when variable fonts cannot be used |
| Titles / display | `league-spartan-sb(1).ttf` or `typefaces/oswald/`, `typefaces/syne/` | League Spartan, Oswald, Syne |
| Dense small UI | `tahomabd.ttf` | Tahoma Bold |
| Readable small body | `verdana-regular.ttf` | Verdana Regular |
| Bold wide-coverage sans | `KlokanTechNotoSans-Bold(1).ttf` or `typefaces/notosans/` | Noto Sans |
| Code / logs | `typefaces/jetbrainsmono/`, `typefaces/firacode/` | JetBrains Mono, Fira Code |

```css
@font-face {
  font-family: Montserrat;
  src: url("Montserrat-VariableFont_wght.ttf") format("truetype");
  font-weight: 100 900;
}
```

Do not mix unrelated display faces in one UI. One family for UI, one for titles if needed.

Embedded bitmap fonts (`mochi`, `pretzel`) are BDF, not `@font-face` TTFs. Render from the catalog bitmaps or the C++ bytes in `fonts/*.hpp`.

---

## UI references

`Websites.txt` and `catalog/refs.json` are the same list. Open them before designing or implementing UI. The preview **Refs** tab lists them too.

| Site | Why |
| --- | --- |
| https://grainient.supply/collections | Real grain, dither, and textured backgrounds. Not generic glass. |
| https://animate-ui.com/ | Motion with a purpose. |
| https://transitions.dev/ | Page and view transitions that stay short and directed. |
| https://bklit.com/docs/components/area-chart | How a real data component is built. |

Do not ship AI slop: purple-blue gradients, glowing borders, oversized glass cards, emoji-as-icons, bounce on everything, fake SaaS dashboards. Use this library’s icons and fonts. Keep layout compact, type hierarchical, color semantic, motion rare.
