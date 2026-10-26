from dataclasses import replace
from io import BytesIO
from pathlib import Path

from PIL import Image

from thumbgen import layout
from thumbgen.models import RepoInfo
from thumbgen.renderer import _fit_title, _segment_widths, render
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


def test_tiny_languages_get_a_minimum_width():
    widths = _segment_widths([1_000_000, 50, 10, 1], total_width=1200, min_width=6)
    assert sum(widths) == 1200
    assert widths[1:] == [6, 6, 6]


def test_segment_widths_are_proportional_when_none_are_tiny():
    assert _segment_widths([3, 1], total_width=1200, min_width=6) == [900, 300]


def test_tiny_language_is_visible_in_the_bar():
    image = render(make_info(languages={"TypeScript": 1_000_000, "CSS": 1}))
    assert hex_color(image.getpixel((layout.WIDTH - 1, layout.HEIGHT - 1))) == "#663399"  # CSS


def test_no_description_renders():
    assert render(make_info(description=None)).size == layout.CANVAS_SIZE


def test_international_description_renders():
    info = make_info(description="🚀 中文文档 · 日本語のドキュメント · 한국어 문서 ❤️")
    assert render(info).size == layout.CANVAS_SIZE


def test_uncounted_contributors_render():
    assert render(make_info(contributors=None)).size == layout.CANVAS_SIZE


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


def test_titles_with_wide_letters_shrink_until_they_fit():
    # 39 characters normally get size 43, but these wide letters would need 4 lines at that size.
    size, lines = _fit_title("WWWWWWWWW-WWWWWWWWW", "WWWWWWWWW-WWWWWWWWW")
    assert size < 43
    assert len(lines) <= layout.TITLE_MAX_LINES


def test_description_is_left_out_when_there_is_no_room(monkeypatch):
    monkeypatch.setattr(layout, "STATS_TOP", 200)  # pretend the stats row starts right below the title
    assert render(make_info()) == render(make_info(description=None))


def test_short_titles_use_the_largest_size():
    size, lines = _fit_title("octocat", "hi")
    assert size == layout.TITLE_MAX_SIZE
    assert len(lines) == 1
