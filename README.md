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

It asks for a repository link, then saves the thumbnail as `output/{owner}_{repo}.png`:

```
$ python -m thumbgen
Enter GitHub repo link: https://github.com/stevenlu0830/grade-calculator
Fetching stevenlu0830/grade-calculator ...
Saved output/stevenlu0830_grade-calculator.png
```

You can also pass the link directly, which is handy in scripts: `python -m thumbgen github.com/owner/repo`. Links like `github.com/owner/repo`, `git@github.com:owner/repo.git` or just `owner/repo` all work.

Without a token, GitHub allows 60 API requests an hour, and each run uses 4. To raise that to 5,000 (and to reach private repositories), create a [personal access token](https://github.com/settings/tokens) and set it before running:

```bash
export GITHUB_TOKEN=your-token-here
```

## Sample thumbnails

```bash
python -m scripts.render_samples
```

Draws thumbnails from hard-coded data into `output/` without calling GitHub, which is handy when changing the layout.

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
  fonts.py         # font loading, with CJK and emoji fallbacks
assets/            # fonts, icons, language colours (see assets/README.md)
scripts/
  build_assets.py  # re-downloads and regenerates assets/
  render_samples.py  # draws sample thumbnails from hard-coded data
tests/
  fixtures/        # a saved avatar so tests and samples run offline
```
