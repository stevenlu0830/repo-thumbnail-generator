"""Tests for the GitHub client, using a fake session instead of the network."""

import json

import pytest
import requests

from thumbgen.github_api import (
    API_URL,
    GitHubError,
    NetworkError,
    RateLimitError,
    RepoNotFoundError,
    fetch_repo_info,
)

BASE = f"{API_URL}/repos/octocat/hello-world"
AVATAR_URL = "https://avatars.githubusercontent.com/u/583231?v=4"
REPO_JSON = {
    "name": "Hello-World",
    "owner": {"login": "octocat", "avatar_url": AVATAR_URL},
    "description": "My first repository",
    "stargazers_count": 1500,
    "forks_count": 42,
    "open_issues_count": 10,
}


def make_response(status=200, body=None, headers=None):
    response = requests.Response()
    response.status_code = status
    response._content = body if isinstance(body, bytes) else json.dumps(body).encode()
    response.headers.update(headers or {})
    return response


def last_page(url, page):
    """A ``Link`` header like GitHub's, saying the list has ``page`` pages."""
    return {"Link": f'<{url}?per_page=1&page=2>; rel="next", <{url}?per_page=1&page={page}>; rel="last"'}


class FakeSession:
    """Answers ``get`` from a ``{url: response}`` table and records every call."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append((url, headers))
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        return response


def fake_github(overrides=None):
    responses = {
        BASE: make_response(body=REPO_JSON),
        f"{BASE}/languages": make_response(body={"CSS": 300, "Python": 9000, "HTML": 1200}),
        f"{BASE}/contributors": make_response(body=[{}], headers=last_page(f"{BASE}/contributors", 12)),
        f"{BASE}/pulls": make_response(body=[{}], headers=last_page(f"{BASE}/pulls", 3)),
        AVATAR_URL: make_response(body=b"fake image bytes"),
    }
    responses.update(overrides or {})
    return FakeSession(responses)


def test_collects_everything_the_thumbnail_needs():
    info = fetch_repo_info("octocat", "hello-world", session=fake_github())

    assert (info.owner, info.name) == ("octocat", "Hello-World")
    assert info.description == "My first repository"
    assert (info.stars, info.forks, info.contributors) == (1500, 42, 12)
    assert info.open_issues == 7  # GitHub's 10 "open issues" include the 3 open pull requests
    assert list(info.languages) == ["Python", "HTML", "CSS"]
    assert info.avatar == b"fake image bytes"


def test_counts_short_lists_and_empty_repos():
    session = fake_github({
        f"{BASE}/contributors": make_response(204, b""),
        f"{BASE}/pulls": make_response(body=[{}]),
    })
    info = fetch_repo_info("octocat", "hello-world", session=session)

    assert info.contributors == 0
    assert info.open_issues == 9


def test_contributors_of_huge_repos_are_uncounted():
    too_large = {"message": "The history or contributor list is too large to list contributors for this repository via the API."}
    session = fake_github({f"{BASE}/contributors": make_response(403, too_large)})
    assert fetch_repo_info("octocat", "hello-world", session=session).contributors is None


def test_other_contributor_errors_still_fail():
    session = fake_github({f"{BASE}/contributors": make_response(403, {"message": "Forbidden"})})
    with pytest.raises(GitHubError, match="Forbidden"):
        fetch_repo_info("octocat", "hello-world", session=session)


def test_repos_with_pull_requests_turned_off():
    # e.g. torvalds/linux: the repo exists, but its pull request list answers 404.
    session = fake_github({f"{BASE}/pulls": make_response(404, {"message": "Not Found"})})
    assert fetch_repo_info("octocat", "hello-world", session=session).open_issues == 10


def test_repos_with_issues_turned_off_show_no_issues():
    session = fake_github({BASE: make_response(body={**REPO_JSON, "has_issues": False})})
    assert fetch_repo_info("octocat", "hello-world", session=session).open_issues == 0


def test_token_goes_to_the_api_but_not_the_avatar_host():
    session = fake_github()
    fetch_repo_info("octocat", "hello-world", token="test-token", session=session)

    for url, headers in session.calls:
        if url == AVATAR_URL:
            assert headers is None
        else:
            assert headers["Authorization"] == "Bearer test-token"


def test_failed_avatar_download_is_not_fatal():
    session = fake_github({AVATAR_URL: make_response(500, b"")})
    assert fetch_repo_info("octocat", "hello-world", session=session).avatar is None


def test_missing_repo():
    session = fake_github({BASE: make_response(404, {"message": "Not Found"})})
    with pytest.raises(RepoNotFoundError, match="not found"):
        fetch_repo_info("octocat", "hello-world", session=session)


def test_rate_limit():
    headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1700000000"}
    session = fake_github({BASE: make_response(403, {"message": "API rate limit exceeded"}, headers)})
    with pytest.raises(RateLimitError, match="GITHUB_TOKEN"):
        fetch_repo_info("octocat", "hello-world", session=session)


def test_network_failure():
    session = fake_github({BASE: requests.ConnectionError("no route to host")})
    with pytest.raises(NetworkError, match="internet connection"):
        fetch_repo_info("octocat", "hello-world", session=session)
