"""Tests for making a thumbnail as PNG bytes, with GitHub replaced by a fake."""

from dataclasses import replace
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from thumbgen import service
from thumbgen.github_api import RepoNotFoundError
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


@pytest.fixture
def fake_github(monkeypatch):
    """Record what ``fetch_repo_info`` was asked for, and return ``INFO`` instead of calling GitHub."""
    calls = []

    def fetch(owner, repo, token=None):
        calls.append((owner, repo, token))
        return INFO

    monkeypatch.setattr(service, "fetch_repo_info", fetch)
    return calls


def test_returns_a_png_of_the_thumbnail(fake_github):
    thumbnail = service.generate("stevenlu0830", "grade-calculator", token="test-token")

    assert fake_github == [("stevenlu0830", "grade-calculator", "test-token")]
    with Image.open(BytesIO(thumbnail.png)) as image:
        assert image.format == "PNG"
        assert image.size == (1200, 600)
    assert not thumbnail.avatar_missing


def test_names_the_file_the_way_github_spells_the_repo(fake_github):
    thumbnail = service.generate("StevenLu0830", "Grade-Calculator")

    assert thumbnail.filename == "stevenlu0830_grade-calculator.png"


def test_reports_a_missing_avatar(monkeypatch):
    monkeypatch.setattr(service, "fetch_repo_info", lambda owner, repo, token=None: replace(INFO, avatar=None))

    assert service.generate("stevenlu0830", "grade-calculator").avatar_missing


def test_lets_github_errors_through(monkeypatch):
    def fetch(owner, repo, token=None):
        raise RepoNotFoundError("Repository not found.")

    monkeypatch.setattr(service, "fetch_repo_info", fetch)
    with pytest.raises(RepoNotFoundError):
        service.generate("stevenlu0830", "missing")
