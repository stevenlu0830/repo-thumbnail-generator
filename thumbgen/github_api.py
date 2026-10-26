"""Fetch repository data from the GitHub REST API and return a ``RepoInfo``."""

from datetime import datetime
from urllib.parse import parse_qs, urlsplit

import requests

from thumbgen.models import RepoInfo

API_URL = "https://api.github.com"
AVATAR_SIZE = 400  # px; the thumbnail draws it at about half that
TIMEOUT = 15  # seconds per request


class GitHubError(Exception):
    """Talking to GitHub failed; the message is written for the person running the app."""


class RepoNotFoundError(GitHubError):
    pass


class RateLimitError(GitHubError):
    pass


class NetworkError(GitHubError):
    pass


def fetch_repo_info(
    owner: str,
    repo: str,
    token: str | None = None,
    session: requests.Session | None = None,
) -> RepoInfo:
    """Collect everything the thumbnail shows about ``owner/repo``.

    Makes four API requests plus one avatar download. A ``token`` (GitHub
    personal access token) raises the rate limit from 60 to 5,000 requests an
    hour and gives access to private repositories it can read.
    """
    session = session or requests.Session()
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    base = f"{API_URL}/repos/{owner}/{repo}"

    data = _get(session, base, headers).json()
    languages = _get(session, f"{base}/languages", headers).json()
    contributors = _count_contributors(session, f"{base}/contributors", headers)
    open_pulls = _count_open_pulls(session, f"{base}/pulls", headers)

    return RepoInfo(
        owner=data["owner"]["login"],
        name=data["name"],
        description=data["description"],
        stars=data["stargazers_count"],
        forks=data["forks_count"],
        # GitHub counts open pull requests as issues too. With issues turned off,
        # the count is only pull requests, so there are no issues to show.
        open_issues=max(data["open_issues_count"] - open_pulls, 0) if data.get("has_issues", True) else 0,
        contributors=contributors,
        languages=dict(sorted(languages.items(), key=lambda item: item[1], reverse=True)),
        avatar=_download_avatar(session, data["owner"]["avatar_url"]),
    )


def _get(session: requests.Session, url: str, headers: dict, **params) -> requests.Response:
    try:
        response = session.get(url, params=params, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as error:
        raise NetworkError(
            f"Couldn't reach GitHub ({type(error).__name__}). Check your internet connection."
        ) from error
    _raise_for_status(response)
    return response


def _count(session: requests.Session, url: str, headers: dict, **params) -> int:
    """Count a list's items by asking for one item per page and reading the last page number."""
    response = _get(session, url, headers, per_page=1, **params)
    if response.status_code == 204:  # e.g. contributors of an empty repository
        return 0
    last = response.links.get("last")
    if last:
        return int(parse_qs(urlsplit(last["url"]).query)["page"][0])
    return len(response.json())


def _count_contributors(session: requests.Session, url: str, headers: dict) -> int | None:
    """Like ``_count``, but None for repos GitHub says are too large to list contributors for."""
    try:
        return _count(session, url, headers, anon=1)
    except GitHubError as error:
        if "too large" in str(error):
            return None
        raise


def _count_open_pulls(session: requests.Session, url: str, headers: dict) -> int:
    """Like ``_count``, but 0 for repos with pull requests turned off (GitHub answers 404)."""
    try:
        return _count(session, url, headers, state="open")
    except RepoNotFoundError:
        return 0


def _download_avatar(session: requests.Session, url: str) -> bytes | None:
    # Sent without the API headers: the token is only meant for api.github.com.
    try:
        response = session.get(url, params={"s": AVATAR_SIZE}, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        return None
    return response.content


def _raise_for_status(response: requests.Response) -> None:
    if response.ok:
        return
    status = response.status_code
    if status == 404:
        raise RepoNotFoundError(
            "Repository not found. Check the link; a private repository also needs "
            "a GITHUB_TOKEN that can read it."
        )
    if status in (403, 429) and (
        response.headers.get("X-RateLimit-Remaining") == "0" or "Retry-After" in response.headers
    ):
        raise RateLimitError(
            f"GitHub's rate limit was reached; {_retry_hint(response)}. "
            "Setting GITHUB_TOKEN raises the limit to 5,000 requests an hour."
        )
    if status == 401:
        raise GitHubError("GitHub rejected the GITHUB_TOKEN. Check it hasn't expired, or unset it.")
    raise GitHubError(f"GitHub API error {status}: {_api_message(response)}")


def _retry_hint(response: requests.Response) -> str:
    if "Retry-After" in response.headers:
        return f"try again in {response.headers['Retry-After']} seconds"
    if "X-RateLimit-Reset" in response.headers:
        reset = datetime.fromtimestamp(int(response.headers["X-RateLimit-Reset"]))
        return f"it resets at {reset:%H:%M}"
    return "try again later"


def _api_message(response: requests.Response) -> str:
    try:
        return response.json()["message"]
    except (ValueError, KeyError, TypeError):
        return response.reason or "unknown error"
