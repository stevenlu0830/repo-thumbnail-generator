"""Command-line entry point: ``python -m thumbgen [repo link]``."""

import os
import sys
from pprint import pprint

from thumbgen.github_api import GitHubError, fetch_repo_info
from thumbgen.url_parser import InvalidLinkError, parse_repo_url


def main() -> None:
    link = sys.argv[1] if len(sys.argv) > 1 else input("Enter GitHub repo link: ")
    try:
        owner, repo = parse_repo_url(link)
        print(f"Fetching {owner}/{repo} ...")
        info = fetch_repo_info(owner, repo, token=os.environ.get("GITHUB_TOKEN"))
    except (InvalidLinkError, GitHubError) as error:
        sys.exit(f"Error: {error}")

    # Phase 3 replaces this with rendering and saving the thumbnail.
    pprint(info, sort_dicts=False)
    print(f"avatar: {len(info.avatar):,} bytes" if info.avatar else "avatar: couldn't download")


if __name__ == "__main__":
    main()
