"""Smoke tests: the committed assets exist and load with the libraries the app uses."""

import json
import re

import pytest
from PIL import Image, ImageFont

from thumbgen.layout import FONT_BOLD, FONT_REGULAR, ICON_NAMES, ICONS_DIR, LANGUAGE_COLORS


@pytest.mark.parametrize(("path", "style"), [(FONT_REGULAR, "Regular"), (FONT_BOLD, "Bold")])
def test_font_loads(path, style):
    font = ImageFont.truetype(path, 48)
    assert font.getname() == ("Mona Sans", style)
    assert font.getlength("stevenlu0830/grade-calculator") > 0


@pytest.mark.parametrize("name", ICON_NAMES)
def test_icon_is_square_png_with_transparency(name):
    with Image.open(ICONS_DIR / f"{name}.png") as icon:
        assert icon.format == "PNG"
        assert icon.mode == "RGBA"
        assert icon.width == icon.height
        assert icon.getchannel("A").getextrema() == (0, 255)


def test_language_colors_are_hex():
    colors = json.loads(LANGUAGE_COLORS.read_text())
    assert colors["Python"] == "#3572A5"
    assert all(re.fullmatch(r"#[0-9a-fA-F]{6}", color) for color in colors.values())
