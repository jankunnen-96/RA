#!/bin/bash
set -e
cd /opt/matchadaddy/RA

# get_artists/followed_profiles.csv is gitignored day-to-day so a normal
# `git pull` never touches it (it's persistent VPS-only state, edited live
# by the app). Here we deliberately force-add and back it up to GitHub as
# a snapshot, so it survives a total loss of this server.
git add -f get_artists/followed_profiles.csv
if ! git diff --cached --quiet; then
  git commit -m "Backup followed artists [skip ci]"
  git push
fi

# Pull the latest code and data from GitHub.
git pull
