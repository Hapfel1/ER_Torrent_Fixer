"""
Compatibility wrapper for the new modular parser.

This file provides backward compatibility by mapping old API names to new ones.
The actual implementation is in the parser/ subpackage.
"""

from __future__ import annotations

from .parser.er_types import FloatVector3, FloatVector4, HorseState, MapId

# Import from parser subpackage
from .parser.save import Save, load_save
from .parser.user_data_x import UserDataX
from .parser.world import (
    PlayerCoordinates,
    RideGameData,
    WorldAreaTime,
    WorldAreaWeather,
)

# Compatibility aliases (old name → new name)
EldenRingSaveFile = Save
CharacterSlot = UserDataX
MapID = MapId
CSPlayerCoords = PlayerCoordinates

__all__ = [
    # New names (preferred)
    "Save",
    "UserDataX",
    "MapId",
    "HorseState",
    "RideGameData",
    "WorldAreaWeather",
    "WorldAreaTime",
    "PlayerCoordinates",
    "FloatVector3",
    "FloatVector4",
    "load_save",
    # Old names (compatibility)
    "EldenRingSaveFile",
    "CharacterSlot",
    "MapID",
    "CSPlayerCoords",
]
