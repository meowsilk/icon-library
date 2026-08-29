#!/usr/bin/env python3
"""Download extra typeface families into typefaces/."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "typefaces"
CACHE = ROOT / ".cache" / "google-fonts"
REPO = "https://github.com/google/fonts.git"

# (license_dir, family_slug)
FAMILIES = [
    ("ofl", "inter"),
    ("ofl", "opensans"),
    ("ofl", "sourcesans3"),
    ("ofl", "nunito"),
    ("ofl", "nunitosans"),
    ("ofl", "worksans"),
    ("ofl", "dmsans"),
    ("ofl", "outfit"),
    ("ofl", "figtree"),
    ("ofl", "plusjakartasans"),
    ("ofl", "manrope"),
    ("ofl", "urbanist"),
    ("ofl", "ibmplexsans"),
    ("ofl", "ibmplexsanscondensed"),
    ("ofl", "ptsans"),
    ("ofl", "rubik"),
    ("ofl", "karla"),
    ("ofl", "librefranklin"),
    ("ofl", "atkinsonhyperlegible"),
    ("ofl", "atkinsonhyperlegiblenext"),
    ("ofl", "barlow"),
    ("ofl", "barlowcondensed"),
    ("ofl", "archivo"),
    ("ofl", "publicsans"),
    ("ofl", "sora"),
    ("ofl", "lexend"),
    ("ofl", "redhatdisplay"),
    ("ofl", "redhattext"),
    ("ofl", "schibstedgrotesk"),
    ("ofl", "bricolagegrotesque"),
    ("ofl", "instrumentsans"),
    ("ofl", "spacegrotesk"),
    ("ofl", "syne"),
    ("ofl", "unbounded"),
    ("ofl", "oswald"),
    ("ofl", "bebasneue"),
    ("ofl", "anton"),
    ("ofl", "playfairdisplay"),
    ("ofl", "fraunces"),
    ("ofl", "sourceserif4"),
    ("ofl", "lora"),
    ("ofl", "merriweather"),
    ("ofl", "ebgaramond"),
    ("ofl", "crimsonpro"),
    ("ofl", "librebaskerville"),
    ("ofl", "literata"),
    ("ofl", "newsreader"),
    ("ofl", "spectral"),
    ("ofl", "instrumentserif"),
    ("ofl", "cormorantgaramond"),
    ("ofl", "vollkorn"),
    ("ofl", "alegreya"),
    ("ofl", "alegreyasans"),
    ("ofl", "jetbrainsmono"),
    ("ofl", "sourcecodepro"),
    ("ofl", "firacode"),
    ("ofl", "ibmplexmono"),
    ("ofl", "robotomono"),
    ("ofl", "inconsolata"),
    ("ofl", "spacemono"),
    ("ofl", "anonymouspro"),
    ("ofl", "redhatmono"),
    ("ofl", "sharetechmono"),
    ("ofl", "cascadiamono"),
    ("ofl", "cascadiacode"),
    ("ofl", "geist"),
    ("ofl", "geistmono"),
    ("ofl", "mulish"),
    ("ofl", "cabin"),
    ("ofl", "exo2"),
    ("ofl", "questrial"),
    ("ofl", "josefinsans"),
    ("ofl", "poppins"),
    ("ofl", "raleway"),
    ("ofl", "quicksand"),
    ("ofl", "comfortaa"),
    ("ofl", "orbitron"),
    ("ofl", "vt323"),
    ("ofl", "pressstart2p"),
    ("ofl", "silkscreen"),
    ("ofl", "kanit"),
    ("ofl", "onest"),
    ("ofl", "roboto"),
    ("apache", "robotoslab"),
    ("ufl", "ubuntu"),
    ("ufl", "ubuntumono"),
    ("ofl", "firasans"),
    ("ofl", "overpass"),
    ("ofl", "overpassmono"),
    ("ofl", "ibmplexserif"),
    ("ofl", "notosans"),
    ("ofl", "notoserif"),
    ("ofl", "notosansmono"),
    ("ofl", "lato"),
    ("ofl", "dmsans"),
    ("ofl", "dmserifdisplay"),
    ("ofl", "dmseriftext"),
    ("ofl", "bitter"),
    ("ofl", "arvo"),
    ("ofl", "zillaslab"),
    ("ofl", "chivo"),
    ("ofl", "heebo"),
    ("ofl", "titilliumweb"),
    ("ofl", "yanonekaffeesatz"),
    ("ofl", "russoone"),
    ("ofl", "abrilfatface"),
    ("ofl", "cinzel"),
    ("ofl", "bodonimoda"),
    ("ofl", "recursive"),
    ("ofl", "caveat"),
    ("ofl", "permanentmarker"),
    ("ofl", "comicneue"),
    ("ofl", "hind"),
    ("ofl", "mukta"),
    ("ofl", "assistant"),
    ("ofl", "catamaran"),
    ("ofl", "cardo"),
    ("ofl", "gentiumbookplus"),
    ("ofl", "leaguespartan"),
    ("ofl", "montserrat"),
    ("ofl", "dosis"),
    ("ofl", "mavenpro"),
    ("ofl", "oxygen"),
    ("ofl", "ptserif"),
    ("ofl", "notosansdisplay"),
    ("ofl", "ibmplexmath"),
    ("ofl", "fragmentmono"),
    ("ofl", "commitmono"),
    ("ofl", "iosevkaterm"),
    ("ofl", "lilex"),
    ("ofl", "martianmono"),
    ("ofl", "redditmono"),
    ("ofl", "redditSans"),
    ("ofl", "redditsans"),
    ("ofl", "bricolagegrotesque"),
]

KEEP_EXT = {".ttf", ".otf"}
KEEP_NAME = {
    "ofl.txt",
    "ufl.txt",
    "license.txt",
    "licence.txt",
    "apache license.txt",
    "metadata.pb",
}
SKIP_DIRS = {"article", "static", "description"}


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def ensure_sparse_clone(paths: list[str]) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    if not (CACHE / ".git").exists():
        print("cloning google/fonts (sparse)...", flush=True)
        run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--sparse",
                REPO,
                str(CACHE),
            ]
        )
    print(f"sparse-checkout {len(paths)} families...", flush=True)
    run(["git", "sparse-checkout", "set", "--no-cone", *paths], cwd=CACHE)


def should_keep(name: str) -> bool:
    lower = name.lower()
    suffix = Path(lower).suffix
    if suffix in KEEP_EXT:
        return True
    return lower in KEEP_NAME


def copy_family(src: Path, dest: Path) -> int:
    if not src.is_dir():
        return 0
    copied = 0
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        rel_parts = item.relative_to(src).parts
        if any(part.lower() in SKIP_DIRS for part in rel_parts[:-1]):
            continue
        if not should_keep(item.name):
            continue
        out = dest / item.name
        dest.mkdir(parents=True, exist_ok=True)
        if out.exists() and out.stat().st_size > 0:
            copied += 1
            continue
        shutil.copy2(item, out)
        print(f"  {out.relative_to(ROOT)}  {out.stat().st_size}", flush=True)
        copied += 1
    return copied


def main() -> int:
    seen: set[tuple[str, str]] = set()
    families: list[tuple[str, str]] = []
    for license_dir, slug in FAMILIES:
        slug = slug.replace(" ", "").lower()
        key = (license_dir, slug)
        if key in seen:
            continue
        seen.add(key)
        families.append(key)

    repo_paths = [f"{license_dir}/{slug}" for license_dir, slug in families]
    ensure_sparse_clone(repo_paths)

    DEST.mkdir(parents=True, exist_ok=True)
    ok = 0
    missing: list[str] = []
    total_files = 0
    for license_dir, slug in families:
        dest = DEST / slug
        print(f"{license_dir}/{slug}", flush=True)
        files = copy_family(CACHE / license_dir / slug, dest)
        if files == 0:
            if dest.exists() and dest.is_dir() and not any(dest.iterdir()):
                dest.rmdir()
            missing.append(f"{license_dir}/{slug}")
            print("  missing", flush=True)
            continue
        ok += 1
        total_files += files

    # Drop redundant static cuts left from the API downloader.
    static_dir = DEST / "inconsolata" / "static"
    if static_dir.exists():
        shutil.rmtree(static_dir)
        print("removed typefaces/inconsolata/static", flush=True)

    print(f"downloaded {ok} families, {total_files} files", flush=True)
    if missing:
        print("missing:", ", ".join(missing), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
