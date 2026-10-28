"""Tests for the web app, through Flask's test client with GitHub replaced by a fake."""

from dataclasses import replace
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

import app as web
from thumbgen import service
from thumbgen.github_api import GitHubError, NetworkError, RateLimitError, RepoNotFoundError
from thumbgen.models import RepoInfo

INFO = RepoInfo(
    owner="stevenlu0830",
    name="grade-calculator",
    description="UBC Grade Calculator",
    stars=1,
    forks=0,
    open_issues=0,
    contributors=2,
    languages={"TypeScript": 100},
    avatar=(Path(__file__).parent / "fixtures" / "stevenlu0830-avatar.png").read_bytes(),
)
PNG_URL = "/api/thumbnail/stevenlu0830/grade-calculator.png"


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


@pytest.mark.parametrize(
    "link",
    [
        "https://github.com/StevenLu0830/Grade-Calculator",
        "github.com/stevenlu0830/grade-calculator/tree/main/src",
        "git@github.com:stevenlu0830/grade-calculator.git",
        "  stevenlu0830/grade-calculator  ",
    ],
)
def test_any_link_redirects_to_the_repos_lowercase_address(client, fake_github, link):
    response = client.get("/api/thumbnail", query_string={"repo": link})

    assert response.status_code == 308
    assert response.headers["Location"] == PNG_URL
    assert fake_github == []  # checking a link doesn't use up GitHub requests


def test_following_the_redirect_gives_the_png(client, fake_github):
    response = client.get(
        "/api/thumbnail", query_string={"repo": "github.com/stevenlu0830/grade-calculator"}, follow_redirects=True
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
    assert response.headers["Content-Disposition"] == 'inline; filename="stevenlu0830_grade-calculator.png"'
    assert response.headers["Cache-Control"] == "public, s-maxage=3600, stale-while-revalidate=86400"
    with Image.open(BytesIO(response.data)) as image:
        assert image.size == (1200, 600)
    assert fake_github == [("stevenlu0830", "grade-calculator", None)]


def test_passes_github_token_from_the_environment(client, fake_github, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    client.get(PNG_URL)

    assert fake_github[0][2] == "test-token"


def test_mixed_case_address_redirects_to_lowercase(client, fake_github):
    response = client.get("/api/thumbnail/StevenLu0830/Grade-Calculator.png")

    assert response.status_code == 308
    assert response.headers["Location"] == PNG_URL
    assert fake_github == []


@pytest.mark.parametrize("url", ["/api/thumbnail/-owner/repo.png", "/api/thumbnail/owner/...png"])
def test_invalid_address_is_a_400(client, fake_github, url):
    response = client.get(url)

    assert response.status_code == 400
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


def test_token_problems_are_logged_for_the_site_owner(client, monkeypatch, caplog):
    monkeypatch.setattr(service, "fetch_repo_info", failing_with(GitHubError("GitHub rejected the GITHUB_TOKEN.")))
    client.get(PNG_URL)

    assert "GitHub rejected the GITHUB_TOKEN." in caplog.text
