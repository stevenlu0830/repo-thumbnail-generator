"""Tests for the command line, with GitHub replaced by a fake and run in a temporary folder."""

import pytest
from PIL import Image

from thumbgen import __main__ as cli
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
    avatar=None,
)
SAVED = "output/stevenlu0830_grade-calculator.png"


@pytest.fixture
def fake_github(monkeypatch, tmp_path):
    """Run in an empty folder, and record what ``fetch_repo_info`` was asked for instead of calling GitHub."""
    monkeypatch.chdir(tmp_path)
    calls = []

    def fetch(owner, repo, token=None):
        calls.append((owner, repo, token))
        return INFO

    monkeypatch.setattr(cli, "fetch_repo_info", fetch)
    return calls


def test_saves_a_thumbnail_for_a_link_argument(fake_github, tmp_path, capsys):
    cli.main(["https://github.com/stevenlu0830/grade-calculator"])

    assert fake_github == [("stevenlu0830", "grade-calculator", None)]
    with Image.open(tmp_path / SAVED) as image:
        assert image.size == (1200, 600)
    assert f"Saved {SAVED}" in capsys.readouterr().out


def test_asks_for_a_link_when_none_is_given(fake_github, tmp_path, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "git@github.com:stevenlu0830/grade-calculator.git")
    cli.main([])

    assert (tmp_path / SAVED).exists()


def test_passes_github_token_from_the_environment(fake_github, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    cli.main(["stevenlu0830/grade-calculator"])

    assert fake_github[0][2] == "test-token"


def test_invalid_link_exits_with_a_message(fake_github, tmp_path):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["not a link"])

    assert str(exit_info.value.code).startswith("Error: ")
    assert fake_github == []
    assert not (tmp_path / "output").exists()


def test_github_errors_exit_with_a_message(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    def fetch(owner, repo, token=None):
        raise RepoNotFoundError("Repository not found.")

    monkeypatch.setattr(cli, "fetch_repo_info", fetch)
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["stevenlu0830/missing"])

    assert exit_info.value.code == "Error: Repository not found."
