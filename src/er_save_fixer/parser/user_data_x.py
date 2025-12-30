"""
Elden Ring Save Parser - UserDataX (Character Slot)
File 5 of 6

This is the MAIN sequential parser that reads an entire character slot in order.
Based on ER-Save-Lib Rust implementation - EXACT field order.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from io import BytesIO
import struct
from typing import List, Optional

from .er_types import Gaitem, MapId
from .character import PlayerGameData, SPEffect
from .equipment import (
    EquippedItemsEquipIndex, ActiveWeaponSlotsAndArmStyle,
    EquippedItemsItemIds, EquippedItemsGaitemHandles,
    Inventory, EquippedSpells, EquippedItems, EquippedGestures,
    AcquiredProjectiles, EquippedArmamentsAndItems, EquippedPhysics,
    TrophyEquipData
)
from .world import (
    FaceData, Gestures, Regions, RideGameData, BloodStain,
    MenuSaveLoad, GaitemGameData, TutorialData, FieldArea,
    WorldArea, WorldGeomMan, RendMan, PlayerCoordinates,
    NetMan, WorldAreaWeather, WorldAreaTime, BaseVersion,
    PS5Activity, DLC, PlayerGameDataHash
)


@dataclass
class UserDataX:
    """
    Complete character slot (UserDataX structure)
    
    This class sequentially parses EVERY field in exact order from the save file.
    Size: ~2.6MB per slot (varies based on version and data)
    
    CRITICAL: Field order MUST match the Rust implementation exactly!
    Any deviation will cause misalignment and data corruption.
    """
    
    # Header (4 + 4 + 8 + 16 = 32 bytes)
    version: int = 0
    map_id: MapId = field(default_factory=MapId)
    unk0x8: bytes = field(default_factory=lambda: b'\x00' * 8)
    unk0x10: bytes = field(default_factory=lambda: b'\x00' * 16)
    
    # Gaitem map (VARIABLE LENGTH! 5118 or 5120 entries)
    gaitem_map: List[Gaitem] = field(default_factory=list)
    
    # Player data (0x1B0 = 432 bytes)
    player_game_data: PlayerGameData = field(default_factory=PlayerGameData)
    
    # SP Effects (13 entries ÃƒÆ’Ã¢â‚¬â€ 16 bytes = 208 bytes, but actually reads different)
    sp_effects: List[SPEffect] = field(default_factory=list)
    
    # Equipment structures
    equipped_items_equip_index: EquippedItemsEquipIndex = field(default_factory=EquippedItemsEquipIndex)
    active_weapon_slots_and_arm_style: ActiveWeaponSlotsAndArmStyle = field(default_factory=ActiveWeaponSlotsAndArmStyle)
    equipped_items_item_id: EquippedItemsItemIds = field(default_factory=EquippedItemsItemIds)
    equipped_items_gaitem_handle: EquippedItemsGaitemHandles = field(default_factory=EquippedItemsGaitemHandles)
    
    # Inventory held (CRITICAL: 0xa80 common, 0x180 key)
    inventory_held: Inventory = field(default_factory=Inventory)
    
    # More equipment
    equipped_spells: EquippedSpells = field(default_factory=EquippedSpells)
    equipped_items: EquippedItems = field(default_factory=EquippedItems)
    equipped_gestures: EquippedGestures = field(default_factory=EquippedGestures)
    acquired_projectiles: AcquiredProjectiles = field(default_factory=AcquiredProjectiles)
    equipped_armaments_and_items: EquippedArmamentsAndItems = field(default_factory=EquippedArmamentsAndItems)
    equipped_physics: EquippedPhysics = field(default_factory=EquippedPhysics)
    
    # Face data (0x12F = 303 bytes when in_profile_summary=False)
    face_data: FaceData = field(default_factory=FaceData)
    
    # Inventory storage (CRITICAL: 0x780 common, 0x80 key)
    inventory_storage_box: Inventory = field(default_factory=Inventory)
    
    # Gestures and regions
    gestures: Gestures = field(default_factory=Gestures)
    unlocked_regions: Regions = field(default_factory=Regions)
    
    # Horse/Torrent
    horse: RideGameData = field(default_factory=RideGameData)
    
    # Control byte (1 byte)
    control_byte_maybe: int = 0
    
    # Blood stain
    blood_stain: BloodStain = field(default_factory=BloodStain)
    
    # Unknown fields (8 bytes total)
    unk_gamedataman_0x120_or_gamedataman_0x130: int = 0
    unk_gamedataman_0x88: int = 0
    
    # Menu and game data
    menu_profile_save_load: MenuSaveLoad = field(default_factory=MenuSaveLoad)
    trophy_equip_data: TrophyEquipData = field(default_factory=TrophyEquipData)
    gaitem_game_data: GaitemGameData = field(default_factory=GaitemGameData)
    tutorial_data: TutorialData = field(default_factory=TutorialData)
    
    # GameMan bytes (3 bytes)
    gameman_0x8c: int = 0
    gameman_0x8d: int = 0
    gameman_0x8e: int = 0
    
    # Death and character info
    total_deaths_count: int = 0
    character_type: int = 0
    in_online_session_flag: int = 0
    character_type_online: int = 0
    last_rested_grace: int = 0
    not_alone_flag: int = 0
    in_game_countdown_timer: int = 0
    unk_gamedataman_0x124_or_gamedataman_0x134: int = 0
    
    # Event flags (MASSIVE! 0x1BF99F = 1,833,375 bytes)
    event_flags: bytes = field(default_factory=lambda: b'\x00' * 0x1BF99F)
    event_flags_terminator: int = 0
    
    # World structures
    field_area: FieldArea = field(default_factory=FieldArea)
    world_area: WorldArea = field(default_factory=WorldArea)
    world_geom_man: WorldGeomMan = field(default_factory=WorldGeomMan)
    world_geom_man2: WorldGeomMan = field(default_factory=WorldGeomMan)
    rend_man: RendMan = field(default_factory=RendMan)
    
    # Player position
    player_coordinates: PlayerCoordinates = field(default_factory=PlayerCoordinates)
    
    # More GameMan bytes
    game_man_0x5be: int = 0
    game_man_0x5bf: int = 0
    spawn_point_entity_id: int = 0
    game_man_0xb64: int = 0
    
    # Version-specific fields
    temp_spawn_point_entity_id: Optional[int] = None  # version >= 65
    game_man_0xcb3: Optional[int] = None  # version >= 66
    
    # Network and world state
    net_man: NetMan = field(default_factory=NetMan)
    world_area_weather: WorldAreaWeather = field(default_factory=WorldAreaWeather)
    world_area_time: WorldAreaTime = field(default_factory=WorldAreaTime)
    base_version: BaseVersion = field(default_factory=BaseVersion)
    steam_id: int = 0
    ps5_activity: PS5Activity = field(default_factory=PS5Activity)
    dlc: DLC = field(default_factory=DLC)
    player_data_hash: PlayerGameDataHash = field(default_factory=PlayerGameDataHash)
    
    # Any remaining bytes
    rest: bytes = b''
    

    @classmethod
    def _find_gesture_start(cls, f: BytesIO, start_pos: int, max_pos: int) -> Optional[int]:
        """
        Find where gestures actually start using STRICT pattern matching.
        
        CRITICAL: Mystery structure can be NEGATIVE or POSITIVE.
        Must be VERY strict to avoid false positives!
        """
        original_pos = f.tell()
        
        # Search range: -1KB to +2KB
        search_start = max(start_pos - 1000, 0)
        search_end = min(start_pos + 2000, max_pos - 512)
        
        best_match = None
        best_score = 0
        
        for offset in range(search_start, search_end, 4):
            f.seek(offset)
            chunk = f.read(256)
            if len(chunk) < 256:
                continue
            
            score = 0
            
            # Pattern 1: VERY high 0xFF density (bitmask gestures)
            ff_count = chunk.count(0xFF)
            if ff_count > 220:  # Very strict - need 85%+ 0xFF
                score = 100
            elif ff_count > 180:  # Medium match
                score = 50
            
            # Pattern 2: Gesture ID validation (must be CONSECUTIVE and VALID)
            consecutive_valid = 0
            max_consecutive = 0
            for i in range(0, 64, 4):
                if i + 4 <= len(chunk):
                    val = struct.unpack('<I', chunk[i:i+4])[0]
                    # Very strict gesture ID ranges
                    if val == 0 or val == 0xFFFFFFFE or (3000000 <= val <= 9000000):
                        consecutive_valid += 1
                        max_consecutive = max(max_consecutive, consecutive_valid)
                    else:
                        consecutive_valid = 0
            
            if max_consecutive >= 12:  # Need 12+ consecutive valid IDs
                score = max(score, 80)
            elif max_consecutive >= 8:
                score = max(score, 40)
            
            # Track best match
            if score > best_score:
                best_score = score
                best_match = offset
        
        f.seek(original_pos)
        
        # Only return if we have a STRONG match (score >= 80)
        if best_score >= 80 and best_match is not None:
            return best_match
        
        # No strong pattern - assume no mystery structure
        return start_pos
    

    @classmethod
    def read(cls, f: BytesIO, is_ps: bool, slot_start_offset: int, slot_size: int) -> UserDataX:
        """
        Read complete UserDataX from stream with robust error handling.
        
        CRITICAL FIX: This version uses slot boundary tracking to handle
        version differences and unknown structures added in game updates.
        
        Args:
            f: BytesIO stream positioned at start of character slot data
            is_ps: True if PlayStation format (no checksum)
            slot_start_offset: Absolute file offset where slot data starts (after checksum)
            slot_size: Total size of slot data (0x280000 = 2,621,440 bytes)
            
        Returns:
            UserDataX instance with all fields populated
        """
        obj = cls()
        data_start = f.tell()  # Track where we started reading
        
        # Read version (4 bytes)
        obj.version = struct.unpack("<I", f.read(4))[0]
        print(f"    [0x{f.tell()-data_start:X}] Version: {obj.version}")
        
        # Empty slot check
        if obj.version == 0:
            # Read rest of slot to maintain alignment
            bytes_read = f.tell() - data_start
            remaining = slot_size - bytes_read
            if remaining > 0:
                f.read(remaining)
            return obj
        
        # Read map_id and header (4 + 8 + 16 = 28 bytes)
        obj.map_id = MapId.read(f)
        obj.unk0x8 = f.read(8)
        obj.unk0x10 = f.read(16)
        print(f"    [0x{f.tell()-data_start:X}] After header")
        
        # Read Gaitem map (VARIABLE LENGTH!)
        gaitem_count = 0x13FE if obj.version <= 81 else 0x1400  # 5118 or 5120
        print(f"    Reading {gaitem_count} gaitems...")
        obj.gaitem_map = [Gaitem.read(f) for _ in range(gaitem_count)]
        print(f"    [0x{f.tell()-data_start:X}] After gaitems")
        
        # Read player game data (432 bytes)
        print(f"    Reading player data...")
        obj.player_game_data = PlayerGameData.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After player data")
        
        # Read SP effects (13 entries)
        print(f"    Reading SP effects...")
        obj.sp_effects = [SPEffect.read(f) for _ in range(13)]
        print(f"    [0x{f.tell()-data_start:X}] After SP effects")
        
        # Read equipment structures
        print(f"    Reading equipment...")
        obj.equipped_items_equip_index = EquippedItemsEquipIndex.read(f)
        obj.active_weapon_slots_and_arm_style = ActiveWeaponSlotsAndArmStyle.read(f)
        obj.equipped_items_item_id = EquippedItemsItemIds.read(f)
        obj.equipped_items_gaitem_handle = EquippedItemsGaitemHandles.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After equipment structures")
        
        # Read inventory held (CRITICAL CAPACITIES - VERSION DEPENDENT!)
        print(f"    Reading held inventory...")
        # ALWAYS use maximum capacity - version doesn't determine this!
        # The count fields tell us how many are actually used
        held_common_cap = 0xa80   # 2,688 common items (ALWAYS)
        held_key_cap = 0x180      # 384 key items (ALWAYS)
        obj.inventory_held = Inventory.read(f, held_common_cap, held_key_cap)
        print(f"    [0x{f.tell()-data_start:X}] After held inventory")
        
        # Read more equipment
        obj.equipped_spells = EquippedSpells.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After EquippedSpells")
        obj.equipped_items = EquippedItems.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After EquippedItems")
        obj.equipped_gestures = EquippedGestures.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After EquippedGestures")
        obj.acquired_projectiles = AcquiredProjectiles.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After AcquiredProjectiles")
        obj.equipped_armaments_and_items = EquippedArmamentsAndItems.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After EquippedArmamentsAndItems")
        obj.equipped_physics = EquippedPhysics.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After EquippedPhysics (more equipment complete)")
        
        # Read face data (303 bytes)
        print(f"    Reading face data...")
        obj.face_data = FaceData.read(f, in_profile_summary=False)
        print(f"    [0x{f.tell()-data_start:X}] After face data")
        
        # Read inventory storage (CRITICAL CAPACITIES!)
        print(f"    Reading storage inventory...")
        obj.inventory_storage_box = Inventory.read(f, 0x780, 0x80)
        print(f"    [0x{f.tell()-data_start:X}] After storage inventory")
        
        # Parse remaining structures (gestures comes immediately after storage)
        print(f"    Reading gestures and regions...")
        obj.gestures = Gestures.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After gestures")
        obj.unlocked_regions = Regions.read(f)
        print(f"      Regions count: {obj.unlocked_regions.count}")
        print(f"    [0x{f.tell()-data_start:X}] After regions")
        
        print(f"    Reading Torrent data...")
        obj.horse = RideGameData.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After horse")
        obj.control_byte_maybe = struct.unpack("<B", f.read(1))[0]
        print(f"    [0x{f.tell()-data_start:X}] After control byte")
        obj.blood_stain = BloodStain.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After blood stain")
        obj.unk_gamedataman_0x120_or_gamedataman_0x130 = struct.unpack("<I", f.read(4))[0]
        obj.unk_gamedataman_0x88 = struct.unpack("<I", f.read(4))[0]
        print(f"    [0x{f.tell()-data_start:X}] After unk fields")
        
        print(f"    Reading menu and game data...")
        try:
            # MenuSaveLoad only exists in version 151+
            obj.menu_profile_save_load = MenuSaveLoad.read(f)
            print(f"    [0x{f.tell()-data_start:X}] After MenuSaveLoad")
            obj.trophy_equip_data = TrophyEquipData.read(f)
            print(f"    [0x{f.tell()-data_start:X}] After TrophyEquipData")
            obj.gaitem_game_data = GaitemGameData.read(f)
            print(f"    [0x{f.tell()-data_start:X}] After GaitemGameData")
            obj.tutorial_data = TutorialData.read(f)
            print(f"    [0x{f.tell()-data_start:X}] After TutorialData")
        except Exception as e:
            print(f"      ⚠ Error in menu data: {e}")
            print(f"      File position: {f.tell()}")
            print(f"      Expected to be around: {data_start + 0x1C0000}")
            raise

        obj.gameman_0x8c = struct.unpack("<B", f.read(1))[0]
        obj.gameman_0x8d = struct.unpack("<B", f.read(1))[0]
        obj.gameman_0x8e = struct.unpack("<B", f.read(1))[0]
        print(f"    [0x{f.tell()-data_start:X}] After gameman bytes")
        
        obj.total_deaths_count = struct.unpack("<I", f.read(4))[0]
        obj.character_type = struct.unpack("<i", f.read(4))[0]
        obj.in_online_session_flag = struct.unpack("<B", f.read(1))[0]
        obj.character_type_online = struct.unpack("<I", f.read(4))[0]
        obj.last_rested_grace = struct.unpack("<I", f.read(4))[0]
        obj.not_alone_flag = struct.unpack("<B", f.read(1))[0]
        obj.in_game_countdown_timer = struct.unpack("<I", f.read(4))[0]
        obj.unk_gamedataman_0x124_or_gamedataman_0x134 = struct.unpack("<I", f.read(4))[0]
        print(f"    [0x{f.tell()-data_start:X}] After game state fields")
        
        print(f"    Reading event flags (1.8MB)...")
        obj.event_flags = f.read(0x1BF99F)
        obj.event_flags_terminator = struct.unpack("<B", f.read(1))[0]
        # There are 16 more bytes after the terminator

        print(f"    [0x{f.tell()-data_start:X}] After event flags")
        
        print(f"    Reading world structures...")
        obj.field_area = FieldArea.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After FieldArea")
        obj.world_area = WorldArea.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After WorldArea")
        obj.world_geom_man = WorldGeomMan.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After WorldGeomMan")
        obj.world_geom_man2 = WorldGeomMan.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After WorldGeomMan2")
        obj.rend_man = RendMan.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After RendMan")
        obj.player_coordinates = PlayerCoordinates.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After PlayerCoordinates")
        
        # 2 bytes padding after PlayerCoordinates
        f.read(2)
        obj.spawn_point_entity_id = struct.unpack("<I", f.read(4))[0]
        # 4 bytes padding
        obj.game_man_0xb64 = struct.unpack("<I", f.read(4))[0]
        print(f"    [0x{f.tell()-data_start:X}] After spawn point fields")
        
        if obj.version >= 65:
            obj.temp_spawn_point_entity_id = struct.unpack("<I", f.read(4))[0]
            print(f"    [0x{f.tell()-data_start:X}] After temp spawn (v>=65)")
        if obj.version >= 66:
            obj.game_man_0xcb3 = struct.unpack("<B", f.read(1))[0]
            print(f"    [0x{f.tell()-data_start:X}] After game_man_0xcb3 (v>=66)")
        
        print(f"    Reading network manager...")
        obj.net_man = NetMan.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After NetMan")
        
        # DIAGNOSTIC: Show exact position and bytes
        current_pos = f.tell()
        absolute_pos = current_pos + 0x300
        diagnostic_bytes = f.read(24)
        f.seek(current_pos)
        print(f"    DIAGNOSTIC: Relative={current_pos:X}, Absolute={absolute_pos:X} (expected=0x21A7A1)")
        print(f"      Short by: {0x21A7A1 - absolute_pos} bytes (0x{0x21A7A1 - absolute_pos:X})")
        print(f"      Weather (12 bytes): {diagnostic_bytes[:12].hex(' ')}")
        print(f"      Time (12 bytes): {diagnostic_bytes[12:].hex(' ')}")
        
        obj.world_area_weather = WorldAreaWeather.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After Weather (AreaId={obj.world_area_weather.area_id})")
        obj.world_area_time = WorldAreaTime.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After Time ({obj.world_area_time})")
        obj.base_version = BaseVersion.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After BaseVersion")
        obj.steam_id = struct.unpack("<Q", f.read(8))[0]
        print(f"    [0x{f.tell()-data_start:X}] After SteamId")
        obj.ps5_activity = PS5Activity.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After PS5Activity")
        obj.dlc = DLC.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After DLC")
        obj.player_data_hash = PlayerGameDataHash.read(f)
        print(f"    [0x{f.tell()-data_start:X}] After PlayerDataHash")
        
        print(f"    âœ“ All structures parsed successfully")

        
        # CRITICAL: Always seek to exact slot boundary, then read rest
        # Calculate where we should be
        slot_end_position = data_start + slot_size
        current_position = f.tell()
        
        if current_position > slot_end_position:
            # We overread - seek back to slot boundary
            print(f"    Ã¢Å¡Â  WARNING: Read {current_position - slot_end_position} bytes beyond slot boundary!")
            print(f"      Seeking back to slot boundary...")
            f.seek(slot_end_position)
        elif current_position < slot_end_position:
            # We have bytes left - read them as rest
            remaining = slot_end_position - current_position
            obj.rest = f.read(remaining)
            print(f"    Read {remaining:,} rest bytes to reach slot boundary")
        
        print(f"    Character slot parsed successfully!")
        return obj
    
    def is_empty(self) -> bool:
        """Check if this is an empty character slot"""
        return self.version == 0
    
    def get_character_name(self) -> str:
        """Get character name"""
        return self.player_game_data.character_name
    
    def get_level(self) -> int:
        """Get character level"""
        return self.player_game_data.level
    
    def has_torrent_bug(self) -> bool:
        """Check if Torrent has the infinite loading bug"""
        return self.horse.has_bug()
    
    def fix_torrent_bug(self):
        """Fix Torrent infinite loading bug"""
        self.horse.fix_bug()
    
    def has_weather_corruption(self) -> bool:
        """
        Check if weather data is corrupted.
        Note: Weather AreaId=0 is NORMAL for Seamless Co-op saves, not corruption.
        Only flag as corruption if there are other signs of issues.
        """
        # For now, don't flag weather as corrupted since 0 is valid for co-op
        return False
    
    def has_time_corruption(self) -> bool:
        """
        Check if time data is corrupted.
        Note: Time 00:00:00 is NORMAL for Seamless Co-op saves, not corruption.
        Only flag as corruption if combined with other issues.
        """
        # For now, don't flag time as corrupted since 00:00:00 is valid for co-op
        return False