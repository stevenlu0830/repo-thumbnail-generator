import pytest

from thumbgen.url_parser import InvalidLinkError, parse_repo_url


@pytest.mark.parametrize(
    "link",
    [
        "https://github.com/octocat/Hello-World",
        "http://github.com/octocat/Hello-World",
        "https://www.github.com/octocat/Hello-World",
        "github.com/octocat/Hello-World",
        "https://github.com/octocat/Hello-World/",
        "https://github.com/octocat/Hello-World.git",
        "https://github.com/octocat/Hello-World/tree/main/src",
        "https://github.com/octocat/Hello-World?tab=readme-ov-file#readme",
        "git@github.com:octocat/Hello-World.git",
        "octocat/Hello-World",
        "  octocat/Hello-World \n",
    ],
)
def test_accepts_common_link_forms(link):
    assert parse_repo_url(link) == ("octocat", "Hello-World")


def test_keeps_dots_and_underscores_in_repo_names():
    assert parse_repo_url("github.com/someone/my_repo.js") == ("someone", "my_repo.js")


@pytest.mark.parametrize(
    "link",
    [
        "",
        "octocat",
        "github.com",
        "https://github.com/octocat",
        "https://gitlab.com/octocat/Hello-World",
        "https://github.com/-octocat/Hello-World",
        "not a link",
    ],
)
def test_rejects_non_repo_links(link):
    with pytest.raises(InvalidLinkError):
        parse_repo_url(link)
