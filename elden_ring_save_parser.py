"""
Elden Ring Save File Parser
Proper implementation that calculates actual offsets from the template structure
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
        
        search_start = self.data_start + 0x10000
        search_end = min(self.data_start + 0x50000, self.data_start + self.SLOT_SIZE)
        
        self.horse_offset = self._find_horse_data(search_start, search_end)
        
        if self.horse_offset > 0:
            search_start = self.horse_offset + 0x100000
        else:
            search_start = self.data_start + 0x1E0000 
        
        search_end = self.data_start + self.SLOT_SIZE - 100
        self.player_coords_offset = self._find_player_coords(search_start, search_end)
    
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
        if self.horse_offset > 0:
            try:
                horse = RideGameData.from_bytes(self.data, self.horse_offset)
                return horse 
            except:
                pass
        return None
    
    def write_horse_data(self, horse: RideGameData):
        """Write RideGameData back to save"""
        if self.horse_offset > 0:
            horse_bytes = horse.to_bytes()
            self.data[self.horse_offset:self.horse_offset + len(horse_bytes)] = horse_bytes
    
    def get_player_coords(self) -> Optional[CSPlayerCoords]:
        """Get parsed CSPlayerCoords"""
        if self.player_coords_offset > 0:
            try:
                return CSPlayerCoords.from_bytes(self.data, self.player_coords_offset)
            except:
                pass
        return None
    
    def write_player_coords(self, coords: CSPlayerCoords):
        """Write CSPlayerCoords back to save"""
        if self.player_coords_offset > 0:
            coords_bytes = coords.to_bytes()
            self.data[self.player_coords_offset:self.player_coords_offset + len(coords_bytes)] = coords_bytes

class EldenRingSaveFile:
    """Main save file parser"""
    
    HEADER_SIZE = 0x300
    CHARACTER_FILE_SIZE = 0x280000
    CHECKSUM_SIZE = 0x10
    USERDATA_10_SIZE = 0x60000
    MAX_CHARACTER_COUNT = 10
    ACTIVE_SLOTS_OFFSET = 0x1901D04
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        
        with open(filepath, 'rb') as f:
            self.data = bytearray(f.read())
        
        # Parse ALL character slots (not just marked active)
        # This fixes the 7/10 character detection issue
        self.characters: List[Optional[CharacterSlot]] = []
        for i in range(self.MAX_CHARACTER_COUNT):
            try:
                slot = CharacterSlot(self.data, i)
                # Check if slot has valid character name
                name = slot.get_character_name()
                if name and name.strip():
                    self.characters.append(slot)
                else:
                    self.characters.append(None)
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
        
        with open(filepath, 'wb') as f:
            f.write(self.data)
            f.flush()
            import os
            os.fsync(f.fileno())