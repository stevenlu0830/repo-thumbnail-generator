"""Data classes shared between the API client and the renderer."""

from dataclasses import dataclass, field


@dataclass
class RepoInfo:
    """Everything the thumbnail shows about one repository."""

    owner: str
    name: str
    description: str | None
    stars: int
    forks: int
    open_issues: int  # pull requests not included
    contributors: int | None  # None when GitHub won't count them (very large repos)
    languages: dict[str, int]  # language name → bytes of code, largest first
    avatar: bytes | None = field(repr=False)  # owner's avatar image; None if the download failed
