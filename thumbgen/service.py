"""Make a repo's thumbnail as PNG bytes; shared by the command line and the web app."""

from dataclasses import dataclass, field
from io import BytesIO

from thumbgen.github_api import fetch_repo_info
from thumbgen.renderer import render


@dataclass
class Thumbnail:
    """A finished thumbnail, ready to save to a file or send to a browser."""

    filename: str  # "{owner}_{repo}.png", spelled the way GitHub spells them
    png: bytes = field(repr=False)
    avatar_missing: bool  # the avatar download failed, so a placeholder was drawn


def generate(owner: str, repo: str, token: str | None = None) -> Thumbnail:
    """Fetch ``owner/repo`` from GitHub and draw its thumbnail.

    Raises ``GitHubError`` when GitHub can't be reached or the repo can't be
    read, so each caller can show the message its own way.
    """
    info = fetch_repo_info(owner, repo, token=token)
    buffer = BytesIO()
    render(info).save(buffer, format="PNG")
    return Thumbnail(
        filename=f"{info.owner}_{info.name}.png",
        png=buffer.getvalue(),
        avatar_missing=info.avatar is None,
    )
