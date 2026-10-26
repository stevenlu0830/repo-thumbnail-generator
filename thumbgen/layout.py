"""Sizes, colours and positions used by the renderer, plus where the assets live.

Positions are in pixels on the 1200×600 canvas and were measured from GitHub's
own social preview images (see example.jpg and example2.jpg).
"""

from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
ICONS_DIR = ASSETS_DIR / "icons"

FONT_REGULAR = FONTS_DIR / "MonaSans-Regular.ttf"
FONT_BOLD = FONTS_DIR / "MonaSans-Bold.ttf"
LANGUAGE_COLORS = ASSETS_DIR / "language_colors.json"

# Fallbacks for characters Mona Sans doesn't have, tried in this order.
FONT_EMOJI = FONTS_DIR / "NotoEmoji.ttf"
FONT_CJK = FONTS_DIR / "NotoSansSC-Regular.otf"  # Chinese (simplified and traditional) and Japanese
FONT_KOREAN = FONTS_DIR / "NotoSansKR-Regular.otf"
FALLBACK_FONTS = (FONT_EMOJI, FONT_CJK, FONT_KOREAN)

ICON_NAMES = ("people", "issue-opened", "star", "repo-forked", "mark-github")

# Same size as GitHub's own social preview images.
CANVAS_SIZE = (1200, 600)
WIDTH, HEIGHT = CANVAS_SIZE
MARGIN_X = 100

# Colours (GitHub's Primer palette)
BACKGROUND = "#ffffff"
TEXT_COLOR = "#1f2328"
MUTED_COLOR = "#656d76"  # description, stat labels and icons
SUBTLE_COLOR = "#848d97"  # GitHub logo
PLACEHOLDER_COLOR = "#eaeef2"  # stands in for an avatar that couldn't be downloaded
UNKNOWN_LANGUAGE_COLOR = "#cccccc"

# Avatar, top right
AVATAR_SIZE = 192
AVATAR_TOP = 106
AVATAR_RADIUS = 16
AVATAR_LEFT = WIDTH - MARGIN_X - AVATAR_SIZE

# Title and description wrap within this width, leaving a gap before the avatar.
TEXT_MAX_WIDTH = 720

# Title: "owner/" in regular weight, "repo" in bold. Longer titles get a smaller
# font (size ≈ TITLE_SIZE_FACTOR / number of characters, kept within the limits).
TITLE_TOP = 100
TITLE_MAX_SIZE = 76
TITLE_MIN_SIZE = 40
TITLE_SIZE_FACTOR = 1680
TITLE_LINE_HEIGHT = 1.19  # × font size
TITLE_MAX_LINES = 3

# Description, below the title
DESCRIPTION_SIZE = 31
DESCRIPTION_LINE_HEIGHT = 47
DESCRIPTION_GAP = 24  # between the title's descenders and the description's ascenders
DESCRIPTION_MAX_LINES = 3

# Stats row: icon, then a number with a label underneath, one column per stat.
STATS_TOP = 467
STAT_ICON_SIZE = 31
STAT_TEXT_OFFSET = 47  # from the icon's left edge to the number's left edge
STAT_COLUMN_GAP = 48  # from the end of one column's text to the next icon
STAT_NUMBER_SIZE = 41
STAT_NUMBER_BASELINE = 497
STAT_LABEL_SIZE = 22
STAT_LABEL_BASELINE = 529
# Shown when GitHub's API won't count contributors (very large repos, e.g. torvalds/linux).
UNCOUNTED_NUMBER = "5k+"

# GitHub logo, bottom right, centred on the stats row
GITHUB_MARK_SIZE = 46
GITHUB_MARK_CENTER_Y = 496

LANGUAGE_BAR_HEIGHT = 22
LANGUAGE_MIN_WIDTH = 6  # so even a tiny share of the code stays visible
