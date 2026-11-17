# Images

| File | Size | Used by | Notes |
|---|---|---|---|
| `banner.png` | 1280 × 320 px | `README.md` and the translated READMEs | Wordmark, tagline and the Nova mark on the page's dark background. |
| `icon.png` | 512 × 512 px, transparent | The chat page, served at `GET /docs/img/icon.png` | The page tints it white with a CSS filter, so keep the background transparent. |
| `social-preview.png` | 1280 × 640 px | Upload under GitHub *Settings → General → Social preview* | Same artwork as the banner at GitHub's recommended size. Not referenced from the repository itself. |
| `screenshots/chat-desktop.png` | 1400 × 1260 px | `README.md` | Capture of `src/index.html` on a desktop browser. |
| `screenshots/chat-mobile.png` | 520 × 1125 px | `README.md` | Capture of `src/index.html` on a phone. |
| `badges/*.svg` | 20 px high | `README.md` and the translated READMEs | Version, license, runtime and dependency badges, each linking to the file that backs it (changelog, `LICENSE`, install guide, architecture notes). Edit `badges/generate_badges.py` and run it to regenerate them (standard library only). |

The brand colours are the CSS variables at the top of `src/index.html`: `--bg` `#05070f`, `--panel` `rgba(13, 18, 34, 0.72)`, `--accent` `#6c8cff`, `--accent-2` `#a855f7`, `--cyan` `#22d3ee`, `--text` `#e8ecf7` and `--muted` `#8b95b2`.
