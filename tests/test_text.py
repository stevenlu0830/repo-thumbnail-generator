import pytest

from thumbgen.fonts import FallbackFont, font
from thumbgen.text import (
    ELLIPSIS,
    format_count,
    pluralize,
    runs_width,
    wrap_lines,
    wrap_text,
    wrap_title,
)

# The renderer's own fonts, so text is measured exactly as it is drawn.
REGULAR = font(30)


def title_lines(owner, repo, size, max_width=720):
    regular, bold = font(size), font(size, bold=True)
    lines = wrap_title(owner, repo, regular, bold, max_width)
    return [[(text, run_font is bold) for text, run_font in line] for line in lines]


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (0, "0"),
        (999, "999"),
        (1000, "1k"),
        (1234, "1.2k"),
        (12_345, "12.3k"),
        (99_960, "100k"),
        (123_456, "123k"),
        (999_999, "1m"),
        (1_500_000, "1.5m"),
        (1_234_567_890, "1.2b"),
        (2_000_000_000, "2b"),
    ],
)
def test_format_count(count, expected):
    assert format_count(count) == expected


def test_pluralize():
    assert [pluralize(n, "Star") for n in (0, 1, 2)] == ["Stars", "Star", "Stars"]


def test_wrap_text_breaks_between_words():
    text = "Vibe code with pi in a lightweight, real IDE that customises"
    lines = wrap_text(text, REGULAR, 600)
    assert len(lines) == 2
    assert all(REGULAR.getlength(line) <= 600 for line in lines)
    assert " ".join(lines) == text


def test_wrap_text_of_blank_text_has_no_lines():
    assert wrap_text("   \n ", REGULAR, 600) == []


def test_wrap_text_splits_words_too_long_for_a_line():
    lines = wrap_text("x" * 200, REGULAR, 300)
    assert len(lines) > 1
    assert "".join(lines) == "x" * 200
    assert all(REGULAR.getlength(line) <= 300 for line in lines)


def test_cjk_text_breaks_between_characters():
    font = FallbackFont(30)
    text = "这是一个能根据你的工作方式自我定制的轻量级开发环境" * 3
    lines = wrap_text(text, font, 300)
    assert len(lines) > 1
    assert "".join(lines) == text  # no spaces added between CJK characters
    assert all(font.getlength(line) <= 300 for line in lines)
    assert font.getlength(lines[0]) > 300 - font.getlength("这")  # the first line is filled


def test_mixed_cjk_and_latin_keeps_spaces_between_words():
    lines = wrap_text("Lightweight IDE 轻量级开发环境 by JetBrains", FallbackFont(30), 10_000)
    assert lines == ["Lightweight IDE 轻量级开发环境 by JetBrains"]


def test_wrap_lines_cuts_with_an_ellipsis():
    lines = wrap_lines("word " * 100, REGULAR, 300, max_lines=2)
    assert len(lines) == 2
    assert lines[-1].endswith(ELLIPSIS)
    assert REGULAR.getlength(lines[-1]) <= 300


def test_title_wraps_after_a_hyphen():
    assert title_lines("JetBrains", "intellij-community", 60) == [
        [("JetBrains/", False), ("intellij-", True)],
        [("community", True)],
    ]


def test_title_wraps_after_a_hyphen_like_example_2():
    assert title_lines("anthonyl8", "nest-finder", 76) == [
        [("anthonyl8/", False), ("nest-", True)],
        [("finder", True)],
    ]


def test_short_title_stays_on_one_line():
    assert title_lines("octocat", "hi", 76) == [[("octocat/", False), ("hi", True)]]


def test_title_without_break_points_is_split_between_characters():
    regular, bold = font(40), font(40, bold=True)
    lines = wrap_title("someone", "a" * 80, regular, bold, 500)
    assert len(lines) > 1
    assert all(runs_width(line) <= 500 for line in lines)
    assert "".join(text for line in lines for text, _ in line) == "someone/" + "a" * 80
