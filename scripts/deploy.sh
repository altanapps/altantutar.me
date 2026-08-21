#!/bin/zsh
# Stopgap auto-deploy: pull activity-refresh commits and push them to Railway.
# Runs hourly from launchd (me.altantutar.site-deploy) out of a dedicated
# clone at ~/.local/share/site-deploy — NOT the Desktop working copy, because
# macOS TCC blocks launchd jobs from reading anything under ~/Desktop.
# Only deploys when the pull actually moved HEAD. Delete this + the clone +
# the LaunchAgent once the Railway service is connected to the GitHub repo
# (then pushes deploy themselves).
set -e
cd "$HOME/.local/share/site-deploy"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
before=$(git rev-parse HEAD)
git pull --ff-only --quiet
after=$(git rev-parse HEAD)
if [ "$before" != "$after" ]; then
  railway up --service altantutar-me --detach
  echo "$(date -u +%FT%TZ) deployed $after" >> "$HOME/Library/Logs/site-deploy.log"
else
  echo "$(date -u +%FT%TZ) no change" >> "$HOME/Library/Logs/site-deploy.log"
fi
