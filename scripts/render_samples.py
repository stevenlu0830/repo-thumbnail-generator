"""Draw the sample thumbnails from tests/samples.py into output/, without calling GitHub.

Handy for checking layout changes. Run it from the repo root:

    python -m scripts.render_samples
"""

from pathlib import Path

from tests.samples import SAMPLES
from thumbgen.renderer import render

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    for name, info in SAMPLES.items():
        path = OUTPUT_DIR / f"sample-{name}.png"
        render(info).save(path)
        print(f"Saved {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
