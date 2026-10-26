"""Draw sample thumbnails from hard-coded data into output/, without calling GitHub.

Handy for checking layout changes. Run it from the repo root:

    python -m scripts.render_samples
"""

from pathlib import Path

from thumbgen.models import RepoInfo
from thumbgen.renderer import render

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output"
AVATAR = ROOT / "tests" / "fixtures" / "stevenlu0830-avatar.png"

SAMPLES = {
    # Real data for stevenlu0830/grade-calculator, to compare with example.jpg.
    "grade-calculator": RepoInfo(
        owner="stevenlu0830",
        name="grade-calculator",
        description="UBC Grade Calculator that provides user-friendly interface to keep track of course grades",
        stars=1,
        forks=0,
        open_issues=0,
        contributors=2,
        languages={"TypeScript": 652315, "PLpgSQL": 5666, "CSS": 4419, "HTML": 2165, "JavaScript": 846},
        avatar=AVATAR.read_bytes(),
    ),
    # Everything long or large at once: title shrinking and wrapping, description
    # truncation, number formatting, many languages and a missing avatar.
    "stress-test": RepoInfo(
        owner="an-organisation-with-a-long-name",
        name="an_extremely-long-repository-name.used-for-testing-the-wrapping",
        description=(
            "A deliberately long description that keeps going well past the point where it "
            "should be cut off, so we can check that it wraps neatly and ends with an "
            "ellipsis instead of running into the stats row below it."
        ),
        stars=123_456,
        forks=7_890,
        open_issues=1,
        contributors=1_500,
        languages={"Python": 50_000, "TypeScript": 30_000, "Rust": 10_000, "Go": 5_000, "Shell": 3_000,
                   "Dockerfile": 1_000, "Not A Real Language": 1_000},
        avatar=None,
    ),
    # Emoji and Chinese/Japanese/Korean text, tiny languages and an uncountable number of contributors.
    "international": RepoInfo(
        owner="example-org",
        name="polyglot",
        description="🚀 A fast toolkit ✨ 中文文档 · 日本語のドキュメント · 한국어 문서 ❤️ with docs in every language 🌏",
        stars=45_300,
        forks=2_100,
        open_issues=321,
        contributors=None,
        languages={"Python": 900_000, "C": 50_000, "Cython": 2_000, "Shell": 500, "Makefile": 200,
                   "Dockerfile": 100, "Batchfile": 50},
        avatar=AVATAR.read_bytes(),
    ),
    # A brand-new, empty repository: no description, no code, nothing counted yet.
    "empty": RepoInfo(
        owner="octocat",
        name="new-project",
        description=None,
        stars=0,
        forks=0,
        open_issues=0,
        contributors=0,
        languages={},
        avatar=None,
    ),
}


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    for name, info in SAMPLES.items():
        path = OUTPUT_DIR / f"sample-{name}.png"
        render(info).save(path)
        print(f"Saved {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
