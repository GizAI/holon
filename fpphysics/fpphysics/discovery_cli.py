"""Backward-compatible entry point for automatic discovery."""

from .discover_cli import main

if __name__ == "__main__":
    raise SystemExit(main())
