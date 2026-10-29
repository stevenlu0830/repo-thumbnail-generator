"""Make the page's browser-tab icon and iOS home-screen icon from assets/icons/agenda.png.

The results are committed in public/, so this only needs re-running after
changing agenda.png. Run it from the repo root:

    python -m scripts.build_page_icons
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets" / "icons" / "agenda.png"
FAVICON = ROOT / "public" / "favicon.png"
HOME_SCREEN_ICON = ROOT / "public" / "apple-touch-icon.png"

BACKGROUND = "#ffffff"  # the drawing is black, so it needs a light tile to show on dark tab bars


def on_tile(drawing: Image.Image, size: int, drawing_height: int, radius: int = 0) -> Image.Image:
    """``drawing`` scaled to ``drawing_height`` and centred on a white square of ``size`` pixels."""
    drawing = drawing.crop(drawing.getchannel("A").getbbox())  # drop the see-through margins
    width = round(drawing.width * drawing_height / drawing.height)
    drawing = drawing.resize((width, drawing_height), Image.Resampling.LANCZOS)

    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(tile).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=BACKGROUND)
    tile.alpha_composite(drawing, ((size - drawing.width) // 2, (size - drawing.height) // 2))
    return tile


def main() -> None:
    with Image.open(SOURCE) as source:
        drawing = source.convert("RGBA")

    # Drawn at 4× and scaled down, so the rounded corners come out smooth.
    favicon = on_tile(drawing, 256, 208, radius=56).resize((64, 64), Image.Resampling.LANCZOS)
    favicon.save(FAVICON, optimize=True)

    # iOS rounds the corners itself, and fills see-through parts with black, so this one is a
    # plain opaque square with some room around the drawing. 180×180 is the size iPhones use.
    on_tile(drawing, 180, 128).convert("RGB").save(HOME_SCREEN_ICON, optimize=True)

    for path in (FAVICON, HOME_SCREEN_ICON):
        print(f"Saved {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
