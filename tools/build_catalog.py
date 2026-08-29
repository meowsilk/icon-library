#!/usr/bin/env python3
"""Build catalog JSON for the preview app and AI search."""

from __future__ import annotations

import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog"
PREVIEW = ROOT / "preview"
ICONS = ROOT / "icons"
EMBEDS = ROOT / "embeds"

CSS_ICON_RE = re.compile(
    r"((?:\.fa-[a-zA-Z0-9-]+)+)\{[^}]*?--fa:((?:\"[^\"]*\"|'[^']*'))"
)
CSS_V5_ICON_RE = re.compile(
    r"((?:\.fa-[a-zA-Z0-9-]+)+):before\{content:((?:\"[^\"]*\"|'[^']*'))\}"
)
STYLE_CLASS_RE = re.compile(r"\.(fa-[a-z0-9-]+)")
FAMILY_RE = re.compile(r'--fa-family-[a-z0-9-]+:"([^"]+)"')
WEIGHT_RE = re.compile(r"font-weight:(\d+)")
SRC_RE = re.compile(r"src:url\(([^)]+)\)")
HPP_ARRAY_RE = re.compile(
    r"inline unsigned char (\w+)\[\s*(\d+)\s*\]\s*\{([^}]+)\}",
    re.S,
)


def css_escape_to_cp(raw: str) -> int | None:
    raw = raw.strip().strip("\"'")
    if not raw:
        return None
    if raw[0] != "\\":
        return ord(raw[0])
    body = raw[1:]
    hex_part = ""
    for ch in body:
        if ch in "0123456789abcdefABCDEF":
            hex_part += ch
            if len(hex_part) == 6:
                break
        else:
            break
    if hex_part:
        return int(hex_part, 16)
    if body:
        return ord(body[0])
    return None


def parse_icon_rules(css: str, version5: bool = False) -> list[dict]:
    regex = CSS_V5_ICON_RE if version5 else CSS_ICON_RE
    by_cp: dict[int, list[str]] = {}
    for selectors, content in regex.findall(css):
        cp = css_escape_to_cp(content)
        if cp is None:
            continue
        names = [s[4:] for s in selectors.split(",") if s.startswith(".fa-")]
        names = [n for n in names if n]
        if not names:
            continue
        bucket = by_cp.setdefault(cp, [])
        for name in names:
            if name not in bucket:
                bucket.append(name)
    icons = []
    for cp, names in by_cp.items():
        primary = min(names, key=lambda n: (len(n), n))
        aliases = [n for n in names if n != primary]
        icons.append(
            {
                "name": primary,
                "aliases": aliases,
                "unicode": f"{cp:04x}",
            }
        )
    icons.sort(key=lambda i: i["name"])
    return icons


def fa_icon_class(stem: str, version: str) -> str:
    if version.startswith("5."):
        return {
            "solid": "fas",
            "regular": "far",
            "light": "fal",
            "duotone": "fad",
            "brands": "fab",
        }.get(stem, f"fa-{stem}")
    if stem in ("brands", "duotone"):
        return f"fa-{stem}"
    weights = ("semibold", "solid", "regular", "light", "thin")
    if stem in weights:
        return f"fa-{stem}"
    for weight in weights:
        suffix = f"-{weight}"
        if stem.endswith(suffix):
            return f"fa-{stem[:-len(suffix)]} fa-{weight}"
    return f"fa-{stem}"


def parse_fa_style(css_path: Path, version: str) -> dict:
    text = css_path.read_text(encoding="utf-8", errors="replace")
    families = FAMILY_RE.findall(text)
    weights = WEIGHT_RE.findall(text)
    srcs = SRC_RE.findall(text)
    return {
        "id": css_path.stem,
        "label": css_path.stem.replace("-", " ").title(),
        "css": css_path.name,
        "iconClass": fa_icon_class(css_path.stem, version),
        "fontFamily": families[0] if families else None,
        "weight": int(weights[0]) if weights else None,
        "webfont": srcs[0].replace("../", "") if srcs else None,
        "brand": "brand" in css_path.stem,
    }


def load_fa_release(version: str) -> dict:
    rel = ICONS / "fontawesome" / f"v{version}"
    css_dir = rel / "css"
    core = (css_dir / "fontawesome.css").read_text(encoding="utf-8", errors="replace")
    version5 = version.startswith("5.")
    icons = parse_icon_rules(core, version5=version5)
    styles = []
    for css_path in sorted(css_dir.glob("*.css")):
        if css_path.name == "fontawesome.css":
            continue
        styles.append(parse_fa_style(css_path, version))
    brand_names = set()
    brands_css = css_dir / "brands.css"
    if brands_css.exists():
        brand_icons = parse_icon_rules(
            brands_css.read_text(encoding="utf-8", errors="replace"),
            version5=version5,
        )
        brand_names = {i["name"] for i in brand_icons}
        for i in brand_icons:
            brand_names.update(i["aliases"])
    for icon in icons:
        icon["brand"] = icon["name"] in brand_names or any(a in brand_names for a in icon["aliases"])
    return {
        "id": f"fa-{version}",
        "name": f"Font Awesome {version}",
        "kind": "fa",
        "version": version,
        "cssBase": f"icons/fontawesome/v{version}/css/",
        "coreCss": "fontawesome.css",
        "styles": styles,
        "icons": icons,
    }


def u16(data: bytes, off: int) -> int:
    return struct.unpack_from(">H", data, off)[0]


def u32(data: bytes, off: int) -> int:
    return struct.unpack_from(">I", data, off)[0]


def i16(data: bytes, off: int) -> int:
    return struct.unpack_from(">h", data, off)[0]


def read_ttf_tables(data: bytes) -> dict[str, bytes]:
    num = u16(data, 4)
    tables = {}
    for i in range(num):
        rec = 12 + i * 16
        tag = data[rec : rec + 4].decode("ascii", errors="replace")
        offset = u32(data, rec + 8)
        length = u32(data, rec + 12)
        tables[tag] = data[offset : offset + length]
    return tables


def parse_name_table(blob: bytes) -> dict[str, str]:
    if len(blob) < 6:
        return {}
    count = u16(blob, 2)
    storage = u16(blob, 4)
    wanted = {1: "family", 2: "subfamily", 4: "full", 6: "postscript"}
    out: dict[str, str] = {}
    for i in range(count):
        rec = 6 + i * 12
        if rec + 12 > len(blob):
            break
        platform, encoding, lang, name_id, length, offset = struct.unpack_from(">HHHHHH", blob, rec)
        if name_id not in wanted:
            continue
        start = storage + offset
        raw = blob[start : start + length]
        if platform == 3 or (platform == 0):
            text = raw.decode("utf-16-be", errors="replace")
        else:
            text = raw.decode("latin-1", errors="replace")
        key = wanted[name_id]
        if key not in out or (platform == 3 and lang == 0x0409):
            out[key] = text
    return out


def parse_cmap(blob: bytes) -> dict[int, int]:
    if len(blob) < 4:
        return {}
    num = u16(blob, 2)
    mapping: dict[int, int] = {}
    records = []
    for i in range(num):
        rec = 4 + i * 8
        platform, encoding, offset = struct.unpack_from(">HHI", blob, rec)
        records.append((platform, encoding, offset))
    preferred = [r for r in records if r[0] == 3 and r[1] in (1, 10)]
    preferred += [r for r in records if r[0] == 0]
    preferred += records
    seen_off = set()
    for _, _, offset in preferred:
        if offset in seen_off or offset + 2 > len(blob):
            continue
        seen_off.add(offset)
        fmt = u16(blob, offset)
        if fmt == 4:
            mapping.update(_cmap_fmt4(blob, offset))
        elif fmt == 12:
            mapping.update(_cmap_fmt12(blob, offset))
        elif fmt == 6:
            mapping.update(_cmap_fmt6(blob, offset))
    return mapping


def _cmap_fmt4(blob: bytes, offset: int) -> dict[int, int]:
    length = u16(blob, offset + 2)
    seg_count = u16(blob, offset + 6) // 2
    end_off = offset + 14
    start_off = end_off + 2 + seg_count * 2
    delta_off = start_off + seg_count * 2
    range_off = delta_off + seg_count * 2
    out = {}
    for i in range(seg_count):
        end = u16(blob, end_off + i * 2)
        start = u16(blob, start_off + i * 2)
        delta = i16(blob, delta_off + i * 2)
        range_offset = u16(blob, range_off + i * 2)
        for cp in range(start, end + 1):
            if range_offset == 0:
                gid = (cp + delta) & 0xFFFF
            else:
                loc = range_off + i * 2 + range_offset + (cp - start) * 2
                if loc + 2 > offset + length:
                    continue
                gid = u16(blob, loc)
                if gid != 0:
                    gid = (gid + delta) & 0xFFFF
            if gid:
                out[cp] = gid
    return out


def _cmap_fmt6(blob: bytes, offset: int) -> dict[int, int]:
    first = u16(blob, offset + 6)
    count = u16(blob, offset + 8)
    out = {}
    for i in range(count):
        gid = u16(blob, offset + 10 + i * 2)
        if gid:
            out[first + i] = gid
    return out


def _cmap_fmt12(blob: bytes, offset: int) -> dict[int, int]:
    n_groups = u32(blob, offset + 12)
    out = {}
    for i in range(n_groups):
        rec = offset + 16 + i * 12
        start_cp, end_cp, start_gid = struct.unpack_from(">III", blob, rec)
        for n, cp in enumerate(range(start_cp, end_cp + 1)):
            gid = start_gid + n
            if gid:
                out[cp] = gid
    return out


def parse_post_names(blob: bytes) -> dict[int, str]:
    if len(blob) < 32:
        return {}
    fmt = struct.unpack_from(">i", blob, 0)[0]
    if fmt != 0x00020000:
        return {}
    num_glyphs = u16(blob, 32)
    gids = [u16(blob, 34 + i * 2) for i in range(num_glyphs)]
    pascal_off = 34 + num_glyphs * 2
    extras: list[str] = []
    p = pascal_off
    while p < len(blob):
        n = blob[p]
        p += 1
        extras.append(blob[p : p + n].decode("latin-1", errors="replace"))
        p += n
    mac = MAC_STANDARD
    names = {}
    for gid, idx in enumerate(gids):
        if idx < 258:
            if idx < len(mac):
                names[gid] = mac[idx]
        else:
            extra_i = idx - 258
            if extra_i < len(extras):
                names[gid] = extras[extra_i]
    return names


MAC_STANDARD = [
    ".notdef", ".null", "nonmarkingreturn", "space", "exclam", "quotedbl",
    "numbersign", "dollar", "percent", "ampersand", "quotesingle", "parenleft",
    "parenright", "asterisk", "plus", "comma", "hyphen", "period", "slash",
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "colon", "semicolon", "less", "equal", "greater", "question", "at",
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O",
    "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "bracketleft",
    "backslash", "bracketright", "asciicircum", "underscore", "grave", "a", "b",
    "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q",
    "r", "s", "t", "u", "v", "w", "x", "y", "z", "braceleft", "bar", "braceright",
    "asciitilde",
] + [f"mac{i}" for i in range(96, 258)]


def inspect_font(path: Path) -> dict:
    data = path.read_bytes()
    if data.startswith(b"STARTFONT"):
        return inspect_bdf(data, path.stem)
    if len(data) < 28 or data[0:4] not in (b"\x00\x01\x00\x00", b"OTTO", b"true"):
        return {
            "family": path.stem,
            "full": path.stem,
            "subfamily": None,
            "postscript": None,
            "format": "unknown",
            "glyphs": [],
            "glyphCount": 0,
        }
    tables = read_ttf_tables(data)
    names = parse_name_table(tables.get("name", b""))
    cmap = parse_cmap(tables.get("cmap", b""))
    post = parse_post_names(tables.get("post", b""))
    glyphs = []
    for cp, gid in sorted(cmap.items()):
        if cp < 32:
            continue
        name = post.get(gid) or f"u{cp:04x}"
        if name in (".notdef", ".null", "nonmarkingreturn", "space"):
            continue
        glyphs.append({"name": name, "unicode": f"{cp:04x}", "gid": gid})
    return {
        "family": names.get("family") or path.stem,
        "full": names.get("full") or names.get("family") or path.stem,
        "subfamily": names.get("subfamily"),
        "postscript": names.get("postscript"),
        "format": "ttf",
        "glyphs": glyphs,
        "glyphCount": len(glyphs),
    }


def inspect_bdf(data: bytes, fallback: str) -> dict:
    text = data.decode("latin-1", errors="replace")
    family = fallback
    fm = re.search(r"^FONT\s+(.+)$", text, re.M)
    if fm:
        family = fm.group(1).strip()
    glyphs = []
    for block in re.finditer(
        r"STARTCHAR\s+(\S+)\s+.*?ENCODING\s+(-?\d+)\s+.*?BBX\s+(\d+)\s+(\d+)\s+(-?\d+)\s+(-?\d+)\s+.*?BITMAP\s+([0-9A-Fa-f\s]+?)ENDCHAR",
        text,
        re.S,
    ):
        name, enc_s, w, h, x, y, bitmap = block.groups()
        enc = int(enc_s)
        if enc < 0:
            continue
        rows = [r.strip() for r in bitmap.splitlines() if r.strip()]
        glyphs.append(
            {
                "name": name,
                "unicode": f"{enc:04x}",
                "bbx": [int(w), int(h), int(x), int(y)],
                "bitmap": rows,
            }
        )
    return {
        "family": family,
        "full": family,
        "subfamily": None,
        "postscript": None,
        "format": "bdf",
        "glyphs": glyphs,
        "glyphCount": len(glyphs),
    }


def parse_defs(path: Path) -> list[dict]:
    icons = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        label, rest = line.split(":", 1)
        m = re.search(r"U\+([0-9A-Fa-f]+)", rest)
        if not m:
            continue
        name = re.sub(r"\s+def$", "", label.strip(), flags=re.I)
        cp = int(m.group(1), 16)
        icons.append(
            {
                "name": name,
                "aliases": [],
                "unicode": f"{cp:04x}",
            }
        )
    return icons


def extract_hpp_fonts() -> list[dict]:
    out_dir = EMBEDS / "extracted"
    out_dir.mkdir(parents=True, exist_ok=True)
    fonts = []
    for hpp in sorted(EMBEDS.glob("*.hpp")):
        text = hpp.read_text(encoding="utf-8", errors="replace")
        m = HPP_ARRAY_RE.search(text)
        if not m:
            continue
        name, size_s, body = m.groups()
        hexes = re.findall(r"0x([0-9A-Fa-f]{2})", body)
        data = bytes(int(h, 16) for h in hexes)
        fmt = "bdf" if data.startswith(b"STARTFONT") else "ttf"
        dest = out_dir / f"{name}.{fmt}"
        dest.write_bytes(data)
        info = inspect_font(dest)
        rel = dest.relative_to(ROOT).as_posix()
        kind = "bdf" if fmt == "bdf" else "icon-or-ui"
        fonts.append(
            {
                "id": f"embedded-{name}",
                "name": name,
                "kind": kind,
                "path": rel,
                "source": f"embeds/{hpp.name}",
                "family": info["family"],
                "subfamily": info["subfamily"],
                "glyphCount": info["glyphCount"],
                "format": info.get("format"),
                "use": f"Embedded C++ {fmt} from embeds/{hpp.name}",
            }
        )
        icons = []
        for g in info["glyphs"]:
            icon = {"name": g["name"], "aliases": [], "unicode": g["unicode"]}
            if "bitmap" in g:
                icon["bbx"] = g["bbx"]
                icon["bitmap"] = g["bitmap"]
            icons.append(icon)
        fonts[-1]["_collection"] = {
            "id": f"embedded-{name}",
            "name": f"{name} embedded",
            "kind": "bdf" if fmt == "bdf" else "iconfont",
            "fontUrl": rel,
            "fontFamily": f"Embedded {info['family']}",
            "useWhen": f"C++ embed from embeds/{hpp.name}.",
            "icons": icons,
        }
    return fonts


def text_font_entry(path: Path, **extra) -> dict:
    info = inspect_font(path)
    entry = {
        "id": slug(path.stem),
        "name": extra.pop("name", info["full"]),
        "kind": extra.pop("kind", "text"),
        "path": path.relative_to(ROOT).as_posix(),
        "family": extra.pop("family", info["family"]),
        "subfamily": info["subfamily"],
        "glyphCount": info["glyphCount"],
    }
    entry.update(extra)
    return entry


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    CATALOG.mkdir(exist_ok=True)
    PREVIEW.mkdir(exist_ok=True)

    collections = []

    fa73 = load_fa_release("7.3.0")
    fa73["name"] = "Font Awesome Pro 7.3"
    fa73["useWhen"] = "Default UI icons. Prefer solid for overlays and dense tools."
    collections.append(fa73)

    fa67 = load_fa_release("6.7.2")
    fa67["name"] = "Font Awesome Pro 6.7"
    fa67["useWhen"] = "Only when a project is pinned to FA 6."
    collections.append(fa67)

    fa5 = load_fa_release("5.15.4")
    fa5["name"] = "Font Awesome Pro 5.15"
    fa5["useWhen"] = "Only when a project is pinned to FA 5."
    collections.append(fa5)

    remix_path = ICONS / "remix" / "remixicon.ttf"
    remix = inspect_font(remix_path)
    remix_col = {
        "id": "remix",
        "name": "Remix Icon",
        "kind": "iconfont",
        "fontUrl": remix_path.relative_to(ROOT).as_posix(),
        "fontFamily": "RemixIcon Library",
        "useWhen": "Line/fill UI icons when FA feels too heavy or a Remix name fits better.",
        "icons": [{"name": g["name"], "aliases": [], "unicode": g["unicode"]} for g in remix["glyphs"]],
    }
    collections.append(remix_col)

    dop_path = ICONS / "custom" / "dopamina.ttf"
    dopamina = inspect_font(dop_path)
    defs = parse_defs(ICONS / "custom" / "defs.txt")
    dop_icons = []
    for g in dopamina["glyphs"]:
        dop_icons.append({"name": g["name"], "aliases": [], "unicode": g["unicode"]})
    pua = [i for i in dop_icons if int(i["unicode"], 16) >= 0xF000]
    for i, mapped in enumerate(defs):
        if i >= len(pua):
            break
        letter = chr(int(mapped["unicode"], 16))
        pua[i]["name"] = mapped["name"]
        pua[i]["aliases"] = [letter, f"U+{mapped['unicode'].upper()}", mapped["unicode"]]
        pua[i]["input"] = letter
    collections.append(
        {
            "id": "dopamina",
            "name": "CustomIconPack DOPAMINA",
            "kind": "iconfont",
            "fontUrl": dop_path.relative_to(ROOT).as_posix(),
            "fontFamily": "CustomIconPack DOPAMINA",
            "useWhen": "Custom overlay pack. Known map: A crosshair, B eye, C globe, D weapon, E sliders, F gear.",
            "icons": dop_icons,
        }
    )

    for path, label, when in (
        (ICONS / "custom" / "iconsv2.ttf", "iconsV2", "Second custom icon font. Inspect glyphs before using."),
        (ICONS / "custom" / "tab.ttf", "tab_icon", "Tiny custom font, likely a single tab glyph."),
        (ICONS / "fontawesome" / "loose" / "fa-solid-900.ttf", "FA Solid 900 (loose TTF)", "Loose FA solid file. Prefer icons/fontawesome/v7.3.0."),
        (ICONS / "fontawesome" / "loose" / "fa-7-free-solid-900.otf", "FA 7 Free Solid", "Free solid subset. Prefer Pro 7.3 in this library."),
    ):
        if not path.exists():
            continue
        info = inspect_font(path)
        collections.append(
            {
                "id": slug(label),
                "name": label,
                "kind": "iconfont",
                "fontUrl": path.relative_to(ROOT).as_posix(),
                "fontFamily": f"Lib {info['family']}",
                "useWhen": when,
                "icons": [{"name": g["name"], "aliases": [], "unicode": g["unicode"]} for g in info["glyphs"]],
            }
        )

    cs2 = []
    for svg in sorted((ICONS / "cs2" / "equipment").glob("*.svg")):
        name = svg.stem
        tags = [p for p in name.split("_") if p]
        cs2.append(
            {
                "name": name,
                "aliases": tags,
                "path": svg.relative_to(ROOT).as_posix(),
            }
        )
    collections.append(
        {
            "id": "cs2",
            "name": "CS2 Equipment",
            "kind": "svg",
            "useWhen": "Counter-Strike weapon, grenade, armor, and utility art. Always prefer these over generic gun icons.",
            "icons": cs2,
        }
    )

    fonts = []
    typefaces_root = ROOT / "typefaces"
    if typefaces_root.exists():
        for font_file in sorted(typefaces_root.rglob("*")):
            if font_file.suffix.lower() not in {".ttf", ".otf"}:
                continue
            rel_parts = font_file.relative_to(typefaces_root).parts
            if any(part.lower() == "static" for part in rel_parts[:-1]):
                continue
            family_dir = rel_parts[0]
            meta = (typefaces_root / family_dir / "METADATA.pb").read_text(encoding="utf-8", errors="replace") if (typefaces_root / family_dir / "METADATA.pb").exists() else ""
            category = "SANS_SERIF"
            m = re.search(r'category:\s*"([^"]+)"', meta)
            if m:
                category = m.group(1)
            display = family_dir
            n = re.search(r'name:\s*"([^"]+)"', meta)
            if n:
                display = n.group(1)
            lower = f"{display} {font_file.stem}".lower()
            if any(k in lower for k in ("mono", "code", "inconsolata")):
                use = "Monospace. Code, logs, numeric UI."
            elif category == "DISPLAY" or any(k in lower for k in ("bebas", "anton", "oswald", "syne", "unbounded", "orbitron")):
                use = "Display / titles."
            elif category == "SERIF" or "serif" in lower:
                use = "Serif. Long text and editorial UI."
            elif category == "HANDWRITING":
                use = "Handwriting / informal labels."
            elif "condensed" in lower:
                use = "Condensed UI / dense labels."
            elif any(k in lower for k in ("press start", "silkscreen", "vt323", "pixel")):
                use = "Pixel / retro display."
            else:
                use = "Open-source UI sans."
            kind = "variable" if "[" in font_file.stem or "Variable" in font_file.stem else "static"
            fonts.append(
                text_font_entry(
                    font_file,
                    name=font_file.stem.replace("[", " ").replace("]", " ").replace(",", " "),
                    family=display,
                    kind=kind,
                    license="open-source",
                    source=f"typefaces/{family_dir}",
                    use=use,
                )
            )

    embedded = extract_hpp_fonts()
    for emb in embedded:
        col = emb.pop("_collection", None)
        if col:
            collections.append(col)
    fonts.extend(embedded)

    rules = [
        "CS2 weapons, grenades, armor, kits → collection cs2 (SVG paths under icons/cs2/equipment/).",
        "Custom overlay set (crosshair, eye, globe, weapon, sliders, gear) → dopamina / icons/custom/dopamina.ttf, codes A–F from icons/custom/defs.txt.",
        "General UI icons → fa-7.3.0, style solid, class `fa-solid fa-<name>`. CSS in icons/fontawesome/v7.3.0/.",
        "Brand logos → fa-7.3.0 style brands, class `fa-brands fa-<name>`.",
        "Lighter line icons → remix (icons/remix/remixicon.ttf) when a Remix name is a better match.",
        "Do not use FA 6/5 unless the consuming project is pinned to that version.",
        "UI text → Montserrat or Inter. Titles → League Spartan, Oswald, or Syne. Dense small UI → Tahoma Bold or Verdana. Code → JetBrains Mono or Fira Code. Faces live in typefaces/.",
        "C++ embeds live in embeds/*.hpp; extracted copies are embeds/extracted/.",
    ]
    write_json(
        CATALOG / "icons.json",
        {
            "name": "ff0l icon library",
            "search": "python tools/search.py <query>",
            "preview": "python serve.py",
            "rules": rules,
            "collections": collections,
        },
    )
    write_json(
        CATALOG / "fonts.json",
        {
            "name": "ff0l icon library",
            "search": "python tools/search.py --kind font <query>",
            "fonts": fonts,
        },
    )

    stale = [CATALOG / "preview.json", CATALOG / "index.json"]
    sets_dir = CATALOG / "sets"
    if sets_dir.exists():
        for leftover in sets_dir.glob("*.json"):
            leftover.unlink()
        try:
            sets_dir.rmdir()
        except OSError:
            pass
    for path in stale:
        if path.exists():
            path.unlink()

    print("collections:")
    for c in collections:
        print(f"  {c['id']:28} {len(c.get('icons', [])):5} {c['kind']}")
    print(f"fonts: {len(fonts)}")
    print(f"wrote {CATALOG / 'icons.json'}")
    print(f"wrote {CATALOG / 'fonts.json'}")


if __name__ == "__main__":
    main()
