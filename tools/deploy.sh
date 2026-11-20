#!/bin/sh
# Publishes the v2 brand hub to Netlify (starman-brand-hub-v2). Only index.html, assets/ and fonts/ go up;
# backups and tools stay local. Usage: sh tools/deploy.sh
set -e
SITE=5a3cda7b-d8bd-4f8f-9a34-7be688449efa
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$(mktemp -d)"
cp "$HERE/index.html" "$OUT/"
cp -R "$HERE/assets" "$HERE/fonts" "$OUT/"
find "$OUT" -name .DS_Store -delete
# keep the hub out of search engines
printf '/*\n  X-Robots-Tag: noindex, nofollow\n' > "$OUT/_headers"
netlify deploy --prod --dir "$OUT" --site "$SITE" --no-build
rm -rf "$OUT"
