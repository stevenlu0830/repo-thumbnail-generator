"""Tests for the command line, with GitHub replaced by a fake and run in a temporary folder."""

from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image

from thumbgen import __main__ as cli
from thumbgen import service
from thumbgen.github_api import RepoNotFoundError
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
    avatar=None,
)
SAVED = "output/JetBrains_thinkrail.png"
AVATAR = (Path(__file__).parent / "fixtures" / "jetbrains-avatar.png").read_bytes()


@pytest.fixture
def fake_github(monkeypatch, tmp_path):
    """Run in an empty folder, and record what ``fetch_repo_info`` was asked for instead of calling GitHub."""
    monkeypatch.chdir(tmp_path)
    calls = []

    def fetch(owner, repo, token=None):
        calls.append((owner, repo, token))
        return INFO

    monkeypatch.setattr(service, "fetch_repo_info", fetch)
    return calls


def test_saves_a_thumbnail_for_a_link_argument(fake_github, tmp_path, capsys):
    cli.main(["https://github.com/JetBrains/thinkrail"])

    assert fake_github == [("JetBrains", "thinkrail", None)]
    with Image.open(tmp_path / SAVED) as image:
        assert image.size == (1200, 600)
    out = capsys.readouterr().out
    assert f"Saved {SAVED}" in out
    assert "placeholder" in out  # INFO has no avatar


def test_says_nothing_about_the_avatar_when_it_downloaded(fake_github, monkeypatch, capsys):
    monkeypatch.setattr(service, "fetch_repo_info", lambda owner, repo, token=None: replace(INFO, avatar=AVATAR))
    cli.main(["JetBrains/thinkrail"])

    assert "placeholder" not in capsys.readouterr().out


def test_asks_for_a_link_when_none_is_given(fake_github, tmp_path, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "git@github.com:JetBrains/thinkrail.git")
    cli.main([])

    assert (tmp_path / SAVED).exists()


def test_passes_github_token_from_the_environment(fake_github, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    cli.main(["JetBrains/thinkrail"])

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

    monkeypatch.setattr(service, "fetch_repo_info", fetch)
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["stevenlu0830/missing"])

    assert exit_info.value.code == "Error: Repository not found."
