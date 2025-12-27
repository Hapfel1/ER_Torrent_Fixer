"""PyInstaller entrypoint for the GUI.

This avoids relying on root-level compatibility shims and keeps the build stable
as the project structure evolves.
"""

# ruff: noqa: I001

from __future__ import annotations

from er_save_fixer.gui import main  # pyright: ignore[reportMissingImports]


if __name__ == "__main__":
    main()
