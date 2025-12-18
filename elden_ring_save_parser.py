"""
Elden Ring Save File Parser
Implementation that calculates actual offsets from the template structure
"""

import struct
from dataclasses import dataclass
from typing import List, Optional, Tuple
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
        x, y, z = struct.unpack('<fff', data[offset:offset+12])
        return cls(x, y, z)
    
    def to_bytes(self) -> bytes:
        return struct.pack('<fff', self.x, self.y, self.z)
    
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
        x, y, z, w = struct.unpack('<ffff', data[offset:offset+16])
        return cls(x, y, z, w)
    
    def to_bytes(self) -> bytes:
        return struct.pack('<ffff', self.x, self.y, self.z, self.w)

@dataclass
class MapID:
    """Map identifier (4 bytes, displayed in reverse)"""
    data: bytes  # 4 bytes
    
    @classmethod
    def from_bytes(cls, data: bytes, offset: int):
        return cls(bytes(data[offset:offset+4]))
    
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
@dataclass
class WorldAreaTime:
    """World area time structure (CSWorldAreaTime) - 0xC bytes"""
    hour: int
    minute: int
    seconds: int
    
    SIZE = 0xC
    
    @classmethod
    def from_bytes(cls, data: bytes, offset: int):
        hour = struct.unpack('<I', data[offset:offset+4])[0]
        minute = struct.unpack('<I', data[offset+4:offset+8])[0]
        seconds = struct.unpack('<I', data[offset+8:offset+12])[0]
        return cls(hour, minute, seconds)
    
    def to_bytes(self) -> bytes:
        result = bytearray()
        result.extend(struct.pack('<I', self.hour))
        result.extend(struct.pack('<I', self.minute))
        result.extend(struct.pack('<I', self.seconds))
        return bytes(result)
    
    def is_zero(self) -> bool:
        """Check if time is 00:00:00 (corrupted)"""
        return self.hour == 0 and self.minute == 0 and self.seconds == 0
    
    def get_formatted(self) -> str:
        """Get formatted time as HH:MM:SS"""
        return f"{self.hour:02d}:{self.minute:02d}:{self.seconds:02d}"
    
    @classmethod
    def from_seconds(cls, total_seconds: int):
        """Create WorldAreaTime from total seconds played"""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return cls(hours, minutes, seconds)
    
    @classmethod
    def from_seconds(cls, total_seconds: int):
        """Create WorldAreaTime from total seconds"""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        return cls(hours, minutes, secs)
    
    def is_zero(self) -> bool:
        """Check if time is 00:00:00 (corrupted)"""
        return self.hour == 0 and self.minute == 0 and self.seconds == 0
    
    def __str__(self):
        return f"{self.hour:02d}:{self.minute:02d}:{self.seconds:02d}"

@dataclass
class WorldAreaWeather:
    """World area weather structure (CSWorldAreaWeather) - 0xC bytes"""
    area_id: int      # uint16
    weather_type: int # uint16 (enum)
    timer: int        # uint32
    
    SIZE = 0xC
    
    @classmethod
    def from_bytes(cls, data: bytes, offset: int):
        area_id = struct.unpack('<H', data[offset:offset+2])[0]
        weather_type = struct.unpack('<H', data[offset+2:offset+4])[0]
        timer = struct.unpack('<I', data[offset+4:offset+8])[0]
        return cls(area_id, weather_type, timer)
    
    def to_bytes(self) -> bytes:
        result = bytearray()
        result.extend(struct.pack('<H', self.area_id))
        result.extend(struct.pack('<H', self.weather_type))
        result.extend(struct.pack('<I', self.timer))
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
        hp = struct.unpack('<I', data[offset+32:offset+36])[0]
        state = HorseState(struct.unpack('<I', data[offset+36:offset+40])[0])
        return cls(coords, map_id, angle, hp, state)
    
    def to_bytes(self) -> bytes:
        result = bytearray()
        result.extend(self.coordinates.to_bytes())
        result.extend(self.map_id.to_bytes())
        result.extend(self.angle.to_bytes())
        result.extend(struct.pack('<I', self.hp))
        result.extend(struct.pack('<I', int(self.state)))
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
        
        self.slot_offset = self.HEADER_SIZE + (slot_index * (self.SLOT_SIZE + self.CHECKSUM_SIZE))
        self.checksum_offset = self.slot_offset
        self.data_start = self.slot_offset + self.CHECKSUM_SIZE
        
        self.version: Optional[int] = None
        self.map_id: Optional[MapID] = None
        self.gaitem_count: int = 0
        self.gaitem_map_end: int = 0
        self.player_data_offset: int = 0
        self.horse_offset: int = 0
        self.player_coords_offset: int = 0
        
        
        self._parse_structure()
        

    
    def _parse_structure(self):
        """Parse through the structure to find exact offsets"""
        offset = self.data_start
        
        self.version = struct.unpack('<I', self.data[offset:offset+4])[0]
        offset += 4
        
        self.map_id = MapID.from_bytes(self.data, offset)
        offset += 4
        
        offset += 0x18
        
        if self.version <= 81:
            self.gaitem_count = 0x13FE
        else:
            self.gaitem_count = 0x1400
        
        # Parse GaitemHandleMap to find player_data_offset (needed for get_character_name)
        for i in range(self.gaitem_count):
            gaitem_handle = struct.unpack('<I', self.data[offset:offset+4])[0]
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
            search_end = min(self.data_start + 0x50000, self.data_start + self.SLOT_SIZE)
            self.horse_offset = self._find_horse_data(search_start, search_end)
    
    def _ensure_player_coords(self):
        """Lazy load player coords on first access"""
        if self.player_coords_offset == 0:
            search_start = self.data_start + 0x1E0000
            search_end = self.data_start + 0x210000
            self.player_coords_offset = self._find_player_coords(search_start, search_end)
    
    def _ensure_corruption_structures(self):
        """
        Lazy loader for corruption structures.
        Only searches when first needed (has_corruption, get_weather, etc.)
        """
        if not self._corruption_structures_found and self.version and self.version > 0:
            self._find_corruption_structures()
            self._corruption_structures_found = True
    
    def _find_corruption_structures(self):
       
        """Search for corruption-related structures (WorldAreaWeather, WorldAreaTime, SteamID)"""
        char_name = self.get_character_name() or f"Slot {self.slot_index}"
        
        print(f"\n[DEBUG] Searching for corruption structures via Weather - {char_name}")
        
        # Search for weather in typical range (around 0x216000-0x21A000 from data_start)
        weather_search_start = self.data_start + 0x214000
        weather_search_end = self.data_start + 0x21C000
        
        weather_candidates = []
        
        print(f"  Searching for Weather structures...")
        
        # DEBUG: Check Character 1's exact offset if this is slot 1
        if self.slot_index == 1:
            test_offset = 0x496827
            print(f"\n  [DEBUG] Checking Character 1's known weather at 0x{test_offset:X}:")
            try:
                area_id_test = struct.unpack('<H', self.data[test_offset:test_offset+2])[0]
                weather_type_test = struct.unpack('<H', self.data[test_offset+2:test_offset+4])[0]
                timer_test = struct.unpack('<I', self.data[test_offset+4:test_offset+8])[0]
                time_h = struct.unpack('<I', self.data[test_offset+0xC:test_offset+0x10])[0]
                time_m = struct.unpack('<I', self.data[test_offset+0x10:test_offset+0x14])[0]
                time_s = struct.unpack('<I', self.data[test_offset+0x14:test_offset+0x18])[0]
                bv_copy = struct.unpack('<i', self.data[test_offset+0x18:test_offset+0x1C])[0]
                bv = struct.unpack('<i', self.data[test_offset+0x1C:test_offset+0x20])[0]
                bv_latest = struct.unpack('<i', self.data[test_offset+0x20:test_offset+0x24])[0]
                
                print(f"    AreaId={area_id_test}, WeatherType={weather_type_test}, Timer={timer_test}")
                print(f"    Time={time_h}:{time_m}:{time_s}")
                print(f"    BaseVersionCopy={bv_copy}, BaseVersion={bv}, IsLatest={bv_latest}")
                print(f"    Validations:")
                print(f"      area_id <= 255: {area_id_test <= 255}")
                print(f"      weather_type <= 100: {weather_type_test <= 100}")
                print(f"      timer <= 100000: {timer_test <= 100000}")
                print(f"      time valid: {time_h < 200 and time_m < 60 and time_s < 60}")
                print(f"      base_version 0-300: {0 <= bv <= 300}")
                print(f"      bv_copy == bv: {bv_copy == bv}")
                print(f"      bv_latest in [0,1]: {bv_latest in [0, 1]}")
                print(f"      not all_zero: {not (bv == 0 and time_h == 0 and time_m == 0 and time_s == 0)}")
            except Exception as e:
                print(f"    Error reading: {e}")
        
        
        candidates_checked = 0
        failed_reasons = {
            'area_id': 0,
            'weather_type': 0,
            'timer': 0,
            'time': 0,
            'base_version_range': 0,
            'base_version_mismatch': 0,
            'base_version_is_latest': 0,
            'all_zero': 0,
            'coords_bounds': 0,
            'mapid_invalid': 0,
            'mapid_range': 0
        }
        
        
        for offset in range(weather_search_start, weather_search_end, 1):  # Step=1 to catch all alignments!
            try:
                candidates_checked += 1
                
                # Read potential WorldAreaWeather
                area_id = struct.unpack('<H', self.data[offset:offset+2])[0]
                weather_type = struct.unpack('<H', self.data[offset+2:offset+4])[0]
                timer = struct.unpack('<I', self.data[offset+4:offset+8])[0]
                
                # Validate weather structure
                if area_id > 255:  # AreaId out of range
                    failed_reasons['area_id'] += 1
                    continue
                if weather_type > 100:  # WeatherType out of range
                    failed_reasons['weather_type'] += 1
                    continue
                if timer > 100000:  # Timer too large
                    failed_reasons['timer'] += 1
                    continue
                
                # Check time structure at +0xC
                time_hour = struct.unpack('<I', self.data[offset+0xC:offset+0x10])[0]
                time_min = struct.unpack('<I', self.data[offset+0x10:offset+0x14])[0]
                time_sec = struct.unpack('<I', self.data[offset+0x14:offset+0x18])[0]
                
                if not (time_hour < 200 and time_min < 60 and time_sec < 60):
                    failed_reasons['time'] += 1
                    continue
                
                # Check BaseVersion at +0x18
                # BaseVersion structure: BaseVersionCopy (int32) + BaseVersion (int32) + BaseVersionIsLatest (int32) + padding
                base_version_copy = struct.unpack('<i', self.data[offset+0x18:offset+0x1C])[0]
                base_version = struct.unpack('<i', self.data[offset+0x1C:offset+0x20])[0]
                base_version_is_latest = struct.unpack('<i', self.data[offset+0x20:offset+0x24])[0]
                
                if not (0 <= base_version <= 300):
                    failed_reasons['base_version_range'] += 1
                    continue
                
                # BaseVersionCopy should equal BaseVersion (they're synchronized)
                if base_version_copy != base_version:
                    failed_reasons['base_version_mismatch'] += 1
                    continue
                
                # BaseVersionIsLatest must be 0 or 1 (boolean stored as int32)
                if base_version_is_latest not in [0, 1]:
                    failed_reasons['base_version_is_latest'] += 1
                    continue
                
                # CRITICAL: Accept structures even if mostly zero, AS LONG AS coords are valid
                # For corrupted saves, weather might be all zeros but coords exist
                # Validating the weather structure separately in has_corruption()
                # Only skip if coords are clearly invalid (all zeros AND no steam ID later)
                pass  # Accept this candidate, even if weather data looks corrupted
                
                
                # Calculate where CSPlayerCoords should be
                coords_offset = offset - 0x20050
                
                # Verify the coords make sense
                x, y, z = struct.unpack('<fff', self.data[coords_offset:coords_offset+12])
                map_bytes = bytes(self.data[coords_offset+12:coords_offset+16])
                
                # Reject near-zero coords
                if abs(x) < 1.0 and abs(y) < 1.0:
                    failed_reasons['coords_bounds'] += 1
                    continue
                
                # Validate coordinates - normal bounds check
                if not (-10000 < x < 10000 and -5000 < y < 5000 and -10000 < z < 10000):
                    failed_reasons['coords_bounds'] += 1
                    continue
                if map_bytes == bytes([0,0,0,0]) or map_bytes == bytes([0xFF]*4):
                    failed_reasons['mapid_invalid'] += 1
                    continue
                if not (0x0A <= map_bytes[3] <= 0x70):
                    failed_reasons['mapid_range'] += 1
                    continue
                
                # Calculate score
                score = 0
                if area_id > 0:
                    score += 10
                if time_hour > 0 or time_min > 0 or time_sec > 0:
                    score += 5
                if 50 <= base_version <= 100:
                    score += 15
                elif 0 < base_version < 300:
                    score += 5
                
                # For corrupted saves (all zeros), give minimal score of 1
                # so they're still found and can be fixed
                if score == 0:
                    score = 1
                
                weather_candidates.append((coords_offset, score, area_id, time_hour, time_min, time_sec, x, y, z, map_bytes, base_version))
                
            except:
                continue
        
        if not weather_candidates:
            print(f"  ✗ No valid Weather structures found")
            print(f"    Checked {candidates_checked} candidates")
            print(f"    Failed validations:")
            for reason, count in failed_reasons.items():
                if count > 0:
                    print(f"      {reason}: {count}")
            self.WORLD_AREA_WEATHER_OFFSET = 0
            self.WORLD_AREA_TIME_OFFSET = 0
            self.STEAM_ID_OFFSET = 0
            return
        
        # Pick best candidate
        # Strategy: Categorize first, then sort by score within category
        # Categories (highest to lowest priority):
        # 1. Valid = AreaId>0 AND BaseVersion>0 
        # 2. Corrupted = AreaId=0 AND BaseVersion=0 
        # 3. Garbage = other combinations 
        
        
        # DEBUG: Show all Category 2 (corrupted) candidates with their quality scores
        if self.slot_index == 4:
            print(f"\n  [DEBUG] All corrupted candidates (Category 2):")
            corrupted_candidates = []
            for c in weather_candidates:
                coords_offset, score, area_id, time_hour, time_min, time_sec, x, y, z, map_bytes, base_version = c
                is_corrupted = (area_id == 0 and base_version == 0)
                if is_corrupted:
                    # Calculate quality (same as candidate_quality function)
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
                    
                    corrupted_candidates.append((coords_offset, coords_quality, score, x, y, z, map_bytes.hex()))
            
            # Show top 5
            for i, (offset, quality, score, x, y, z, map_hex) in enumerate(sorted(corrupted_candidates, key=lambda c: (-c[1], -c[2], c[0]))[:5]):
                is_csv = (offset == 0xBFA11C)
                print(f"    {i+1}. Offset: 0x{offset:X}, Quality: {quality}, Score: {score}")
                print(f"       Coords: ({x:.1f}, {y:.1f}, {z:.1f}), MapID: {map_hex} {'<-- CSV!' if is_csv else ''}")
        
        def candidate_quality(c):
            coords_offset, score, area_id, time_hour, time_min, time_sec, x, y, z, map_bytes, base_version = c
            
            is_valid = (area_id > 0 and base_version > 0)
            is_corrupted = (area_id == 0 and base_version == 0)
            
            if is_valid:
                # Category 1: Valid structures (highest priority)
                non_zero_count = sum([
                    1 if area_id > 0 else 0,
                    1 if time_hour > 0 or time_min > 0 or time_sec > 0 else 0,
                    1 if base_version > 0 else 0
                ])
                return (1, score, non_zero_count)  # Category 1 first
            elif is_corrupted:
                
                coords_quality = 0
                
                
                if abs(y) > 10.0 and abs(y) < 2000.0:
                    coords_quality += 10
                
                # MapID should have valid prefix byte (0x0A-0x70 range)
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
                
                if x == 128.0 or y == 128.0 or z == 128.0:  # Common garbage value
                    coords_quality -= 10
                
                # Use offset as final tiebreaker for stable sorting
                return (2, -coords_quality, -score, coords_offset)  # Earlier offsets preferred when tied
            else:
                # Category 3: Garbage (lowest priority)
                return (3, score, 0)  # Category 3 first
        
        weather_candidates.sort(key=candidate_quality, reverse=False)  # ASCENDING: lower category = better
        coords_offset, score, area_id, time_hour, time_min, time_sec, x, y, z, map_bytes, base_version = weather_candidates[0]
        
        print(f"  ✓ CSPlayerCoords found via Weather at 0x{coords_offset:X} (rel: 0x{coords_offset - self.data_start:X})")
        print(f"    Coords: ({x:.1f}, {y:.1f}, {z:.1f})")
        print(f"    MapID: {map_bytes.hex()}")
        print(f"    Score: {score} (found {len(weather_candidates)} candidates)")
        
        # Set offsets
        player_coords_offset = coords_offset
        self.CSPLAYERCOORDS_OFFSET = player_coords_offset - self.data_start
        self.WORLD_AREA_WEATHER_OFFSET = self.CSPLAYERCOORDS_OFFSET + 0x20050
        self.WORLD_AREA_TIME_OFFSET = self.WORLD_AREA_WEATHER_OFFSET + 0xC
        self.STEAM_ID_OFFSET = self.WORLD_AREA_WEATHER_OFFSET + 0x28
        
        # Show final data
        weather_abs = player_coords_offset + 0x20050
        steamid_abs = weather_abs + 0x28
        
        steamid = struct.unpack('<Q', self.data[steamid_abs:steamid_abs+8])[0]
        
        print(f"  ✓ Corruption structures at +0x20050:")
        print(f"    Weather: 0x{weather_abs:X} (rel: 0x{self.WORLD_AREA_WEATHER_OFFSET:X})")
        print(f"    AreaId: {area_id}, Time: {time_hour:02d}:{time_min:02d}:{time_sec:02d}")
        print(f"    BaseVersion: {base_version}, SteamId: {steamid}")
    
    def _find_horse_data(self, start: int, end: int) -> int:
        """Find RideGameData by searching for distinctive Torrent patterns"""
        
        for offset in range(start, end - RideGameData.SIZE):
            if self.data[offset:offset+12] != bytes(12):
                continue
            
            if self.data[offset+12:offset+16] != bytes([0xFF, 0xFF, 0xFF, 0xFF]):
                continue
            
            if self.data[offset+16:offset+32] != bytes(16):
                continue
            
            try:
                hp = struct.unpack('<I', self.data[offset+32:offset+36])[0]
                state = struct.unpack('<I', self.data[offset+36:offset+40])[0]
                
                if hp > 0 and hp < 5000 and state == 1:
                    return offset
            except:
                continue
        
        for offset in range(start, end - RideGameData.SIZE):
            try:
                horse = RideGameData.from_bytes(self.data, offset)
                
                coords_not_zero = not (abs(horse.coordinates.x) < 0.01 and 
                                      abs(horse.coordinates.y) < 0.01 and 
                                      abs(horse.coordinates.z) < 0.01)
                coords_reasonable = (abs(horse.coordinates.x) < 10000 and
                                   abs(horse.coordinates.y) < 10000 and
                                   abs(horse.coordinates.z) < 10000)
                
                map_bytes = horse.map_id.to_bytes()
                valid_map = (map_bytes != bytes([0, 0, 0, 0]) and 
                           map_bytes != bytes([0xFF, 0xFF, 0xFF, 0xFF]))
                
                valid_hp = 0 <= horse.hp < 5000
                valid_state = horse.state in [HorseState.INACTIVE, HorseState.DEAD, HorseState.ACTIVE]
                
                significant_coords = (abs(horse.coordinates.x) > 1.0 or
                                    abs(horse.coordinates.y) > 1.0 or
                                    abs(horse.coordinates.z) > 1.0)
                
                if coords_not_zero and coords_reasonable and valid_map and valid_hp and valid_state and significant_coords:
                    return offset
                    
            except:
                continue
        
        return 0
    
    def _find_player_coords(self, start: int, end: int) -> int:
        """Find CSPlayerCoords by looking for valid structure"""
        for offset in range(start, end - CSPlayerCoords.MIN_SIZE):
            try:
                coords = CSPlayerCoords.from_bytes(self.data, offset)
                
                map_bytes = coords.map_id.data
                if map_bytes == bytes([0, 0, 0, 0]) or map_bytes == bytes([0xFF, 0xFF, 0xFF, 0xFF]):
                    continue
                
                if not (abs(coords.coordinates.x) < 50000 and
                        abs(coords.coordinates.y) < 50000 and
                        abs(coords.coordinates.z) < 50000):
                    continue
                
                if not (abs(coords.angle.x) < 0.01 and
                        abs(coords.angle.z) < 0.01 and
                        abs(coords.angle.w) < 0.01 and
                        abs(coords.angle.y) < 7.0):
                    continue
                
                return offset
                
            except:
                continue
        
        return 0 
    
    def get_character_name(self) -> Optional[str]:
        """Get character name from PlayerGameData at offset +0x94"""
        try:
            name_offset = self.player_data_offset + 0x94
            name_bytes = self.data[name_offset:name_offset + 32]
            name = name_bytes.decode('utf-16le', errors='ignore')
            
            if '\x00' in name:
                name = name.split('\x00')[0]
            
            name = name.strip()
            
            if name and all(c.isprintable() or c.isspace() for c in name) and 1 <= len(name) <= 16:
                return name
            
        except Exception as e:
            pass
        
        return None
    
    def get_slot_map_id(self) -> Optional[MapID]:
        """Get the M MapID from the slot header"""
        try:
            map_id_offset = self.data_start + 0x4
            return MapID.from_bytes(self.data, map_id_offset)
        except:
            return None
    
    def get_horse_data(self) -> Optional[RideGameData]:
        """Get parsed RideGameData"""
        self._ensure_horse_data()  # Lazy load
        if self.horse_offset > 0:
            try:
                horse = RideGameData.from_bytes(self.data, self.horse_offset)
                return horse 
            except:
                pass
        return None
    
    def write_horse_data(self, horse: RideGameData):
        """Write RideGameData back to save"""
        self._ensure_horse_data()  # Lazy load
        if self.horse_offset > 0:
            horse_bytes = horse.to_bytes()
            self.data[self.horse_offset:self.horse_offset + len(horse_bytes)] = horse_bytes
    
    def get_player_coords(self) -> Optional[CSPlayerCoords]:
        """Get parsed CSPlayerCoords"""
        self._ensure_player_coords()  # Lazy load
        if self.player_coords_offset > 0:
            try:
                return CSPlayerCoords.from_bytes(self.data, self.player_coords_offset)
            except:
                pass
        return None
    
    def write_player_coords(self, coords: CSPlayerCoords):
        """Write CSPlayerCoords back to save"""
        self._ensure_player_coords()  # Lazy load
        if self.player_coords_offset > 0:
            coords_bytes = coords.to_bytes()
            self.data[self.player_coords_offset:self.player_coords_offset + len(coords_bytes)] = coords_bytes
    
    def get_world_area_time(self) -> Optional[WorldAreaTime]:
        """Get WorldAreaTime structure"""
        self._ensure_corruption_structures()  # Lazy load
        if self.WORLD_AREA_TIME_OFFSET == 0:
            return None
        try:
            offset = self.data_start + self.WORLD_AREA_TIME_OFFSET
            return WorldAreaTime.from_bytes(self.data, offset)
        except:
            return None
    
    def write_world_area_time(self, time: WorldAreaTime):
        """Write WorldAreaTime back to save"""
        self._ensure_corruption_structures()  # Lazy load
        if self.WORLD_AREA_TIME_OFFSET == 0:
            return
        offset = self.data_start + self.WORLD_AREA_TIME_OFFSET
        time_bytes = time.to_bytes()
        self.data[offset:offset + len(time_bytes)] = time_bytes
    
    def get_world_area_weather(self) -> Optional[WorldAreaWeather]:
        """Get WorldAreaWeather structure"""
        self._ensure_corruption_structures()  # Lazy load
        if self.WORLD_AREA_WEATHER_OFFSET == 0:
            return None
        try:
            offset = self.data_start + self.WORLD_AREA_WEATHER_OFFSET
            return WorldAreaWeather.from_bytes(self.data, offset)
        except:
            return None
    
    def write_world_area_weather(self, weather: WorldAreaWeather):
        """Write WorldAreaWeather back to save"""
        self._ensure_corruption_structures()  # Lazy load
        if self.WORLD_AREA_WEATHER_OFFSET == 0:
            return
        offset = self.data_start + self.WORLD_AREA_WEATHER_OFFSET
        weather_bytes = weather.to_bytes()
        self.data[offset:offset + len(weather_bytes)] = weather_bytes
    
    def get_steam_id(self) -> Optional[int]:
        """Get SteamId from character slot"""
        self._ensure_corruption_structures()  # Lazy load
        if self.STEAM_ID_OFFSET == 0:
            return None
        try:
            offset = self.data_start + self.STEAM_ID_OFFSET
            return struct.unpack('<Q', self.data[offset:offset+8])[0]
        except:
            return None
    
    def write_steam_id(self, steam_id: int):
        """Write SteamId to character slot"""
        self._ensure_corruption_structures()  # Lazy load
        if self.STEAM_ID_OFFSET == 0:
            return
        offset = self.data_start + self.STEAM_ID_OFFSET
        struct.pack_into('<Q', self.data, offset, steam_id)
    
    def get_seconds_played(self) -> Optional[int]:
        """Get SecondsPlayed from ProfileSummary for this character slot"""
        return None
    
    
    def fix_corruption(self) -> bool:
        """
        Fix corrupted WorldAreaWeather, WorldAreaTime, and SteamId structures.
        
        Returns:
            True if corruption was fixed, False if no corruption found or fix failed
        """
        has_issues, issues = self.has_corruption()
        if not has_issues:
            return False
        
        print(f"\n[FIX] Fixing corruption for character {self.slot_index + 1}...")
        
        try:
            # 1. Get SteamId from USER_DATA10 Common
            # USER_DATA10 is at: HEADER + (10 * SLOT_SIZE) + (10 * CHECKSUM)
            HEADER = 0x300
            SLOT_SIZE = 0x280000
            CHECKSUM = 0x10
            
            user_data10_offset = HEADER + (10 * (SLOT_SIZE + CHECKSUM))
            userdata_start = user_data10_offset + CHECKSUM
            
            # SteamId is at userdata_start + 0x4 (after Version uint32)
            steam_id = struct.unpack('<Q', self.data[userdata_start + 0x4:userdata_start + 0xC])[0]
            print(f"  → SteamId from USER_DATA10: {steam_id}")
            
            # 2. Get SecondsPlayed from CSProfileSummary
            # ProfileSummary is at userdata_start + 0x154 (after Settings, MenuSystemSaveLoad)
            # Each ProfileData is 0x2A0 bytes
            # SecondsPlayed is at ProfileData + 0x24
            
            profile_summary_offset = userdata_start + 0x154
            # Skip 10-byte active slots array
            profile_data_start = profile_summary_offset + 0xA
            
            # Get this character's profile
            profile_offset = profile_data_start + (self.slot_index * 0x2A0)
            seconds_played = struct.unpack('<i', self.data[profile_offset + 0x24:profile_offset + 0x28])[0]
            
            # Convert to hours:minutes:seconds
            hours = seconds_played // 3600
            minutes = (seconds_played % 3600) // 60
            seconds = seconds_played % 60
            
            print(f"  → Playtime: {hours}h {minutes}m {seconds}s ({seconds_played} total seconds)")
            
            # 3. Get AreaId from slot MapID
            # Slot MapID is at data_start + 0x4
            slot_mapid = self.data[self.data_start + 0x4:self.data_start + 0x8]
            area_id = slot_mapid[0]  # byte[0] of MapID (as per 010 template M MapID[3])
            
            print(f"  → AreaId from slot MapID byte[0]: {area_id}")
            
            # 4. Apply fixes
            if self.WORLD_AREA_WEATHER_OFFSET > 0:
                # Fix WorldAreaWeather AreaId
                weather_offset = self.data_start + self.WORLD_AREA_WEATHER_OFFSET
                struct.pack_into('<H', self.data, weather_offset, area_id)
                print(f"  ✓ Fixed WorldAreaWeather AreaId: {area_id}")
                
                # Fix WorldAreaTime
                time_offset = self.data_start + self.WORLD_AREA_TIME_OFFSET
                struct.pack_into('<I', self.data, time_offset, hours)
                struct.pack_into('<I', self.data, time_offset + 4, minutes)
                struct.pack_into('<I', self.data, time_offset + 8, seconds)
                print(f"  ✓ Fixed WorldAreaTime: {hours:02d}:{minutes:02d}:{seconds:02d}")
                
                # Fix SteamId
                steamid_offset = self.data_start + self.STEAM_ID_OFFSET
                struct.pack_into('<Q', self.data, steamid_offset, steam_id)
                print(f"  ✓ Fixed SteamId: {steam_id}")
                
                return True
            else:
                print(f"  ✗ Cannot fix: corruption structures not located")
                return False
                
        except Exception as e:
            print(f"  ✗ Fix failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def has_corruption(self) -> Tuple[bool, List[str]]:
        """
        Check if character has known corruption patterns.
        
        Returns:
            (has_corruption, list_of_issues)
        """
        # Lazy load corruption structures on first check
        self._ensure_corruption_structures()
        
        issues = []
        
        # Skip check if corruption structures weren't found
        if self.WORLD_AREA_WEATHER_OFFSET == 0:
            print(f"  [has_corruption] Structures not found, skipping")
            return (False, [])
        
        # Check SteamId
        steam_id = self.get_steam_id()
        print(f"  [has_corruption] SteamId: {steam_id}")
        if steam_id is not None and steam_id == 0:
            issues.append("SteamId is 0 (should be copied from USER_DATA_10)")
        
        # Check WorldAreaTime
        time = self.get_world_area_time()
        if time:
            print(f"  [has_corruption] Time: {time.get_formatted()}, is_zero: {time.is_zero()}")
            if time.is_zero():
                issues.append("WorldAreaTime is 00:00:00 (should match SecondsPlayed)")
        
        # Check WorldAreaWeather
        weather = self.get_world_area_weather()
        if weather:
            print(f"  [has_corruption] AreaId: {weather.area_id}, is_corrupted: {weather.is_corrupted()}")
            if weather.is_corrupted():
                issues.append(f"WorldAreaWeather AreaId is 0 (should be MapID[3]={self.map_id.data[3] if self.map_id else '?'})")
        
        print(f"  [has_corruption] Total issues: {len(issues)}")
        return (len(issues) > 0, issues)

class EldenRingSaveFile:
    """Main save file parser"""
    
    HEADER_SIZE = 0x300
    CHARACTER_FILE_SIZE = 0x280000
    CHECKSUM_SIZE = 0x10
    USERDATA_10_SIZE = 0x60000
    MAX_CHARACTER_COUNT = 10
    ACTIVE_SLOTS_OFFSET = 0x1901D04
    
    # USER_DATA_10 offsets
    # Structure: HEADER (0x300) + [Slot0-9 with checksums] + USER_DATA10
    # Each character slot is 0x280010 bytes (0x10 checksum + 0x280000 data)
    # 10 slots = 0x300 + (0x280010 * 10) = 0x19003A0
    # USER_DATA10 struct starts at 0x19003A0 (from CSV)
    # The struct INCLUDES its checksum as the first 0x10 bytes
    USERDATA_10_START = HEADER_SIZE + (CHARACTER_FILE_SIZE + CHECKSUM_SIZE) * MAX_CHARACTER_COUNT
    # = 0x300 + (0x280000 + 0x10) * 10 = 0x19003A0 ✓
    
    # Offsets within USER_DATA_10 structure (relative to 0x19003A0)
    # Note: First 0x10 bytes are the checksum, so actual data starts at +0x10
    VERSION_OFFSET_USERDATA = 0x10  # Version at 0x19003B0 (0x19003A0 + 0x10)
    STEAM_ID_OFFSET_USERDATA = 0x14  # SteamId at 0x19003B4 (0x19003A0 + 0x14)
    PROFILE_SUMMARY_OFFSET = 0x1964  # ProfileSummary at 0x1901D04 (0x19003A0 + 0x1964)
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        
        with open(filepath, 'rb') as f:
            self.data = bytearray(f.read())
        
        self.characters: List[Optional[CharacterSlot]] = []
        for i in range(self.MAX_CHARACTER_COUNT):
            try:
                # OPTIMIZATION: Only skip completely empty slots (Version=0)
                # Other validity checks happen after CharacterSlot creation
                slot_offset = self.HEADER_SIZE + (i * (self.CHARACTER_FILE_SIZE + self.CHECKSUM_SIZE))
                data_start = slot_offset + self.CHECKSUM_SIZE
                
                # Quick check: Version=0 means slot is completely empty
                version = struct.unpack('<I', self.data[data_start:data_start+4])[0]
                if version == 0:
                    self.characters.append(None)
                    continue
                
                # Create CharacterSlot
                slot = CharacterSlot(self.data, i)
                
                name = slot.get_character_name()
                if name and name.strip():
                    self.characters.append(slot)
                else:
                    # No valid name - but keep it anyway to avoid filtering valid characters
                    # The GUI will filter based on is_slot_active() check
                    self.characters.append(slot)
                
            except Exception as e:
                self.characters.append(None)
    
    def is_slot_active(self, slot_index: int) -> bool:
        """Check if character slot is active"""
        if 0 <= slot_index < self.MAX_CHARACTER_COUNT:
            return self.data[self.ACTIVE_SLOTS_OFFSET + slot_index] == 1
        return False
    
    def get_active_slots(self) -> List[int]:
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
                char_data = self.data[slot.data_start:slot.data_start + self.CHARACTER_FILE_SIZE]
                md5_hash = hashlib.md5(char_data).digest()
                self.data[slot.checksum_offset:slot.checksum_offset + self.CHECKSUM_SIZE] = md5_hash
        
        offset = self.HEADER_SIZE + (self.CHARACTER_FILE_SIZE * self.MAX_CHARACTER_COUNT)
        userdata_start = offset + self.CHECKSUM_SIZE
        userdata = self.data[userdata_start:userdata_start + self.USERDATA_10_SIZE]
        
        md5_hash = hashlib.md5(userdata).digest()
        self.data[offset:offset + self.CHECKSUM_SIZE] = md5_hash
    
    def save(self, filepath: Optional[str] = None):
        """Save to disk"""
        if filepath is None:
            filepath = self.filepath
        
        print(f"\n[SAVE] Writing to {filepath}...")
        with open(filepath, 'wb') as f:
            f.write(self.data)
            f.flush()
            import os
            os.fsync(f.fileno())
        print(f"[SAVE] File written successfully ({len(self.data)} bytes)")
    
    def get_userdata_steam_id(self) -> Optional[int]:
        """Get SteamId from USER_DATA_10 (Common data)"""
        try:
            offset = self.USERDATA_10_START + self.STEAM_ID_OFFSET_USERDATA
            return struct.unpack('<Q', self.data[offset:offset+8])[0]
        except:
            return None
    
    def get_seconds_played(self, slot_index: int) -> Optional[int]:
        """
        Get SecondsPlayed for a specific character from ProfileSummary.
        
        ProfileSummary structure:
        - At offset 0x1964 from USER_DATA10 start (absolute: 0x1901D04)
        - SlotState[10] (10 bytes) - which slots are active
        - ProfileData[10] - array of profile structs
        
        Each ProfileData structure:
        - CharacterName (0x20 bytes)
        - Level (4 bytes) at +0x22
        - SecondsPlayed (4 bytes) at +0x26
        - Size per profile: 0x24C bytes
        
        SecondsPlayed is at ProfileData[slot_index] + 0x26
        """
        try:
            # ProfileSummary starts at this offset
            profile_summary_start = self.USERDATA_10_START + self.PROFILE_SUMMARY_OFFSET
            
            print(f"DEBUG get_seconds_played:")
            print(f"  slot_index: {slot_index}")
            print(f"  USERDATA_10_START: 0x{self.USERDATA_10_START:X}")
            print(f"  PROFILE_SUMMARY_OFFSET: 0x{self.PROFILE_SUMMARY_OFFSET:X}")
            print(f"  profile_summary_start: 0x{profile_summary_start:X}")
            
            # Skip SlotState array (10 bytes)
            profile_data_array_start = profile_summary_start + 10
            print(f"  profile_data_array_start: 0x{profile_data_array_start:X}")
            
            # Each ProfileData is 0x24C bytes
            profile_data_size = 0x24C
            
            # Get this slot's ProfileData
            profile_data_start = profile_data_array_start + (slot_index * profile_data_size)
            print(f"  profile_data_start (slot {slot_index}): 0x{profile_data_start:X}")
            
            # SecondsPlayed is at +0x26 within ProfileData
            seconds_offset = profile_data_start + 0x26
            print(f"  seconds_offset: 0x{seconds_offset:X}")
            
            # Read the value
            value = struct.unpack('<i', self.data[seconds_offset:seconds_offset+4])[0]
            print(f"  SecondsPlayed value: {value}")
            
            return value
        except Exception as e:
            print(f"ERROR reading SecondsPlayed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def fix_character_corruption(self, slot_index: int) -> Tuple[bool, List[str]]:
        """
        Fix known corruption patterns for a character slot.
        
        Returns:
            (was_fixed, list_of_fixes_applied)
        """
        if not (0 <= slot_index < self.MAX_CHARACTER_COUNT):
            return (False, ["Invalid slot index"])
        
        slot = self.characters[slot_index]
        if not slot:
            return (False, ["Slot is empty"])
        
        fixes_applied = []
        
        print(f"\n[FIX] Starting fix for slot {slot_index}")
        print(f"[FIX] Detected offsets:")
        print(f"  player_coords_offset: 0x{slot.player_coords_offset:X}")
        print(f"  WORLD_AREA_WEATHER_OFFSET: 0x{slot.WORLD_AREA_WEATHER_OFFSET:X}")
        print(f"  WORLD_AREA_TIME_OFFSET: 0x{slot.WORLD_AREA_TIME_OFFSET:X}")
        print(f"  Absolute weather offset: 0x{slot.data_start + slot.WORLD_AREA_WEATHER_OFFSET:X}")
        print(f"  Absolute time offset: 0x{slot.data_start + slot.WORLD_AREA_TIME_OFFSET:X}")
        
        # Fix 1: SteamId (copy from USER_DATA_10)
        slot_steam_id = slot.get_steam_id()
        userdata_steam_id = self.get_userdata_steam_id()
        
        print(f"\n[FIX] SteamId check:")
        print(f"  Slot SteamId: {slot_steam_id}")
        print(f"  USER_DATA SteamId: {userdata_steam_id}")
        
        if slot_steam_id == 0 and userdata_steam_id and userdata_steam_id != 0:
            print(f"  → Applying fix: 0 -> {userdata_steam_id}")
            slot.write_steam_id(userdata_steam_id)
            fixes_applied.append(f"SteamId: 0 -> {userdata_steam_id}")
            
            # Verify write
            new_steam_id = slot.get_steam_id()
            print(f"  ✓ Verified: SteamId is now {new_steam_id}")
        else:
            print(f"  → No fix needed")
        
        # Fix 2: WorldAreaTime (calculate from SecondsPlayed)
        time = slot.get_world_area_time()
        seconds_played = self.get_seconds_played(slot_index)
        
        print(f"\n[FIX] WorldAreaTime check:")
        print(f"  Current time: {time}")
        print(f"  SecondsPlayed: {seconds_played}")
        
        if time and time.is_zero():
            if seconds_played and seconds_played > 0:
                new_time = WorldAreaTime.from_seconds(seconds_played)
                print(f"  → Applying fix: 00:00:00 -> {new_time}")
                print(f"  → Writing to offset: 0x{slot.data_start + slot.WORLD_AREA_TIME_OFFSET:X}")
                slot.write_world_area_time(new_time)
                fixes_applied.append(f"WorldAreaTime: 00:00:00 -> {new_time}")
                
                # Verify write
                new_time_read = slot.get_world_area_time()
                print(f"  ✓ Verified: Time is now {new_time_read}")
        else:
            print(f"  → No fix needed (time is not zero or no seconds played)")
        
        # Fix 3: WorldAreaWeather AreaId (copy from MapID[3])
        weather = slot.get_world_area_weather()
        
        print(f"\n[FIX] WorldAreaWeather check:")
        print(f"  Current weather: {weather}")
        print(f"  MapID: {slot.map_id}")
        print(f"  MapID bytes: {slot.map_id.data.hex() if slot.map_id else 'None'}")
        
        if weather and weather.is_corrupted() and slot.map_id:
            # AreaId should be MapID byte[3] (in decimal)
            area_id = slot.map_id.data[3]
            print(f"  → Applying fix: AreaId 0 -> {area_id}")
            print(f"  → Writing to offset: 0x{slot.data_start + slot.WORLD_AREA_WEATHER_OFFSET:X}")
            weather.area_id = area_id
            slot.write_world_area_weather(weather)
            fixes_applied.append(f"WorldAreaWeather AreaId: 0 -> {area_id}")
            
            # Verify write
            new_weather = slot.get_world_area_weather()
            print(f"  ✓ Verified: Weather is now {new_weather}")
        else:
            print(f"  → No fix needed")
            if weather:
                print(f"     is_corrupted: {weather.is_corrupted()}")
            if not slot.map_id:
                print(f"     MapID is None!")
        
        # Fix 4: BaseVersion (set to current game version if 0)
        # BaseVersion is at Weather offset + 0x18 (BaseVersionCopy), +0x1C (BaseVersion), +0x20 (IsLatest)
        base_version_offset = slot.data_start + slot.WORLD_AREA_WEATHER_OFFSET + 0x1C
        current_base_version = struct.unpack('<i', slot.data[base_version_offset:base_version_offset+4])[0]
        
        print(f"\n[FIX] BaseVersion check:")
        print(f"  Current BaseVersion: {current_base_version}")
        
        if current_base_version == 0:
            game_version = 150
            print(f"  → Applying fix: BaseVersion 0 -> {game_version}")
            print(f"  → Writing to offset: 0x{base_version_offset:X}")
            
            # Write BaseVersionCopy at +0x18
            struct.pack_into('<i', slot.data, base_version_offset - 4, game_version)
            # Write BaseVersion at +0x1C
            struct.pack_into('<i', slot.data, base_version_offset, game_version)
            # Write BaseVersionIsLatest at +0x20 (set to 1 = True)
            struct.pack_into('<i', slot.data, base_version_offset + 4, 1)
            
            fixes_applied.append(f"BaseVersion: 0 -> {game_version}")
            
            # Verify write
            new_base_version = struct.unpack('<i', slot.data[base_version_offset:base_version_offset+4])[0]
            print(f"  ✓ Verified: BaseVersion is now {new_base_version}")
        else:
            print(f"  → No fix needed (BaseVersion={current_base_version})")
        
        print(f"\n[FIX] Complete. Fixes applied: {len(fixes_applied)}")
        for fix in fixes_applied:
            print(f"  - {fix}")
        
        return (len(fixes_applied) > 0, fixes_applied)