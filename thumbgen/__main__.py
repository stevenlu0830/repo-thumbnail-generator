"""Command-line entry point: ``python -m thumbgen [repo link]``."""

import os
import sys
from pathlib import Path

from thumbgen.github_api import GitHubError
from thumbgen.service import generate
from thumbgen.url_parser import InvalidLinkError, parse_repo_url

OUTPUT_DIR = Path("output")


def main(argv: list[str] | None = None) -> None:
    """Ask for a repo link (or take it from ``argv``), then fetch, draw and save its thumbnail."""
    args = sys.argv[1:] if argv is None else argv
    link = args[0] if args else input("Enter GitHub repo link: ")
    try:
        owner, repo = parse_repo_url(link)
        print(f"Fetching {owner}/{repo} ...")
        thumbnail = generate(owner, repo, token=os.environ.get("GITHUB_TOKEN"))
    except (InvalidLinkError, GitHubError) as error:
        sys.exit(f"Error: {error}")

    if thumbnail.avatar_missing:
        print("Couldn't download the owner's avatar, so a placeholder is used instead.")
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / thumbnail.filename
    path.write_bytes(thumbnail.png)
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
