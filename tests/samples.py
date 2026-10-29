"""Hard-coded repositories used by the snapshot tests and scripts/render_samples.py.

Each one exercises different parts of the layout, and none of them calls GitHub.
"""

from pathlib import Path

from thumbgen.models import RepoInfo

AVATAR = Path(__file__).parent / "fixtures" / "stevenlu0830-avatar.png"
JETBRAINS_AVATAR = Path(__file__).parent / "fixtures" / "jetbrains-avatar.png"

SAMPLES = {
    # Real data for JetBrains/thinkrail, fetched on 2026-10-29: a popular repo with an
    # organisation avatar, a description that wraps and several languages.
    "thinkrail": RepoInfo(
        owner="JetBrains",
        name="thinkrail",
        description="Vibe code with pi in a lightweight, real IDE that customises itself around the way you work — The Vibe You Need",
        stars=5222,
        forks=269,
        open_issues=189,
        contributors=30,
        languages={"TypeScript": 11081699, "HTML": 1612257, "CSS": 120764, "Astro": 56603, "Shell": 19974,
                   "PowerShell": 18875, "JavaScript": 5157},
        avatar=JETBRAINS_AVATAR.read_bytes(),
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
