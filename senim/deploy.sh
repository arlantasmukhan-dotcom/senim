#!/usr/bin/env bash
# Publishes the current local code to Vercel: backend (project senim-api) and site (project senim).
# Keys and the proxy token live in the Vercel projects' environment variables, not in these files.
# Run `npx vercel login` once if you are logged out.
set -euo pipefail
cd "$(dirname "$0")"
# A project-local npm cache avoids EACCES errors from root-owned files in ~/.npm.
export npm_config_cache="$PWD/.tools/npm-cache"

echo "Deploying the backend (senim-api)…"
npx --yes vercel@latest deploy --prod --yes > .tools/deploy-api.log 2>&1 || { tail -20 .tools/deploy-api.log; exit 1; }

echo "Deploying the site (senim)…"
(cd web && npx --yes vercel@latest deploy --prod --yes > ../.tools/deploy-web.log 2>&1) || { tail -20 .tools/deploy-web.log; exit 1; }

echo
echo "Done. Site: $(grep -oE 'Aliased +https://[^ ]+' .tools/deploy-web.log | awk '{print $2}' | tail -1)"
