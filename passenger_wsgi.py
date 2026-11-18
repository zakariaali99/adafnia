"""Passenger entry point (Libyan Spider cPanel).

Production settings live outside the repo in ~/.adafnia.env as `export NAME=value` lines,
the same file deploy.sh sources, so the web app and the shell always share one configuration.
"""
import os
from pathlib import Path

env_file = Path.home() / '.adafnia.env'
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line.startswith('export '):
            line = line[len('export '):]
        if not line or line.startswith('#') or '=' not in line:
            continue
        name, value = line.split('=', 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))

from config.wsgi import application  # noqa: E402
