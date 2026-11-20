# Starman Brand Hub v2

Single-page brand guideline for Starman: strategy, logo, colour, photography, avatar, typography, icons, dashboard, telemetry, thinking orbs and downloads.

- Live: https://starman-brand-hub-v2.netlify.app
- Preview locally: `python3 -m http.server 8793`, then open http://localhost:8793/
- Deploy: `sh tools/deploy.sh` (publishes `index.html`, `assets/` and `fonts/` to Netlify)

## Generated files

Do not hand-edit these; change the script and run it.

- `python3 tools/build_logo.py` writes the mark (`assets/starman-mark*.svg`, `starman-mono-white.svg`, `starman-avatar.png`, favicons) and the `sm-light` / `sm-sun` symbols in `index.html`. Needs Pillow.
- `python3 tools/build_icons.py` writes `assets/icons/` and the Icons chapter in `index.html`.

## Not for redistribution

- `fonts/` holds the licensed Anxler typeface.
- `assets/photo/` holds style-reference photographs from another shoot.

Keep this repository private unless both are removed.
