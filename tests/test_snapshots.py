"""Snapshot tests: draw each sample and compare it with a saved reference image.

They catch any visible change to the thumbnail. When a change is intended,
regenerate the references, look at them, and commit them with the change:

    UPDATE_SNAPSHOTS=1 pytest tests/test_snapshots.py
"""

import os
from pathlib import Path

import pytest
from PIL import Image, ImageChops

from tests.samples import SAMPLES
from thumbgen.renderer import render

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"
FAILURES_DIR = ROOT / "output" / "snapshot-failures"
UPDATE_COMMAND = "UPDATE_SNAPSHOTS=1 pytest tests/test_snapshots.py"

# Tiny differences (for example anti-aliasing from another Pillow version) are
# allowed; anything that moves, resizes or recolours an element is not.
PIXEL_TOLERANCE = 32  # how much a colour channel (0–255) may differ before a pixel counts as changed
MAX_CHANGED_PIXELS = 0.001  # fraction of the image that may change


@pytest.mark.parametrize("name", SAMPLES)
def test_matches_snapshot(name):
    actual = render(SAMPLES[name])
    reference_path = SNAPSHOTS_DIR / f"{name}.png"
    for old_failure in FAILURES_DIR.glob(f"{name}-*.png"):
        old_failure.unlink()

    if os.environ.get("UPDATE_SNAPSHOTS"):
        SNAPSHOTS_DIR.mkdir(exist_ok=True)
        actual.save(reference_path)
        pytest.skip(f"updated {reference_path.relative_to(ROOT)}")

    assert reference_path.exists(), f"No reference image for {name!r} yet; create it with: {UPDATE_COMMAND}"
    with Image.open(reference_path) as reference:
        expected = reference.convert("RGB")
    assert actual.size == expected.size

    changed = _changed_pixels(actual, expected)
    changed_fraction = changed.histogram()[255] / (actual.width * actual.height)
    if changed_fraction > MAX_CHANGED_PIXELS:
        FAILURES_DIR.mkdir(parents=True, exist_ok=True)
        actual_path = FAILURES_DIR / f"{name}-actual.png"
        diff_path = FAILURES_DIR / f"{name}-diff.png"
        actual.save(actual_path)
        _highlight(expected, changed).save(diff_path)
        pytest.fail(
            f"{changed_fraction:.2%} of the pixels changed. Compare {actual_path.relative_to(ROOT)} "
            f"with {reference_path.relative_to(ROOT)}; changed pixels are red in {diff_path.relative_to(ROOT)}. "
            f"If the change is intended, run: {UPDATE_COMMAND}"
        )


def _changed_pixels(actual: Image.Image, expected: Image.Image) -> Image.Image:
    """A black-and-white mask: white where any colour channel differs by more than PIXEL_TOLERANCE."""
    red, green, blue = ImageChops.difference(actual, expected).split()
    largest = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    return largest.point(lambda value: 255 if value > PIXEL_TOLERANCE else 0)


def _highlight(expected: Image.Image, changed: Image.Image) -> Image.Image:
    """The reference image, faded, with the changed pixels painted red."""
    faded = Image.blend(expected, Image.new("RGB", expected.size, "white"), 0.7)
    faded.paste((255, 0, 0), mask=changed)
    return faded
