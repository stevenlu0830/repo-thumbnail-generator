"""Sizes, colours and positions used by the renderer, plus where the assets live."""

from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
ICONS_DIR = ASSETS_DIR / "icons"

FONT_REGULAR = FONTS_DIR / "MonaSans-Regular.ttf"
FONT_BOLD = FONTS_DIR / "MonaSans-Bold.ttf"
LANGUAGE_COLORS = ASSETS_DIR / "language_colors.json"

ICON_NAMES = ("people", "issue-opened", "star", "repo-forked", "mark-github")

# Same size as GitHub's own social preview images.
CANVAS_SIZE = (1200, 600)
