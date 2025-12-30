"""ER Save Fixer package."""
from .save import Save, load_save
from .user_data_x import UserDataX
from .user_data_10 import UserData10
from .character import PlayerGameData
from .er_types import MapId, HorseState
from .world import RideGameData, WorldAreaWeather, WorldAreaTime

__all__ = [
    'Save',
    'load_save',
    'UserDataX',
    'UserData10',
    'PlayerGameData',
    'MapId',
    'HorseState',
    'RideGameData',
    'WorldAreaWeather',
    'WorldAreaTime',
]

# Keep in sync with `pyproject.toml` and `version_info.txt` (PyInstaller).
__version__ = "3.2.0"

"""ER Save Fixer package."""

__all__ = ["__version__"]

# Keep this in sync with `version_info.txt` (PyInstaller) and `pyproject.toml`.
__version__ = "3.2.0"

"""ER Save Fixer package."""

__all__ = ["__version__"]

# Keep this in sync with PyInstaller's `version_info.txt` as needed.
__version__ = "3.2.0"
