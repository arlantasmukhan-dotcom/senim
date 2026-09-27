#!/usr/bin/env bash
# Fastest way to show SENIM to friends: a public https://….trycloudflare.com link to the site on this Mac.
# If ./start.sh is already running, the link is ready in a few seconds; otherwise this starts the site too
# (no build step). The link works while this terminal stays open; Ctrl+C closes it.
set -euo pipefail
cd "$(dirname "$0")"
WEB_PORT="${WEB_PORT:-3000}"
CF=.tools/cloudflared
SITE=""

if [ ! -x "$CF" ]; then
  echo "Downloading cloudflared (one time)…"
  mkdir -p .tools
  arch=$(uname -m); [ "$arch" = "x86_64" ] && arch=amd64
  curl -sSL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-$arch.tgz" | tar -xz -C .tools
  chmod +x "$CF"
fi

if ! curl -s -o /dev/null "http://localhost:$WEB_PORT"; then
  echo "Starting the site…"
  WEB_PORT="$WEB_PORT" ./start.sh > .tools/site.log 2>&1 &
  SITE=$!
  until curl -s -o /dev/null "http://localhost:$WEB_PORT"; do
    kill -0 "$SITE" 2>/dev/null || { echo "The site did not start, see senim/.tools/site.log"; exit 1; }
    sleep 1
  done
fi
trap '[ -n "$SITE" ] && kill "$SITE" 2>/dev/null; true' EXIT INT TERM

# Compile the pages once so the first visitor does not wait for the dev server.
curl -s -o /dev/null "http://localhost:$WEB_PORT/" || true
curl -s -o /dev/null "http://localhost:$WEB_PORT/check" || true

echo "Opening the public link…"
"$CF" tunnel --no-autoupdate --url "http://localhost:$WEB_PORT" 2>&1 \
  | grep --line-buffered -oE "https://[a-z0-9-]+\.trycloudflare\.com" \
  | while read -r url; do
      echo
      echo "  Ссылка для друзей: $url"
      echo "  Работает, пока открыт этот терминал. Ctrl+C закрывает ссылку."
      echo
    done
