from pathlib import Path

import pytest

from thumbgen import layout
from thumbgen.fonts import FallbackFont


def font_files(text):
    """Which font file draws each run of ``text``."""
    return [(piece, Path(font.path).name) for piece, font in FallbackFont(30).runs(text)]


def test_latin_text_uses_mona_sans():
    assert font_files("Hello, world!") == [("Hello, world!", layout.FONT_REGULAR.name)]


@pytest.mark.parametrize(
    ("text", "font_file"),
    [
        ("🚀", layout.FONT_EMOJI.name),
        ("中文", layout.FONT_CJK.name),
        ("繁體", layout.FONT_CJK.name),
        ("ひらがなカタカナ", layout.FONT_CJK.name),
        ("한국어", layout.FONT_KOREAN.name),
    ],
)
def test_characters_mona_sans_lacks_use_a_fallback(text, font_file):
    assert font_files(text) == [(text, font_file)]


def test_mixed_text_is_split_into_runs():
    assert font_files("Docs 中文 🚀") == [
        ("Docs ", layout.FONT_REGULAR.name),
        ("中文", layout.FONT_CJK.name),
        (" ", layout.FONT_REGULAR.name),
        ("🚀", layout.FONT_EMOJI.name),
    ]


def test_emoji_variation_selector_adds_no_width():
    # "❤️" is a heart followed by the invisible emoji variation selector U+FE0F.
    font = FallbackFont(30)
    assert font.getlength("❤️") == font.getlength("❤")


def test_invisible_characters_no_font_has_are_dropped():
    # U+2060 WORD JOINER is in none of the fonts; drawing it would show a "missing" box.
    assert "".join(piece for piece, _ in FallbackFont(30).runs("a⁠b")) == "ab"


def test_length_is_the_sum_of_its_runs():
    font = FallbackFont(30)
    text = "Docs 中文 🚀"
    assert font.getlength(text) == sum(run_font.getlength(piece) for piece, run_font in font.runs(text))
