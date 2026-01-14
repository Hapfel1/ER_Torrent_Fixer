"""ER Save Fixer package."""

from .parser import (
    HorseState,
    MapId,
    RideGameData,
    Save,
    UserDataX,
    load_save,
)

__all__ = [
    "Save",
    "load_save",
    "UserDataX",
    "MapId",
    "HorseState",
    "RideGameData",
]

# Keep in sync with `pyproject.toml` and `version_info.txt` (PyInstaller).
__version__ = "3.3.1"

"""ER Save Fixer package."""

__all__ = ["__version__"]

# Keep this in sync with `version_info.txt` (PyInstaller) and `pyproject.toml`.
__version__ = "3.3.1"

"""ER Save Fixer package."""

__all__ = ["__version__"]

# Keep this in sync with PyInstaller's `version_info.txt` as needed.
__version__ = "3.3.1"
