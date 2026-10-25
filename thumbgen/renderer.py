"""Draw the thumbnail image from a ``RepoInfo`` with Pillow."""

import json
from functools import cache
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

from thumbgen import layout
from thumbgen.models import RepoInfo
from thumbgen.text import Run, ellipsize, format_count, pluralize, runs_width, wrap_lines, wrap_title

# Shapes with curved edges are drawn this many times larger, then shrunk, so the edges look smooth.
SUPERSAMPLE = 4


def render(info: RepoInfo) -> Image.Image:
    """Draw the 1200×600 thumbnail for ``info``."""
    image = Image.new("RGB", layout.CANVAS_SIZE, layout.BACKGROUND)
    draw = ImageDraw.Draw(image)

    title_bottom = _draw_title(draw, info.owner, info.name)
    if info.description:
        _draw_description(draw, info.description, title_bottom)
    _draw_avatar(image, info.avatar)
    _draw_stats(image, draw, info)
    _draw_github_mark(image)
    _draw_language_bar(draw, info.languages)
    return image


def _draw_title(draw: ImageDraw.ImageDraw, owner: str, repo: str) -> int:
    """Draw "owner/repo" and return the y coordinate just below its last line."""
    size, lines = _fit_title(owner, repo)
    ascent, descent = _font(size).getmetrics()
    line_height = round(size * layout.TITLE_LINE_HEIGHT)
    baseline = layout.TITLE_TOP + ascent
    for index, line in enumerate(lines):
        if index:
            baseline += line_height
        x = layout.MARGIN_X
        for text, font in line:
            draw.text((x, baseline), text, font=font, fill=layout.TEXT_COLOR, anchor="ls")
            x += font.getlength(text)
    return baseline + descent


def _fit_title(owner: str, repo: str) -> tuple[int, list[list[Run]]]:
    """Choose the title's font size and wrap it into at most TITLE_MAX_LINES lines."""
    characters = len(owner) + 1 + len(repo)
    size = min(layout.TITLE_MAX_SIZE, max(layout.TITLE_MIN_SIZE, layout.TITLE_SIZE_FACTOR // characters))
    while True:
        lines = wrap_title(owner, repo, _font(size), _font(size, bold=True), layout.TEXT_MAX_WIDTH)
        if len(lines) <= layout.TITLE_MAX_LINES or size == layout.TITLE_MIN_SIZE:
            break
        size = max(size - 2, layout.TITLE_MIN_SIZE)

    if len(lines) > layout.TITLE_MAX_LINES:  # still too long at the smallest size
        lines = lines[: layout.TITLE_MAX_LINES]
        *rest, (text, font) = lines[-1]
        lines[-1] = [*rest, (ellipsize(text, font, layout.TEXT_MAX_WIDTH - runs_width(rest)), font)]
    return size, lines


def _draw_description(draw: ImageDraw.ImageDraw, description: str, top: int) -> None:
    font = _font(layout.DESCRIPTION_SIZE)
    ascent, descent = font.getmetrics()
    first_baseline = top + layout.DESCRIPTION_GAP + ascent
    # Use as many lines as fit above the stats row, up to DESCRIPTION_MAX_LINES.
    room = layout.STATS_TOP - layout.DESCRIPTION_GAP - descent - first_baseline
    max_lines = min(layout.DESCRIPTION_MAX_LINES, room // layout.DESCRIPTION_LINE_HEIGHT + 1)
    if max_lines < 1:
        return
    lines = wrap_lines(description, font, layout.TEXT_MAX_WIDTH, max_lines)
    for index, line in enumerate(lines):
        baseline = first_baseline + index * layout.DESCRIPTION_LINE_HEIGHT
        draw.text((layout.MARGIN_X, baseline), line, font=font, fill=layout.MUTED_COLOR, anchor="ls")


def _draw_avatar(image: Image.Image, avatar: bytes | None) -> None:
    size = layout.AVATAR_SIZE
    left, top = layout.AVATAR_LEFT, layout.AVATAR_TOP
    mask = _rounded_mask(size, layout.AVATAR_RADIUS)
    picture = _load_avatar(avatar, size)
    if picture is None:
        image.paste(layout.PLACEHOLDER_COLOR, (left, top, left + size, top + size), mask)
    else:
        image.paste(picture, (left, top), mask)


def _load_avatar(data: bytes | None, size: int) -> Image.Image | None:
    """Decode the avatar, crop it square and flatten any transparency onto white."""
    if data is None:
        return None
    try:
        picture = Image.open(BytesIO(data))
        picture.load()
    except (UnidentifiedImageError, OSError):
        return None
    picture = ImageOps.fit(picture.convert("RGBA"), (size, size), Image.Resampling.LANCZOS)
    flattened = Image.new("RGBA", picture.size, layout.BACKGROUND)
    flattened.alpha_composite(picture)
    return flattened.convert("RGB")


def _rounded_mask(size: int, radius: int) -> Image.Image:
    big = size * SUPERSAMPLE
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, big - 1, big - 1), radius * SUPERSAMPLE, fill=255)
    return mask.resize((size, size), Image.Resampling.LANCZOS)


def _draw_stats(image: Image.Image, draw: ImageDraw.ImageDraw, info: RepoInfo) -> None:
    """Draw the icon / number / label columns, each as wide as its text."""
    number_font = _font(layout.STAT_NUMBER_SIZE)
    label_font = _font(layout.STAT_LABEL_SIZE)
    stats = [
        ("people", info.contributors, "Contributor"),
        ("issue-opened", info.open_issues, "Issue"),
        ("star", info.stars, "Star"),
        ("repo-forked", info.forks, "Fork"),
    ]
    x = layout.MARGIN_X
    for icon, count, word in stats:
        _draw_icon(image, icon, x, layout.STATS_TOP, layout.STAT_ICON_SIZE, layout.MUTED_COLOR)
        number, label = format_count(count), pluralize(count, word)
        text_x = x + layout.STAT_TEXT_OFFSET
        draw.text((text_x, layout.STAT_NUMBER_BASELINE), number, font=number_font, fill=layout.TEXT_COLOR, anchor="ls")
        draw.text((text_x, layout.STAT_LABEL_BASELINE), label, font=label_font, fill=layout.MUTED_COLOR, anchor="ls")
        text_width = max(number_font.getlength(number), label_font.getlength(label))
        x = round(text_x + text_width + layout.STAT_COLUMN_GAP)


def _draw_github_mark(image: Image.Image) -> None:
    size = layout.GITHUB_MARK_SIZE
    left = layout.WIDTH - layout.MARGIN_X - size
    top = layout.GITHUB_MARK_CENTER_Y - size // 2
    _draw_icon(image, "mark-github", left, top, size, layout.SUBTLE_COLOR)


def _draw_icon(image: Image.Image, name: str, left: int, top: int, size: int, color: str) -> None:
    image.paste(color, (left, top, left + size, top + size), _icon_mask(name, size))


def _draw_language_bar(draw: ImageDraw.ImageDraw, languages: dict[str, int]) -> None:
    """One coloured segment per language, as wide as its share of the code, largest first."""
    total = sum(languages.values())
    if not total:
        return
    colors = _language_colors()
    top = layout.HEIGHT - layout.LANGUAGE_BAR_HEIGHT
    left, done = 0, 0
    for language, size in languages.items():
        done += size
        right = round(done / total * layout.WIDTH)
        if right > left:  # languages narrower than a pixel are skipped
            color = colors.get(language, layout.UNKNOWN_LANGUAGE_COLOR)
            draw.rectangle((left, top, right - 1, layout.HEIGHT - 1), fill=color)
        left = right


@cache
def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(layout.FONT_BOLD if bold else layout.FONT_REGULAR, size)


@cache
def _icon_mask(name: str, size: int) -> Image.Image:
    """The icon's shape as a greyscale mask, so it can be pasted in any colour."""
    with Image.open(layout.ICONS_DIR / f"{name}.png") as icon:
        return icon.getchannel("A").resize((size, size), Image.Resampling.LANCZOS)


@cache
def _language_colors() -> dict[str, str]:
    return json.loads(layout.LANGUAGE_COLORS.read_text())
