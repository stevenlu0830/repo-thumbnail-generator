"""Tests for the web app, through Flask's test client with GitHub replaced by a fake."""

from dataclasses import replace
from io import BytesIO
from pathlib import Path

import pytest
import requests
from PIL import Image

import app as web
from tests.test_github_api import FakeSession, make_response
from thumbgen import github_api, service
from thumbgen.github_api import GitHubError, NetworkError, RateLimitError, RepoNotFoundError
from thumbgen.models import RepoInfo

INFO = RepoInfo(
    owner="JetBrains",
    name="thinkrail",
    description="Vibe code with pi in a lightweight, real IDE",
    stars=5222,
    forks=269,
    open_issues=189,
    contributors=30,
    languages={"TypeScript": 100},
    avatar=(Path(__file__).parent / "fixtures" / "jetbrains-avatar.png").read_bytes(),
)
PNG_URL = "/api/thumbnail/jetbrains/thinkrail.png"


@pytest.fixture
def client():
    return web.app.test_client()


@pytest.fixture
def fake_github(monkeypatch):
    """Record what ``fetch_repo_info`` was asked for, and return ``INFO`` instead of calling GitHub."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    calls = []

    def fetch(owner, repo, token=None):
        calls.append((owner, repo, token))
        return INFO

    monkeypatch.setattr(service, "fetch_repo_info", fetch)
    return calls


def failing_with(error):
    """A fake ``fetch_repo_info`` that raises ``error``."""

    def fetch(owner, repo, token=None):
        raise error

    return fetch


def test_serves_the_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b'href="/style.css"' in response.data
    assert b'src="/script.js"' in response.data


@pytest.mark.parametrize("path, mimetype", [("/style.css", "text/css"), ("/script.js", "javascript")])
def test_serves_the_pages_css_and_javascript(client, path, mimetype):
    response = client.get(path)

    assert response.status_code == 200
    assert mimetype in response.mimetype  # .js is text/ or application/javascript, depending on the system


def test_page_asks_the_api_these_tests_cover(client):
    assert b"/api/thumbnail?repo=" in client.get("/script.js").data


def test_does_not_serve_files_outside_public(client):
    assert client.get("/app.py").status_code == 404


@pytest.mark.parametrize(
    "link",
    [
        "https://github.com/JetBrains/ThinkRail",
        "github.com/jetbrains/thinkrail/tree/main/src",
        "git@github.com:JetBrains/thinkrail.git",
        "  JetBrains/thinkrail  ",
    ],
)
def test_any_link_redirects_to_the_repos_lowercase_address(client, fake_github, link):
    response = client.get("/api/thumbnail", query_string={"repo": link})

    assert response.status_code == 308
    assert response.headers["Location"] == PNG_URL
    assert fake_github == []  # checking a link doesn't use up GitHub requests


def test_following_the_redirect_gives_the_png(client, fake_github):
    response = client.get(
        "/api/thumbnail", query_string={"repo": "github.com/JetBrains/thinkrail"}, follow_redirects=True
    )

    assert response.status_code == 200
    assert response.mimetype == "image/png"


@pytest.mark.parametrize("query", [{}, {"repo": "  "}, {"repo": "not a link"}, {"repo": "https://gitlab.com/o/r"}])
def test_bad_links_are_a_400(client, fake_github, query):
    response = client.get("/api/thumbnail", query_string=query)

    assert response.status_code == 400
    assert response.json["error"]
    assert response.headers["Cache-Control"] == "no-store"
    assert fake_github == []


def test_returns_the_png_with_its_file_name_and_cache_time(client, fake_github):
    response = client.get(PNG_URL)

    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert response.headers["Content-Disposition"] == 'inline; filename="JetBrains_thinkrail.png"'
    assert response.headers["Cache-Control"] == "public, s-maxage=3600, stale-while-revalidate=86400"
    with Image.open(BytesIO(response.data)) as image:
        assert image.size == (1200, 600)
    assert fake_github == [("jetbrains", "thinkrail", None)]


def test_passes_github_token_from_the_environment(client, fake_github, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    client.get(PNG_URL)

    assert fake_github[0][2] == "test-token"


def test_mixed_case_address_redirects_to_lowercase(client, fake_github):
    response = client.get("/api/thumbnail/JetBrains/ThinkRail.png")

    assert response.status_code == 308
    assert response.headers["Location"] == PNG_URL
    assert fake_github == []


@pytest.mark.parametrize("url", ["/api/thumbnail/-owner/repo.png", "/api/thumbnail/owner/...png"])
def test_invalid_address_is_a_400(client, fake_github, url):
    response = client.get(url)

    assert response.status_code == 400
    assert response.json["error"]
    assert response.headers["Cache-Control"] == "no-store"
    assert fake_github == []


def test_does_not_keep_a_thumbnail_with_a_placeholder_avatar(client, monkeypatch):
    monkeypatch.setattr(service, "fetch_repo_info", lambda owner, repo, token=None: replace(INFO, avatar=None))
    response = client.get(PNG_URL)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize(
    "error, status",
    [
        (RepoNotFoundError("Repository not found. A private repository also needs a GITHUB_TOKEN."), 404),
        (RateLimitError("GitHub's rate limit was reached. Setting GITHUB_TOKEN raises the limit."), 429),
        (NetworkError("Couldn't reach GitHub (ConnectionError). Check your internet connection."), 502),
        (GitHubError("GitHub rejected the GITHUB_TOKEN. Check it hasn't expired, or unset it."), 500),
    ],
)
def test_github_errors_become_messages_for_visitors(client, monkeypatch, error, status):
    monkeypatch.setattr(service, "fetch_repo_info", failing_with(error))
    response = client.get(PNG_URL)

    assert response.status_code == status
    assert response.mimetype == "application/json"
    assert response.json["error"]
    assert "GITHUB_TOKEN" not in response.json["error"]
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize(
    "github_answer, status",
    [
        (make_response(404, {"message": "Not Found"}), 404),
        (make_response(403, {"message": "rate limit"}, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "0"}), 429),
        (requests.ConnectionError("no network"), 502),
        (make_response(401, {"message": "Bad credentials"}), 500),
    ],
)
def test_real_github_errors_get_the_right_status(client, monkeypatch, github_answer, status):
    """Run the real GitHub client with only the network faked, so its own error messages are checked too."""
    session = FakeSession({f"{github_api.API_URL}/repos/jetbrains/thinkrail": github_answer})
    monkeypatch.setattr(github_api.requests, "Session", lambda: session)
    response = client.get(PNG_URL)

    assert response.status_code == status
    assert "GITHUB_TOKEN" not in response.json["error"]
    assert response.headers["Cache-Control"] == "no-store"


def test_token_problems_are_logged_for_the_site_owner(client, monkeypatch, caplog):
    monkeypatch.setattr(service, "fetch_repo_info", failing_with(GitHubError("GitHub rejected the GITHUB_TOKEN.")))
    client.get(PNG_URL)

    assert "GitHub rejected the GITHUB_TOKEN." in caplog.text
