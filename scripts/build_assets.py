"""Download and prepare everything in assets/.

The results are committed, so this only needs re-running to refresh the assets
(for example after bumping one of the pinned versions below). Run it from the
repo root; it needs two packages on top of requirements.txt:

    pip install pyyaml==6.0.3 resvg-py==0.5.0
    python -m scripts.build_assets
"""

import json

import requests
import resvg_py
import yaml

from thumbgen.layout import (
    ASSETS_DIR,
    FONT_BOLD,
    FONT_CJK,
    FONT_EMOJI,
    FONT_KOREAN,
    FONT_REGULAR,
    FONTS_DIR,
    ICON_NAMES,
    ICONS_DIR,
    LANGUAGE_COLORS,
)

# Pinned upstream versions, so re-running gives the same files.
MONA_SANS = "https://raw.githubusercontent.com/github/mona-sans/v2.0.27"
NOTO_CJK = "https://raw.githubusercontent.com/notofonts/noto-cjk/Sans2.004"
NOTO_EMOJI = "https://raw.githubusercontent.com/google/fonts/8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5/ofl/notoemoji"
OCTICONS = "https://raw.githubusercontent.com/primer/octicons/%40primer/octicons%4019.41.0"  # tag "@primer/octicons@19.41.0"
LINGUIST = "https://raw.githubusercontent.com/github-linguist/linguist/v9.7.0"

# Icons are drawn at up to ~64px on the canvas; 2x that keeps them crisp when scaled down.
ICON_SIZE = 128


def download(url: str) -> bytes:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def build_fonts() -> None:
    for font in (FONT_REGULAR, FONT_BOLD):
        font.write_bytes(download(f"{MONA_SANS}/fonts/static/ttf/{font.name}"))
    (FONTS_DIR / "MonaSans-OFL.txt").write_bytes(download(f"{MONA_SANS}/OFL.txt"))

    # Fallbacks for characters Mona Sans doesn't have. The CJK fonts are the
    # region subsets, which are about half the size of the full Pan-CJK font.
    FONT_CJK.write_bytes(download(f"{NOTO_CJK}/Sans/SubsetOTF/SC/{FONT_CJK.name}"))
    FONT_KOREAN.write_bytes(download(f"{NOTO_CJK}/Sans/SubsetOTF/KR/{FONT_KOREAN.name}"))
    (FONTS_DIR / "NotoSansCJK-OFL.txt").write_bytes(download(f"{NOTO_CJK}/LICENSE"))
    FONT_EMOJI.write_bytes(download(f"{NOTO_EMOJI}/NotoEmoji%5Bwght%5D.ttf"))
    (FONTS_DIR / "NotoEmoji-OFL.txt").write_bytes(download(f"{NOTO_EMOJI}/OFL.txt"))


def build_icons() -> None:
    """Rasterise the 24px Octicons to black-on-transparent PNGs; the renderer recolours them."""
    for name in ICON_NAMES:
        svg = download(f"{OCTICONS}/icons/{name}-24.svg").decode()
        png = resvg_py.svg_to_bytes(svg_string=svg, width=ICON_SIZE, height=ICON_SIZE)
        (ICONS_DIR / f"{name}.png").write_bytes(png)
    (ICONS_DIR / "LICENSE.txt").write_bytes(download(f"{OCTICONS}/LICENSE"))


def build_language_colors() -> None:
    """Keep only ``{language name: "#rrggbb"}`` from Linguist's languages.yml."""
    languages = yaml.safe_load(download(f"{LINGUIST}/lib/linguist/languages.yml"))
    colors = {name: info["color"] for name, info in languages.items() if "color" in info}
    LANGUAGE_COLORS.write_text(json.dumps(colors, indent=2, sort_keys=True) + "\n")
    (ASSETS_DIR / "language_colors.LICENSE.txt").write_bytes(download(f"{LINGUIST}/LICENSE"))


def main() -> None:
    build_fonts()
    build_icons()
    build_language_colors()
    print(f"Assets written to {ASSETS_DIR}")


if __name__ == "__main__":
    main()
