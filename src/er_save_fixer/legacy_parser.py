"""
Elden Ring Save File Parser
Implementation that calculates actual offsets from the template structure
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum


class HorseState(IntEnum):
    """Torrent/Horse states"""

    INACTIVE = 1
    DEAD = 3
    ACTIVE = 13


@dataclass
class FloatVector3:
    """3D coordinates"""

    x: float
    y: float
    z: float

    @classmethod
    def from_bytes(cls, data: bytes, offset: int):
        x, y, z = struct.unpack("<fff", data[offset : offset + 12])
        return cls(x, y, z)

    def to_bytes(self) -> bytes:
        return struct.pack("<fff", self.x, self.y, self.z)

    def __str__(self):
        return f"({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"


@dataclass
class FloatVector4:
    """Quaternion/Angle"""

    x: float
    y: float
    z: float
    w: float

    @classmethod
    def from_bytes(cls, data: bytes, offset: int):
        x, y, z, w = struct.unpack("<ffff", data[offset : offset + 16])
        return cls(x, y, z, w)

    def to_bytes(self) -> bytes:
        return struct.pack("<ffff", self.x, self.y, self.z, self.w)


@dataclass
class MapID:
    """Map identifier (4 bytes, displayed in reverse)"""

    data: bytes  # 4 bytes

    @classmethod
    def from_bytes(cls, data: bytes, offset: int):
        return cls(bytes(data[offset : offset + 4]))

    def to_bytes(self) -> bytes:
        return self.data

    def to_string(self) -> str:
        """Display as XX_XX_XX_XX (actual byte order from file)"""
        return f"{self.data[0]:02X}_{self.data[1]:02X}_{self.data[2]:02X}_{self.data[3]:02X}"

    def to_string_decimal(self) -> str:
        """Display as decimal values in map coordinate format (reversed byte order)"""
        return f"{self.data[3]:d} {self.data[2]:d} {self.data[1]:d} {self.data[0]:d}"

    def is_dlc(self) -> bool:
        """Check if this is a DLC map"""
        map_prefix = self.data[3]

        if map_prefix == 0x3D:  # 61 decimal
            return True

        if 0x14 <= map_prefix <= 0x2B:  # 20-43
            return True

        return False


@dataclass
class WorldAreaTime:
    """World area time structure (CSWorldAreaTime) - 0xC bytes"""

    hour: int
    minute: int
    seconds: int

    SIZE = 0xC

    @classmethod
    def from_bytes(cls, data: bytes, offset: int):
        hour = struct.unpack("<I", data[offset : offset + 4])[0]
        minute = struct.unpack("<I", data[offset + 4 : offset + 8])[0]
        seconds = struct.unpack("<I", data[offset + 8 : offset + 12])[0]
        return cls(hour, minute, seconds)

    def to_bytes(self) -> bytes:
        result = bytearray()
        result.extend(struct.pack("<I", self.hour))
        result.extend(struct.pack("<I", self.minute))
        result.extend(struct.pack("<I", self.seconds))
        return bytes(result)

    def is_zero(self) -> bool:
        """Check if time is 00:00:00 (corrupted)"""
        return self.hour == 0 and self.minute == 0 and self.seconds == 0

    def get_formatted(self) -> str:
        """Get formatted time as HH:MM:SS"""
        return f"{self.hour:02d}:{self.minute:02d}:{self.seconds:02d}"

    @classmethod
    def from_seconds(cls, total_seconds: int):
        """Create WorldAreaTime from total seconds"""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        return cls(hours, minutes, secs)

    def __str__(self):
        return f"{self.hour:02d}:{self.minute:02d}:{self.seconds:02d}"


@dataclass
class WorldAreaWeather:
    """World area weather structure (CSWorldAreaWeather) - 0xC bytes"""

    area_id: int  # uint16
    weather_type: int  # uint16 (enum)
    timer: int  # uint32

    SIZE = 0xC

    @classmethod
    def from_bytes(cls, data: bytes, offset: int):
        area_id = struct.unpack("<H", data[offset : offset + 2])[0]
        weather_type = struct.unpack("<H", data[offset + 2 : offset + 4])[0]
        timer = struct.unpack("<I", data[offset + 4 : offset + 8])[0]
        return cls(area_id, weather_type, timer)

    def to_bytes(self) -> bytes:
        result = bytearray()
        result.extend(struct.pack("<H", self.area_id))
        result.extend(struct.pack("<H", self.weather_type))
        result.extend(struct.pack("<I", self.timer))
        result.extend(bytes(4))  # Padding to 0xC
        return bytes(result)

    def is_corrupted(self) -> bool:
        """Check if AreaId is 0 (corrupted)"""
        return self.area_id == 0


@dataclass
class RideGameData:
    """Torrent/Horse data - Length: 0x28 (40 bytes)"""

    coordinates: FloatVector3
    map_id: MapID
    angle: FloatVector4
    hp: int
    state: HorseState

    SIZE = 0x28

    @classmethod
    def from_bytes(cls, data: bytes, offset: int):
        coords = FloatVector3.from_bytes(data, offset)
        map_id = MapID.from_bytes(data, offset + 12)
        angle = FloatVector4.from_bytes(data, offset + 16)
        hp = struct.unpack("<I", data[offset + 32 : offset + 36])[0]
        state = HorseState(struct.unpack("<I", data[offset + 36 : offset + 40])[0])
        return cls(coords, map_id, angle, hp, state)

    def to_bytes(self) -> bytes:
        result = bytearray()
        result.extend(self.coordinates.to_bytes())
        result.extend(self.map_id.to_bytes())
        result.extend(self.angle.to_bytes())
        result.extend(struct.pack("<I", self.hp))
        result.extend(struct.pack("<I", int(self.state)))
        return bytes(result)

    def has_bug(self) -> bool:
        """Check if Torrent has the stuck loading bug"""
        return self.hp == 0 and self.state == HorseState.ACTIVE

    def fix_bug(self):
        """Fix the bug by setting state to Dead"""
        if self.has_bug():
            self.state = HorseState.DEAD


@dataclass
class CSPlayerCoords:
    """Player coordinates structure - Length: 0x3D (61 bytes)"""

    coordinates: FloatVector3
    map_id: MapID
    angle: FloatVector4

    MIN_SIZE = 32

    @classmethod
    def from_bytes(cls, data: bytes, offset: int):
        coords = FloatVector3.from_bytes(data, offset)
        map_id = MapID.from_bytes(data, offset + 12)
        angle = FloatVector4.from_bytes(data, offset + 16)
        return cls(coords, map_id, angle)

    def to_bytes(self) -> bytes:
        """Returns first 32 bytes (coords + mapid + angle)"""
        result = bytearray()
        result.extend(self.coordinates.to_bytes())
        result.extend(self.map_id.to_bytes())
        result.extend(self.angle.to_bytes())
        return bytes(result)


class CharacterSlot:
    """Parses a single character slot"""

    def __init__(self, data: bytearray, slot_index: int):
        self.data = data
        self.slot_index = slot_index

        self.HEADER_SIZE = 0x300
        self.SLOT_SIZE = 0x280000
        self.CHECKSUM_SIZE = 0x10

        self.WORLD_AREA_WEATHER_OFFSET = 0
        self.WORLD_AREA_TIME_OFFSET = 0
        self.STEAM_ID_OFFSET = 0
        self._corruption_structures_found = False

        self.slot_offset = self.HEADER_SIZE + (
            slot_index * (self.SLOT_SIZE + self.CHECKSUM_SIZE)
        )
        self.checksum_offset = self.slot_offset
        self.data_start = self.slot_offset + self.CHECKSUM_SIZE

        self.version: int | None = None
        self.map_id: MapID | None = None
        self.gaitem_count: int = 0
        self.gaitem_map_end: int = 0
        self.player_data_offset: int = 0
        self.horse_offset: int = 0
        self.player_coords_offset: int = 0

        self._parse_structure()

    def _parse_structure(self):
        """Parse through the structure to find exact offsets (minimal work for speed)"""
        offset = self.data_start

        self.version = struct.unpack("<I", self.data[offset : offset + 4])[0]
        offset += 4

        self.map_id = MapID.from_bytes(self.data, offset)
        offset += 4

        offset += 0x18

        if self.version <= 81:
            self.gaitem_count = 0x13FE
        else:
            self.gaitem_count = 0x1400

        # Parse GaitemHandleMap to find player_data_offset (needed for get_character_name)
        for _ in range(self.gaitem_count):
            gaitem_handle = struct.unpack("<I", self.data[offset : offset + 4])[0]
            offset += 4
            offset += 4

            if gaitem_handle != 0:
                handle_type = gaitem_handle & 0xF0000000
                if handle_type == 0x80000000:
                    offset += 4
                    offset += 4
                    offset += 4
                    offset += 1
                elif handle_type == 0x90000000:
                    offset += 4
                    offset += 4

        self.gaitem_map_end = offset
        self.player_data_offset = offset

    def _ensure_horse_data(self):
        """Lazy load horse data on first access"""
        if self.horse_offset == 0:
            search_start = self.data_start + 0x10000
            search_end = min(
                self.data_start + 0x50000, self.data_start + self.SLOT_SIZE
            )
            self.horse_offset = self._find_horse_data(search_start, search_end)

    def _ensure_player_coords(self):
        """Lazy load player coords on first access"""
        if self.player_coords_offset == 0:
            search_start = self.data_start + 0x1E0000
            search_end = self.data_start + 0x210000
            self.player_coords_offset = self._find_player_coords(
                search_start, search_end
            )

    def _ensure_corruption_structures(self):
        """Lazy loader for corruption structures"""
        if not self._corruption_structures_found and self.version and self.version > 0:
            self._find_corruption_structures()
            self._corruption_structures_found = True

    def _find_corruption_structures(self):
        """Search for corruption-related structures (WorldAreaWeather, WorldAreaTime, SteamID)"""

        weather_search_start = self.data_start + 0x214000
        weather_search_end = self.data_start + 0x21C000

        weather_candidates = []

        for offset in range(weather_search_start, weather_search_end, 1):
            try:
                area_id = struct.unpack("<H", self.data[offset : offset + 2])[0]
                weather_type = struct.unpack("<H", self.data[offset + 2 : offset + 4])[
                    0
                ]
                timer = struct.unpack("<I", self.data[offset + 4 : offset + 8])[0]

                if area_id > 255:
                    continue
                if weather_type > 100:
                    continue
                if timer > 100000:
                    continue

                time_hour = struct.unpack(
                    "<I", self.data[offset + 0xC : offset + 0x10]
                )[0]
                time_min = struct.unpack(
                    "<I", self.data[offset + 0x10 : offset + 0x14]
                )[0]
                time_sec = struct.unpack(
                    "<I", self.data[offset + 0x14 : offset + 0x18]
                )[0]

                if not (time_hour < 200 and time_min < 60 and time_sec < 60):
                    continue

                base_version_copy = struct.unpack(
                    "<i", self.data[offset + 0x18 : offset + 0x1C]
                )[0]
                base_version = struct.unpack(
                    "<i", self.data[offset + 0x1C : offset + 0x20]
                )[0]
                base_version_is_latest = struct.unpack(
                    "<i", self.data[offset + 0x20 : offset + 0x24]
                )[0]

                if not (0 <= base_version <= 300):
                    continue

                if base_version_copy != base_version:
                    continue

                if base_version_is_latest not in [0, 1]:
                    continue

                coords_offset = offset - 0x20050

                x, y, z = struct.unpack(
                    "<fff", self.data[coords_offset : coords_offset + 12]
                )
                map_bytes = bytes(self.data[coords_offset + 12 : coords_offset + 16])

                if abs(x) < 1.0 and abs(y) < 1.0:
                    continue

                if not (-10000 < x < 10000 and -5000 < y < 5000 and -10000 < z < 10000):
                    continue
                if map_bytes == bytes([0, 0, 0, 0]) or map_bytes == bytes([0xFF] * 4):
                    continue
                if not (0x0A <= map_bytes[3] <= 0x70):
                    continue

                score = 0
                if area_id > 0:
                    score += 10
                if time_hour > 0 or time_min > 0 or time_sec > 0:
                    score += 5
                if 50 <= base_version <= 100:
                    score += 15
                elif 0 < base_version < 300:
                    score += 5

                if score == 0:
                    score = 1

                weather_candidates.append(
                    (
                        coords_offset,
                        score,
                        area_id,
                        time_hour,
                        time_min,
                        time_sec,
                        x,
                        y,
                        z,
                        map_bytes,
                        base_version,
                    )
                )

            except Exception:
                continue

        if not weather_candidates:
            self.WORLD_AREA_WEATHER_OFFSET = 0
            self.WORLD_AREA_TIME_OFFSET = 0
            self.STEAM_ID_OFFSET = 0
            return

        def candidate_quality(c):
            (
                coords_offset,
                score,
                area_id,
                time_hour,
                time_min,
                time_sec,
                x,
                y,
                z,
                map_bytes,
                base_version,
            ) = c

            is_valid = area_id > 0 and base_version > 0
            is_corrupted = area_id == 0 and base_version == 0

            if is_valid:
                non_zero_count = sum(
                    [
                        1 if area_id > 0 else 0,
                        1 if time_hour > 0 or time_min > 0 or time_sec > 0 else 0,
                        1 if base_version > 0 else 0,
                    ]
                )
                return (1, score, non_zero_count)
            elif is_corrupted:
                coords_quality = 0

                if abs(y) > 10.0 and abs(y) < 2000.0:
                    coords_quality += 10

                if len(map_bytes) >= 4 and 0x0A <= map_bytes[3] <= 0x70:
                    coords_quality += 10

                if abs(x) > 1.0:
                    coords_quality += 5

                if abs(x - y) > 10.0 or abs(y - z) > 10.0:
                    coords_quality += 5

                if abs(x - round(x)) > 0.1 or abs(y - round(y)) > 0.1:
                    coords_quality += 3

                if abs(y) > 1500.0:
                    coords_quality -= 10

                if abs(x) == abs(y):
                    coords_quality -= 10

                if x == 128.0 or y == 128.0 or z == 128.0:
                    coords_quality -= 10

                return (2, -coords_quality, -score, coords_offset)
            else:
                return (3, score, 0)

        weather_candidates.sort(key=candidate_quality, reverse=False)
        coords_offset, *_rest = weather_candidates[0]

        player_coords_offset = coords_offset
        self.CSPLAYERCOORDS_OFFSET = player_coords_offset - self.data_start
        self.WORLD_AREA_WEATHER_OFFSET = self.CSPLAYERCOORDS_OFFSET + 0x20050
        self.WORLD_AREA_TIME_OFFSET = self.WORLD_AREA_WEATHER_OFFSET + 0xC
        self.STEAM_ID_OFFSET = self.WORLD_AREA_WEATHER_OFFSET + 0x28

    def _find_horse_data(self, start: int, end: int) -> int:
        """Find RideGameData by searching for distinctive Torrent patterns"""

        for offset in range(start, end - RideGameData.SIZE):
            if self.data[offset : offset + 12] != bytes(12):
                continue

            if self.data[offset + 12 : offset + 16] != bytes([0xFF, 0xFF, 0xFF, 0xFF]):
                continue

            if self.data[offset + 16 : offset + 32] != bytes(16):
                continue

            try:
                hp = struct.unpack("<I", self.data[offset + 32 : offset + 36])[0]
                state = struct.unpack("<I", self.data[offset + 36 : offset + 40])[0]

                if hp > 0 and hp < 5000 and state == 1:
                    return offset
            except Exception:
                continue

        for offset in range(start, end - RideGameData.SIZE):
            try:
                horse = RideGameData.from_bytes(self.data, offset)

                coords_not_zero = not (
                    abs(horse.coordinates.x) < 0.01
                    and abs(horse.coordinates.y) < 0.01
                    and abs(horse.coordinates.z) < 0.01
                )
                coords_reasonable = (
                    abs(horse.coordinates.x) < 10000
                    and abs(horse.coordinates.y) < 10000
                    and abs(horse.coordinates.z) < 10000
                )

                map_bytes = horse.map_id.to_bytes()
                valid_map = map_bytes != bytes([0, 0, 0, 0]) and map_bytes != bytes(
                    [0xFF, 0xFF, 0xFF, 0xFF]
                )

                valid_hp = 0 <= horse.hp < 5000
                valid_state = horse.state in [
                    HorseState.INACTIVE,
                    HorseState.DEAD,
                    HorseState.ACTIVE,
                ]

                significant_coords = (
                    abs(horse.coordinates.x) > 1.0
                    or abs(horse.coordinates.y) > 1.0
                    or abs(horse.coordinates.z) > 1.0
                )

                if (
                    coords_not_zero
                    and coords_reasonable
                    and valid_map
                    and valid_hp
                    and valid_state
                    and significant_coords
                ):
                    return offset

            except Exception:
                continue

        return 0

    def _find_player_coords(self, start: int, end: int) -> int:
        """Find CSPlayerCoords by looking for valid structure"""
        for offset in range(start, end - CSPlayerCoords.MIN_SIZE):
            try:
                coords = CSPlayerCoords.from_bytes(self.data, offset)

                map_bytes = coords.map_id.data
                if map_bytes == bytes([0, 0, 0, 0]) or map_bytes == bytes(
                    [0xFF, 0xFF, 0xFF, 0xFF]
                ):
                    continue

                if not (
                    abs(coords.coordinates.x) < 50000
                    and abs(coords.coordinates.y) < 50000
                    and abs(coords.coordinates.z) < 50000
                ):
                    continue

                if not (
                    abs(coords.angle.x) < 0.01
                    and abs(coords.angle.z) < 0.01
                    and abs(coords.angle.w) < 0.01
                    and abs(coords.angle.y) < 7.0
                ):
                    continue

                return offset

            except Exception:
                continue

        return 0

    def get_character_name(self) -> str | None:
        """Get character name from PlayerGameData at offset +0x94"""
        try:
            name_offset = self.player_data_offset + 0x94
            name_bytes = self.data[name_offset : name_offset + 32]
            name = name_bytes.decode("utf-16le", errors="ignore")

            if "\x00" in name:
                name = name.split("\x00")[0]

            name = name.strip()

            if (
                name
                and all(c.isprintable() or c.isspace() for c in name)
                and 1 <= len(name) <= 16
            ):
                return name

        except Exception:
            pass

        return None

    def get_slot_map_id(self) -> MapID | None:
        """Get the M MapID from the slot header"""
        try:
            map_id_offset = self.data_start + 0x4
            return MapID.from_bytes(self.data, map_id_offset)
        except Exception:
            return None

    def get_horse_data(self) -> RideGameData | None:
        """Get parsed RideGameData"""
        self._ensure_horse_data()
        if self.horse_offset > 0:
            try:
                horse = RideGameData.from_bytes(self.data, self.horse_offset)
                return horse
            except Exception:
                pass
        return None

    def write_horse_data(self, horse: RideGameData):
        """Write RideGameData back to save"""
        self._ensure_horse_data()
        if self.horse_offset > 0:
            horse_bytes = horse.to_bytes()
            self.data[self.horse_offset : self.horse_offset + len(horse_bytes)] = (
                horse_bytes
            )

    def get_player_coords(self) -> CSPlayerCoords | None:
        """Get parsed CSPlayerCoords"""
        self._ensure_player_coords()
        if self.player_coords_offset > 0:
            try:
                return CSPlayerCoords.from_bytes(self.data, self.player_coords_offset)
            except Exception:
                pass
        return None

    def write_player_coords(self, coords: CSPlayerCoords):
        """Write CSPlayerCoords back to save"""
        self._ensure_player_coords()
        if self.player_coords_offset > 0:
            coords_bytes = coords.to_bytes()
            self.data[
                self.player_coords_offset : self.player_coords_offset
                + len(coords_bytes)
            ] = coords_bytes

    def get_world_area_time(self) -> WorldAreaTime | None:
        """Get WorldAreaTime structure"""
        self._ensure_corruption_structures()
        if self.WORLD_AREA_TIME_OFFSET == 0:
            return None
        try:
            offset = self.data_start + self.WORLD_AREA_TIME_OFFSET
            return WorldAreaTime.from_bytes(self.data, offset)
        except Exception:
            return None

    def write_world_area_time(self, time: WorldAreaTime):
        """Write WorldAreaTime back to save"""
        self._ensure_corruption_structures()
        if self.WORLD_AREA_TIME_OFFSET == 0:
            return
        offset = self.data_start + self.WORLD_AREA_TIME_OFFSET
        time_bytes = time.to_bytes()
        self.data[offset : offset + len(time_bytes)] = time_bytes

    def get_world_area_weather(self) -> WorldAreaWeather | None:
        """Get WorldAreaWeather structure"""
        self._ensure_corruption_structures()
        if self.WORLD_AREA_WEATHER_OFFSET == 0:
            return None
        try:
            offset = self.data_start + self.WORLD_AREA_WEATHER_OFFSET
            return WorldAreaWeather.from_bytes(self.data, offset)
        except Exception:
            return None

    def write_world_area_weather(self, weather: WorldAreaWeather):
        """Write WorldAreaWeather back to save"""
        self._ensure_corruption_structures()
        if self.WORLD_AREA_WEATHER_OFFSET == 0:
            return
        offset = self.data_start + self.WORLD_AREA_WEATHER_OFFSET
        weather_bytes = weather.to_bytes()
        self.data[offset : offset + len(weather_bytes)] = weather_bytes

    def get_steam_id(self) -> int | None:
        """Get SteamId from character slot"""
        self._ensure_corruption_structures()
        if self.STEAM_ID_OFFSET == 0:
            return None
        try:
            offset = self.data_start + self.STEAM_ID_OFFSET
            return struct.unpack("<Q", self.data[offset : offset + 8])[0]
        except Exception:
            return None

    def write_steam_id(self, steam_id: int):
        """Write SteamId to character slot"""
        self._ensure_corruption_structures()
        if self.STEAM_ID_OFFSET == 0:
            return
        offset = self.data_start + self.STEAM_ID_OFFSET
        struct.pack_into("<Q", self.data, offset, steam_id)

    def has_corruption(self) -> tuple[bool, list[str]]:
        """Check if character has known corruption patterns"""
        self._ensure_corruption_structures()

        issues = []

        if self.WORLD_AREA_WEATHER_OFFSET == 0:
            return (False, [])

        steam_id = self.get_steam_id()
        if steam_id is not None and steam_id == 0:
            issues.append("SteamId is 0 (should be copied from USER_DATA_10)")

        time = self.get_world_area_time()
        if time and time.is_zero():
            issues.append("WorldAreaTime is 00:00:00 (should match SecondsPlayed)")

        weather = self.get_world_area_weather()
        if weather and weather.is_corrupted():
            issues.append(
                f"WorldAreaWeather AreaId is 0 (should be MapID[3]={self.map_id.data[3] if self.map_id else '?'})"
            )

        return (len(issues) > 0, issues)


class EldenRingSaveFile:
    """Main save file parser"""

    HEADER_SIZE = 0x300
    CHARACTER_FILE_SIZE = 0x280000
    CHECKSUM_SIZE = 0x10
    USERDATA_10_SIZE = 0x60000
    MAX_CHARACTER_COUNT = 10
    ACTIVE_SLOTS_OFFSET = 0x1901D04

    USERDATA_10_START = (
        HEADER_SIZE + (CHARACTER_FILE_SIZE + CHECKSUM_SIZE) * MAX_CHARACTER_COUNT
    )
    VERSION_OFFSET_USERDATA = 0x10
    STEAM_ID_OFFSET_USERDATA = 0x14
    PROFILE_SUMMARY_OFFSET = 0x1964

    def __init__(self, filepath: str):
        self.filepath = filepath

        with open(filepath, "rb") as f:
            self.data = bytearray(f.read())

        self.characters: list[CharacterSlot | None] = []
        for i in range(self.MAX_CHARACTER_COUNT):
            try:
                slot_offset = self.HEADER_SIZE + (
                    i * (self.CHARACTER_FILE_SIZE + self.CHECKSUM_SIZE)
                )
                data_start = slot_offset + self.CHECKSUM_SIZE

                version = struct.unpack("<I", self.data[data_start : data_start + 4])[0]
                if version == 0:
                    self.characters.append(None)
                    continue

                slot = CharacterSlot(self.data, i)
                self.characters.append(slot)

            except Exception:
                self.characters.append(None)

    def is_slot_active(self, slot_index: int) -> bool:
        """Check if character slot is active"""
        if 0 <= slot_index < self.MAX_CHARACTER_COUNT:
            return self.data[self.ACTIVE_SLOTS_OFFSET + slot_index] == 1
        return False

    def get_active_slots(self) -> list[int]:
        """Get list of active slot indices (slots with valid characters)"""
        active = []
        for i in range(self.MAX_CHARACTER_COUNT):
            if self.characters[i] is not None:
                active.append(i)
        return active

    def recalculate_checksums(self):
        """Recalculate MD5 checksums for all slots and USER_DATA_10"""
        import hashlib

        for slot_idx in self.get_active_slots():
            slot = self.characters[slot_idx]
            if slot:
                char_data = self.data[
                    slot.data_start : slot.data_start + self.CHARACTER_FILE_SIZE
                ]
                md5_hash = hashlib.md5(char_data).digest()
                self.data[
                    slot.checksum_offset : slot.checksum_offset + self.CHECKSUM_SIZE
                ] = md5_hash

        offset = self.HEADER_SIZE + (
            self.CHARACTER_FILE_SIZE * self.MAX_CHARACTER_COUNT
        )
        userdata_start = offset + self.CHECKSUM_SIZE
        userdata = self.data[userdata_start : userdata_start + self.USERDATA_10_SIZE]

        md5_hash = hashlib.md5(userdata).digest()
        self.data[offset : offset + self.CHECKSUM_SIZE] = md5_hash

    def save(self, filepath: str | None = None):
        """Save to disk"""
        if filepath is None:
            filepath = self.filepath

        with open(filepath, "wb") as f:
            f.write(self.data)
            f.flush()
            import os

            os.fsync(f.fileno())

    def get_userdata_steam_id(self) -> int | None:
        """Get SteamId from USER_DATA_10 (Common data)"""
        try:
            offset = self.USERDATA_10_START + self.STEAM_ID_OFFSET_USERDATA
            return struct.unpack("<Q", self.data[offset : offset + 8])[0]
        except Exception:
            return None

    def get_seconds_played(self, slot_index: int) -> int | None:
        """Get SecondsPlayed for a specific character from ProfileSummary"""
        try:
            profile_summary_start = self.USERDATA_10_START + self.PROFILE_SUMMARY_OFFSET
            profile_data_array_start = profile_summary_start + 10
            profile_data_size = 0x24C
            profile_data_start = profile_data_array_start + (
                slot_index * profile_data_size
            )
            seconds_offset = profile_data_start + 0x26
            value = struct.unpack("<i", self.data[seconds_offset : seconds_offset + 4])[
                0
            ]
            return value
        except Exception:
            return None

    def fix_character_corruption(self, slot_index: int) -> tuple[bool, list[str]]:
        """Fix known corruption patterns for a character slot"""
        if not (0 <= slot_index < self.MAX_CHARACTER_COUNT):
            return (False, ["Invalid slot index"])

        slot = self.characters[slot_index]
        if not slot:
            return (False, ["Slot is empty"])

        fixes_applied = []

        # Fix 1: SteamId
        slot_steam_id = slot.get_steam_id()
        userdata_steam_id = self.get_userdata_steam_id()

        if slot_steam_id == 0 and userdata_steam_id and userdata_steam_id != 0:
            slot.write_steam_id(userdata_steam_id)
            fixes_applied.append(f"SteamId: 0 -> {userdata_steam_id}")

        # Fix 2: WorldAreaTime
        time = slot.get_world_area_time()
        seconds_played = self.get_seconds_played(slot_index)

        if time and time.is_zero() and seconds_played and seconds_played > 0:
            new_time = WorldAreaTime.from_seconds(seconds_played)
            slot.write_world_area_time(new_time)
            fixes_applied.append(f"WorldAreaTime: 00:00:00 -> {new_time}")

        # Fix 3: WorldAreaWeather AreaId
        weather = slot.get_world_area_weather()

        if weather and weather.is_corrupted() and slot.map_id:
            area_id = slot.map_id.data[3]
            weather.area_id = area_id
            slot.write_world_area_weather(weather)
            fixes_applied.append(f"WorldAreaWeather AreaId: 0 -> {area_id}")

        # Fix 4: BaseVersion
        if slot.WORLD_AREA_WEATHER_OFFSET > 0:
            base_version_offset = (
                slot.data_start + slot.WORLD_AREA_WEATHER_OFFSET + 0x1C
            )
            current_base_version = struct.unpack(
                "<i", slot.data[base_version_offset : base_version_offset + 4]
            )[0]

            if current_base_version == 0:
                game_version = 150
                struct.pack_into("<i", slot.data, base_version_offset - 4, game_version)
                struct.pack_into("<i", slot.data, base_version_offset, game_version)
                struct.pack_into("<i", slot.data, base_version_offset + 4, 1)
                fixes_applied.append(f"BaseVersion: 0 -> {game_version}")

        return (len(fixes_applied) > 0, fixes_applied)
