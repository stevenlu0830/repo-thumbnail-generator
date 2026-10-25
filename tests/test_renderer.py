from dataclasses import replace
from io import BytesIO
from pathlib import Path

from PIL import Image

from thumbgen import layout
from thumbgen.models import RepoInfo
from thumbgen.renderer import _fit_title, render
from thumbgen.text import runs_width

AVATAR = Path(__file__).parent / "fixtures" / "stevenlu0830-avatar.png"
AVATAR_CENTER = (layout.AVATAR_LEFT + layout.AVATAR_SIZE // 2, layout.AVATAR_TOP + layout.AVATAR_SIZE // 2)


SAMPLE = RepoInfo(
    owner="stevenlu0830",
    name="grade-calculator",
    description="UBC Grade Calculator that provides user-friendly interface to keep track of course grades",
    stars=1,
    forks=0,
    open_issues=0,
    contributors=2,
    languages={"TypeScript": 652315, "CSS": 4419},
    avatar=AVATAR.read_bytes(),
)


def make_info(**changes):
    return replace(SAMPLE, **changes)


def png_bytes(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def hex_color(pixel):
    return "#{:02x}{:02x}{:02x}".format(*pixel)


def test_renders_a_1200x600_image():
    image = render(make_info())
    assert image.size == layout.CANVAS_SIZE
    assert image.mode == "RGB"


def test_language_bar_uses_linguist_colours():
    image = render(make_info())
    assert hex_color(image.getpixel((10, layout.HEIGHT - 1))) == "#3178c6"  # TypeScript
    assert hex_color(image.getpixel((layout.WIDTH - 1, layout.HEIGHT - 1))) == "#663399"  # CSS


def test_no_languages_means_no_bar():
    image = render(make_info(languages={}))
    assert image.getpixel((10, layout.HEIGHT - 1)) == (255, 255, 255)


def test_missing_avatar_draws_a_placeholder():
    image = render(make_info(avatar=None))
    assert hex_color(image.getpixel(AVATAR_CENTER)) == layout.PLACEHOLDER_COLOR


def test_broken_avatar_draws_a_placeholder():
    image = render(make_info(avatar=b"not an image"))
    assert hex_color(image.getpixel(AVATAR_CENTER)) == layout.PLACEHOLDER_COLOR


def test_transparent_avatar_is_shown_on_white():
    transparent = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    image = render(make_info(avatar=png_bytes(transparent)))
    assert image.getpixel(AVATAR_CENTER) == (255, 255, 255)


def test_long_titles_shrink_and_stay_within_the_text_area():
    size, lines = _fit_title("an-organisation-with-a-long-name", "an-extremely-long-repository-name" * 3)
    assert size == layout.TITLE_MIN_SIZE
    assert len(lines) <= layout.TITLE_MAX_LINES
    assert all(runs_width(line) <= layout.TEXT_MAX_WIDTH for line in lines)


def test_short_titles_use_the_largest_size():
    size, lines = _fit_title("octocat", "hi")
    assert size == layout.TITLE_MAX_SIZE
    assert len(lines) == 1
