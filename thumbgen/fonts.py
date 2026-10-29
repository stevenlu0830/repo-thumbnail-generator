"""Loading fonts, with fallbacks for characters Mona Sans doesn't have (CJK and emoji)."""

import unicodedata
from functools import cache
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import ImageFont
from PIL.ImageFont import FreeTypeFont

from thumbgen import layout
from thumbgen.text import Run


@cache
def load_font(path: Path, size: int) -> FreeTypeFont:
    # Left to choose, Pillow lays text out with Raqm wherever the FriBiDi library happens to be
    # installed (GitHub's Linux runners, for example), which places letters slightly differently.
    # Basic layout is available everywhere, so thumbnails come out the same on every machine.
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.BASIC)


def font(size: int, bold: bool = False) -> FreeTypeFont:
    """Mona Sans at ``size`` pixels."""
    return load_font(layout.FONT_BOLD if bold else layout.FONT_REGULAR, size)


class FallbackFont:
    """Mona Sans plus the fallback fonts: each character is drawn in the first font that has it.

    It measures text like a Pillow font (``getlength``), so the wrapping helpers in
    text.py work with it. ``runs`` splits text into pieces that each use one font,
    which is how it gets drawn.
    """

    def __init__(self, size: int):
        self.size = size

    def runs(self, text: str) -> list[Run]:
        runs: list[Run] = []
        for char in text:
            path = _font_path_for(char)
            if path is None:
                continue
            font = load_font(path, self.size)
            if runs and runs[-1][1] is font:
                runs[-1] = (runs[-1][0] + char, font)
            else:
                runs.append((char, font))
        return runs

    def getlength(self, text: str) -> float:
        return sum(font.getlength(piece) for piece, font in self.runs(text))


@cache
def _font_path_for(char: str) -> Path | None:
    """The first font that has ``char``.

    If none has it, invisible characters (like the word joiner U+2060) are dropped
    by returning None; anything else goes to Mona Sans, which draws a "missing" box.
    """
    for path in (layout.FONT_REGULAR, *layout.FALLBACK_FONTS):
        if ord(char) in _characters(path):
            return path
    if unicodedata.category(char) in ("Mn", "Cf"):
        return None
    return layout.FONT_REGULAR


@cache
def _characters(path: Path) -> frozenset[int]:
    """The code points ``path`` has glyphs for. Only read when a character needs this font."""
    with TTFont(path, lazy=True) as font:
        return frozenset(font.getBestCmap())
