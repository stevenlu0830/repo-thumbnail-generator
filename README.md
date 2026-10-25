# repo-thumbnail-generator
A desktop app that will generate PNG thumbnail for your GitHub repository.

## Setup

Needs Python 3.11 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python -m thumbgen
```

It asks for a repository link, or you can pass one directly: `python -m thumbgen github.com/owner/repo`. For now it prints the data it fetched; drawing the thumbnail comes in a later phase.

Without a token, GitHub allows 60 API requests an hour, and each run uses 4. To raise that to 5,000 (and to reach private repositories), create a [personal access token](https://github.com/settings/tokens) and set it before running:

```bash
export GITHUB_TOKEN=your-token-here
```

## Tests

```bash
pytest
```

## Project layout

```
thumbgen/
  __main__.py      # CLI: ask for the link → fetch → render → save
  url_parser.py    # turns a link into (owner, repo)
  github_api.py    # REST calls → RepoInfo
  models.py        # RepoInfo dataclass
  renderer.py      # Pillow drawing
  layout.py        # sizes, colours, positions, asset paths
  text.py          # wrapping, truncation, number formatting
assets/            # fonts, icons, language colours (see assets/README.md)
scripts/
  build_assets.py  # re-downloads and regenerates assets/
tests/
```
