#!/bin/sh
# Server update (Libyan Spider cPanel). Run on the server: ~/adafnia/deploy.sh
# Pulls the latest main from GitHub, then installs, migrates, collects static files and restarts Passenger.
# Production settings live outside the repo in ~/.adafnia.env (never commit it).
set -eu
cd "$(dirname "$0")"
. "$HOME/.adafnia.env"
. "$(ls -d "$HOME"/virtualenv/adafnia/*/bin/activate | tail -1)"
git pull --ff-only origin master
pip install -q -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput -v 0
python manage.py check --deploy
mkdir -p tmp && touch tmp/restart.txt
echo "Deployed $(git log --oneline -1)"
