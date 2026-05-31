"""Entry point for `python -m opennarrator`."""

import sys

if __name__ == "__main__":
    from opennarrator.cli.main import app

    sys.exit(app())
