"""Compatibility shim for legacy imports.

The implementation moved to `src/er_save_fixer/parser.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    repo_root = Path(__file__).resolve().parent
    src_dir = repo_root / "src"
    if src_dir.is_dir():
        sys.path.insert(0, str(src_dir))


_ensure_src_on_path()

from er_save_fixer.parser import (  # noqa: E402
    CSPlayerCoords,
    CharacterSlot,
    EldenRingSaveFile,
    FloatVector3,
    FloatVector4,
    HorseState,
    MapID,
    RideGameData,
    WorldAreaTime,
    WorldAreaWeather,
)

__all__ = [
    "CSPlayerCoords",
    "CharacterSlot",
    "EldenRingSaveFile",
    "FloatVector3",
    "FloatVector4",
    "HorseState",
    "MapID",
    "RideGameData",
    "WorldAreaTime",
    "WorldAreaWeather",
]