"""Web app: a page for entering a repo link, and an API that returns the repo's thumbnail.

Run it locally with ``flask run``. On Vercel, this file's ``app`` is the entrypoint.
"""

import os
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_from_directory, url_for
from werkzeug.wrappers import Response

from thumbgen.github_api import GitHubError, NetworkError, RateLimitError, RepoNotFoundError
from thumbgen.service import generate
from thumbgen.url_parser import InvalidLinkError, parse_repo_url

PUBLIC_DIR = Path(__file__).resolve().parent / "public"
# The CDN keeps each thumbnail for an hour, then for up to a day more it sends the
# old one while fetching a fresh one in the background.
THUMBNAIL_CACHE = "public, s-maxage=3600, stale-while-revalidate=86400"

# Vercel serves public/ itself, so Flask's own static folder isn't used.
app = Flask(__name__, static_folder=None)


@app.get("/")
def index() -> Response:
    """The page. Vercel also serves it straight from public/; this is for ``flask run``."""
    return send_from_directory(PUBLIC_DIR, "index.html")


@app.get("/api/thumbnail")
def thumbnail_for_link() -> Response:
    """Take any form of repo link and redirect to that repo's one thumbnail address."""
    link = request.args.get("repo", "")
    if not link.strip():
        return _error(400, "Enter a GitHub repository link, like github.com/owner/repo.")
    try:
        owner, repo = _lowercase_repo(link)
    except InvalidLinkError as error:
        return _error(400, str(error))
    return redirect(url_for("thumbnail", owner=owner, repo=repo), code=308)


@app.get("/api/thumbnail/<owner>/<repo>.png")
def thumbnail(owner: str, repo: str) -> Response:
    """The thumbnail of ``owner/repo`` as a PNG."""
    try:
        canonical = _lowercase_repo(f"{owner}/{repo}")
    except InvalidLinkError as error:
        return _error(400, str(error))
    if (owner, repo) != canonical:
        return redirect(url_for("thumbnail", owner=canonical[0], repo=canonical[1]), code=308)

    try:
        result = generate(owner, repo, token=os.environ.get("GITHUB_TOKEN"))
    except RepoNotFoundError:
        return _error(404, f"Couldn't find a public repository at github.com/{owner}/{repo}. Check the link.")
    except RateLimitError as error:
        app.logger.warning("GitHub rate limit reached: %s", error)
        return _error(429, "Too many thumbnails have been made recently. Please try again in a few minutes.")
    except NetworkError as error:
        app.logger.warning("Couldn't reach GitHub: %s", error)
        return _error(502, "Couldn't reach GitHub. Please try again in a moment.")
    except GitHubError as error:
        # Usually an expired or wrong GITHUB_TOKEN: the site's problem, not the visitor's.
        app.logger.error("GitHub error for %s/%s: %s", owner, repo, error)
        return _error(500, "Something went wrong on our side. Please try again later.")

    response = Response(result.png, mimetype="image/png")
    response.headers["Content-Disposition"] = f'inline; filename="{result.filename}"'
    # A failed avatar download is usually a passing hiccup, so don't keep that image.
    response.headers["Cache-Control"] = "no-store" if result.avatar_missing else THUMBNAIL_CACHE
    return response


def _lowercase_repo(link: str) -> tuple[str, str]:
    """``(owner, repo)`` in lowercase, so each repo has one address (GitHub ignores case)."""
    owner, repo = parse_repo_url(link)
    return owner.lower(), repo.lower()


def _error(status: int, message: str) -> Response:
    """A JSON error for the page to show. Errors are never cached."""
    response = jsonify(error=message)
    response.status_code = status
    response.headers["Cache-Control"] = "no-store"
    return response
