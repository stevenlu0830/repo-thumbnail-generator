# Assets

Everything here is produced by [`scripts/build_assets.py`](../scripts/build_assets.py) from pinned upstream versions and committed, so the app needs nothing beyond `requirements.txt` to run.

| File(s) | Source | Licence |
|---|---|---|
| `fonts/MonaSans-Regular.ttf`, `fonts/MonaSans-Bold.ttf` | [Mona Sans](https://github.com/github/mona-sans) v2.0.27 | SIL Open Font License 1.1 (`fonts/MonaSans-OFL.txt`) |
| `fonts/NotoSansSC-Regular.otf`, `fonts/NotoSansKR-Regular.otf` | [Noto Sans CJK](https://github.com/notofonts/noto-cjk) Sans2.004, the SC subset (Chinese and Japanese) and KR subset (Korean). Fallbacks for descriptions. | SIL Open Font License 1.1 (`fonts/NotoSansCJK-OFL.txt`) |
| `fonts/NotoEmoji.ttf` | [Noto Emoji](https://github.com/google/fonts/tree/main/ofl/notoemoji) (monochrome) from google/fonts at commit 8b0a1d0. Fallback for emoji in descriptions. | SIL Open Font License 1.1 (`fonts/NotoEmoji-OFL.txt`) |
| `icons/*.png` | [Octicons](https://github.com/primer/octicons) 19.41.0, the 24px SVGs rasterised to 128×128 black-on-transparent PNGs | MIT (`icons/LICENSE.txt`) |
| `language_colors.json` | The `color` of each language in [Linguist](https://github.com/github-linguist/linguist)'s `languages.yml`, v9.7.0 | MIT (`language_colors.LICENSE.txt`) |
