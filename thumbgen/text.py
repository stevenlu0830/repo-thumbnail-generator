"""Text helpers: line wrapping, truncation and number formatting."""

import re

from PIL.ImageFont import FreeTypeFont

ELLIPSIS = "…"

# A piece of text and the font it's drawn in.
Run = tuple[str, FreeTypeFont]

# Splits a title into pieces that each end just after a - _ / or . where possible.
TITLE_PIECES = re.compile(r"[^-_/.]*[-_/.]|[^-_/.]+")


def format_count(n: int) -> str:
    """Shorten big numbers like GitHub does: 1234 → "1.2k", 56789 → "56.8k", 2500000 → "2.5m"."""
    if n < 1000:
        return str(n)
    for scale, suffix in ((1e3, "k"), (1e6, "m"), (1e9, "b")):
        value = n / scale
        text = (f"{value:.1f}" if value < 100 else f"{value:.0f}").removesuffix(".0")
        if float(text) < 1000:  # otherwise 999,999 would show as "1000k" instead of "1m"
            break
    return text + suffix


def pluralize(count: int, word: str) -> str:
    """Return ``word`` for a count of 1 ("Star"), and ``word`` plus "s" otherwise ("Stars")."""
    return word if count == 1 else word + "s"


def wrap_text(text: str, font: FreeTypeFont, max_width: float) -> list[str]:
    """Split text into lines no wider than ``max_width``, breaking between words.

    A word too long to fit on a line by itself is broken between characters.
    """
    lines: list[str] = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}" if line else word
        if font.getlength(candidate) <= max_width:
            line = candidate
            continue
        if line:
            lines.append(line)
        while font.getlength(word) > max_width:
            cut = _fitting_prefix_length(word, font, max_width)
            lines.append(word[:cut])
            word = word[cut:]
        line = word
    if line:
        lines.append(line)
    return lines


def wrap_lines(text: str, font: FreeTypeFont, max_width: float, max_lines: int) -> list[str]:
    """Like ``wrap_text``, but keeps at most ``max_lines`` and ends with "…" if text was cut."""
    lines = wrap_text(text, font, max_width)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = ellipsize(lines[-1], font, max_width)
    return lines


def ellipsize(text: str, font: FreeTypeFont, max_width: float) -> str:
    """Remove characters from the end of ``text`` until it fits ``max_width`` with "…" added."""
    while text and font.getlength(text + ELLIPSIS) > max_width:
        text = text[:-1]
    return text.rstrip() + ELLIPSIS


def wrap_title(
    owner: str, repo: str, regular: FreeTypeFont, bold: FreeTypeFont, max_width: float
) -> list[list[Run]]:
    """Wrap "owner/repo" (owner in regular, repo in bold) into lines of runs.

    Lines break after a - _ / or . where possible, and between characters only
    when a piece is too long to fit on a line by itself.
    """
    pieces = [(piece, regular) for piece in TITLE_PIECES.findall(owner + "/")]
    pieces += [(piece, bold) for piece in TITLE_PIECES.findall(repo)]

    lines: list[list[Run]] = [[]]
    width = 0.0
    for text, font in pieces:
        if lines[-1] and width + font.getlength(text) > max_width:
            lines.append([])
            width = 0.0
        while font.getlength(text) > max_width:  # the current line is empty here
            cut = _fitting_prefix_length(text, font, max_width)
            lines[-1].append((text[:cut], font))
            lines.append([])
            text = text[cut:]
        lines[-1].append((text, font))
        width += font.getlength(text)
    return [_merge_runs(line) for line in lines]


def runs_width(runs: list[Run]) -> float:
    return sum(font.getlength(text) for text, font in runs)


def _merge_runs(runs: list[Run]) -> list[Run]:
    """Join neighbouring runs that use the same font, so they're drawn (and kerned) together."""
    merged: list[Run] = []
    for text, font in runs:
        if merged and merged[-1][1] is font:
            merged[-1] = (merged[-1][0] + text, font)
        else:
            merged.append((text, font))
    return merged


def _fitting_prefix_length(text: str, font: FreeTypeFont, max_width: float) -> int:
    """How many leading characters of ``text`` fit in ``max_width`` (at least 1)."""
    length = len(text)
    while length > 1 and font.getlength(text[:length]) > max_width:
        length -= 1
    return length
