# repo-thumbnail-generator

Generate a GitHub-style social preview image (a 1200×600 PNG) for any GitHub repository, from its link.

![Thumbnail for stevenlu0830/grade-calculator](tests/snapshots/grade-calculator.png)

Like GitHub's own link previews, it shows:

- the `owner/repo` title, with the repo name in bold, shrinking and wrapping for long names
- the owner's avatar (a user or an organisation)
- the description, including emoji and Chinese, Japanese and Korean text
- contributors, open issues (not counting pull requests), stars and forks, shortened like `45.3k`
- a language bar in GitHub's language colours, and the GitHub logo

![Thumbnail with emoji, CJK text and many small languages](tests/snapshots/international.png)

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

You can also pass the link as an argument, which is handy in scripts:

```bash
python -m thumbgen github.com/pallets/flask
```

Any common form of link works: `https://github.com/owner/repo`, `github.com/owner/repo`, links to a branch or file (`…/tree/main/src`), `git@github.com:owner/repo.git`, or just `owner/repo`.

If something goes wrong, it stops with a one-line message instead of a traceback. For example:

```
$ python -m thumbgen stevenlu0830/no-such-repo
Fetching stevenlu0830/no-such-repo ...
Error: Repository not found. Check the link; a private repository also needs a GITHUB_TOKEN that can read it.
```

## GitHub token (optional)

Without a token, GitHub allows 60 API requests an hour from your IP address, and each thumbnail uses 4. A token raises that to 5,000 an hour and lets the tool read private repositories.

1. Create a [fine-grained personal access token](https://github.com/settings/personal-access-tokens/new).
   - For public repositories, choose **Public repositories (read-only)**. No other permissions are needed.
   - For private repositories, select them and give read-only access to **Contents**, **Metadata** and **Pull requests**.
2. Set it in your terminal before running the tool:

   ```bash
   export GITHUB_TOKEN=your-token-here
   ```

   This lasts until you close the terminal. Never put the token in a file you commit.

The token is only sent to `api.github.com`.

## How it works

```
repo link ──url_parser──▶ (owner, repo) ──github_api──▶ RepoInfo ──renderer──▶ PNG
```

1. [`url_parser.py`](thumbgen/url_parser.py) turns the link into an owner and repo name.
2. [`github_api.py`](thumbgen/github_api.py) makes 4 requests to the GitHub REST API, plus one avatar download:

   | Data | Endpoint |
   |---|---|
   | Description, stars, forks, open issues, avatar URL | `GET /repos/{owner}/{repo}` |
   | Bytes of code per language | `GET /repos/{owner}/{repo}/languages` |
   | Number of contributors | `GET /repos/{owner}/{repo}/contributors?per_page=1`, reading the last page number from the `Link` header |
   | Number of open pull requests, subtracted from open issues | `GET /repos/{owner}/{repo}/pulls?state=open&per_page=1`, the same way |

   It collects everything in a [`RepoInfo`](thumbgen/models.py).
3. [`renderer.py`](thumbgen/renderer.py) draws the image with Pillow. Every size, colour and position is in [`layout.py`](thumbgen/layout.py). They were measured from GitHub's own previews.

## Limitations

- **Emoji are monochrome**, in the description's grey. Combined emoji (like 👨‍👩‍👧) show as separate emoji, and `:shortcode:` emoji show as text.
- **Very large repos** like `torvalds/linux`: GitHub's API won't count their contributors, so the thumbnail shows `5k+`.
- **The font is a close match, not exact.** Mona Sans is slightly narrower than the font in GitHub's previews.
- **GitHub's own previews are cached**, so they can show older data (such as the language bar) than this tool, which always uses current data.

## Development

### Tests

```bash
pytest
```

The tests never call GitHub: the API tests use a fake session, and the CLI tests replace the API call.

| File | Covers |
|---|---|
| `test_url_parser.py` | Every accepted link form, and rejecting non-repo links |
| `test_github_api.py` | Counting via `Link` headers, issues minus pull requests, error messages (not found, rate limit, bad token, no network), huge repos |
| `test_text.py` | Number formatting (`1.2k`), Star/Stars, word and CJK wrapping, "…" truncation, title wrapping |
| `test_fonts.py` | Which font draws each character (Mona Sans, emoji, CJK) |
| `test_renderer.py` | Language bar widths and colours, avatar placeholder, title sizing |
| `test_main.py` | The command line: prompt or argument, saving, error messages |
| `test_assets.py` | The bundled fonts, icons and colours load |
| `test_snapshots.py` | Whole thumbnails, compared with reference images |

### Snapshot tests

`test_snapshots.py` draws each sample in [`tests/samples.py`](tests/samples.py) and compares it with the reference image in [`tests/snapshots/`](tests/snapshots/). Any visible change fails the test. The test then saves the new image and a diff (changed pixels in red) to `output/snapshot-failures/`.

When a change is intended, regenerate the references, look at them, and commit them with your change:

```bash
UPDATE_SNAPSHOTS=1 pytest tests/test_snapshots.py
```

### Changing the layout

1. Edit the values in [`layout.py`](thumbgen/layout.py).
2. Draw the samples without calling GitHub, and look at them in `output/`:

   ```bash
   python -m scripts.render_samples
   ```

3. When you're happy with them, update the snapshots as above.

### Rebuilding the assets

Fonts, icons and language colours are downloaded from pinned versions and committed, so the app needs nothing else to run. To refresh them, see [`scripts/build_assets.py`](scripts/build_assets.py) and [`assets/README.md`](assets/README.md).

## Project layout

```
thumbgen/
  __main__.py        # command line: ask for the link → fetch → render → save
  url_parser.py      # turns a link into (owner, repo)
  github_api.py      # GitHub REST calls → RepoInfo
  models.py          # the RepoInfo dataclass
  renderer.py        # Pillow drawing
  layout.py          # sizes, colours, positions, asset paths
  text.py            # wrapping, truncation, number formatting
  fonts.py           # font loading, with CJK and emoji fallbacks
assets/              # fonts, icons, language colours (sources and licences in assets/README.md)
scripts/
  build_assets.py    # re-downloads and regenerates assets/
  render_samples.py  # draws the samples into output/
tests/
  samples.py         # hard-coded RepoInfo samples
  snapshots/         # reference images for the snapshot tests
  fixtures/          # a saved avatar, so tests and samples run offline
```

## Credits

Fonts: [Mona Sans](https://github.com/github/mona-sans), [Noto Sans CJK](https://github.com/notofonts/noto-cjk) and [Noto Emoji](https://github.com/googlefonts/noto-emoji) (SIL Open Font License). Icons: [Octicons](https://github.com/primer/octicons) (MIT). Language colours: [Linguist](https://github.com/github-linguist/linguist) (MIT). Details are in [`assets/README.md`](assets/README.md).
