"""Turn a GitHub repository link into an ``(owner, repo)`` pair."""

import re
from urllib.parse import urlsplit

GITHUB_HOSTS = {"github.com", "www.github.com"}
SSH_PREFIX = "git@github.com:"

# GitHub's naming rules: owners use letters, digits and hyphens (max 39 chars);
# repository names may also contain dots and underscores.
OWNER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}")
REPO_RE = re.compile(r"[A-Za-z0-9._-]{1,100}")


class InvalidLinkError(ValueError):
    """The text isn't a link to a GitHub repository."""


def parse_repo_url(link: str) -> tuple[str, str]:
    """Return ``(owner, repo)`` from any common form of repository link.

    Accepts ``https://github.com/o/r``, ``github.com/o/r``, a trailing ``/``,
    ``.git``, deeper paths like ``/tree/main/src``, ``git@github.com:o/r.git``
    and plain ``o/r``.
    """
    text = link.strip()
    if text.startswith(SSH_PREFIX):
        path = text.removeprefix(SSH_PREFIX)
    else:
        if "://" not in text and text.split("/")[0].lower() in GITHUB_HOSTS:
            text = "https://" + text
        if "://" in text:
            url = urlsplit(text)
            if url.hostname not in GITHUB_HOSTS:
                raise InvalidLinkError(f"{link.strip()!r} is not a github.com link.")
            path = url.path
        else:
            path = text

    segments = [segment for segment in path.split("/") if segment]
    if len(segments) >= 2:
        owner, repo = segments[0], segments[1].removesuffix(".git")
        if OWNER_RE.fullmatch(owner) and REPO_RE.fullmatch(repo) and repo not in {".", ".."}:
            return owner, repo
    raise InvalidLinkError(
        f"{link.strip()!r} doesn't look like a repository link. "
        "Expected something like https://github.com/owner/repo."
    )
