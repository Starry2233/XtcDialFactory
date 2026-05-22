#!/usr/bin/env python3
"""XTC Dial Factory - 小天才电话手表表盘开发IDE."""

import sys
import os
import argparse
import logging

# Ensure the package directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from xtc_dial_factory.app import create_app
from xtc_dial_factory.views.main_window import MainWindow


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="XTC Dial Factory IDE")
    parser.add_argument("--project", "-p", help="Open project directory on startup")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    return parser.parse_args(argv[1:])


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    args = parse_args(sys.argv)
    if args.version:
        from xtc_dial_factory import __version__, __app_name__
        print(f"{__app_name__} v{__version__}")
        return 0

    setup_logging(args.verbose)

    app = create_app(sys.argv)

    window = MainWindow()
    window.show()

    # Open project if specified
    if args.project and os.path.isdir(args.project):
        window._load_project(args.project)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
