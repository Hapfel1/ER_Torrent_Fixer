"""
Elden Ring Save Parser - Save File (Main Entry Point)

Handles complete save file with 10 character slots, checksums, and platform detection.
Based on ER-Save-Lib Rust implementation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from io import BytesIO
import struct
from typing import List, Optional
from pathlib import Path

from .user_data_x import UserDataX
from .user_data_10 import UserData10


@dataclass
class Save:
    """
    Complete Elden Ring save file
    
    Structure:
    - Magic (4 bytes)
    - Header (0x2FC for PC, 0x6C for PS)
    - 10 × Character slots (UserDataX)
    - USER_DATA_10 (Common section with SteamID and ProfileSummary)
    - USER_DATA_11 (Regulation data)
    
    Each character slot on PC has:
    - MD5 checksum (16 bytes)
    - Character data (~2.6MB)
    """
    
    # File identification
    magic: bytes = b''
    is_ps: bool = False
    
    # Header
    header: bytes = b''
    
    # Character slots (10 total)
    character_slots: List[UserDataX] = field(default_factory=list)
    
    # Common section (parsed)
    user_data_10_parsed: Optional[UserData10] = None
    
    # Additional data sections (raw)
    user_data_10: bytes = b''
    user_data_11: bytes = b''
    
    @classmethod
    def from_file(cls, filepath: str) -> Save:
        """
        Load and parse save file from disk.
        
        Args:
            filepath: Path to .sl2 or .co2 save file
            
        Returns:
            Save instance with all data parsed
        """
        print(f"Loading save file: {filepath}")
        
        with open(filepath, 'rb') as file:
            data = file.read()
        
        f = BytesIO(data)
        obj = cls()
        
        # Read magic (4 bytes)
        obj.magic = f.read(4)
        
        # Detect platform
        if obj.magic == b"BND4":
            obj.is_ps = False
            print("Platform: PC (BND4)")
        elif obj.magic == b"SL2\x00":
            obj.is_ps = False
            print("Platform: PC/Seamless Co-op (SL2)")
        elif obj.magic == bytes([0xCB, 0x01, 0x9C, 0x2C]):
            obj.is_ps = True
            print("Platform: PlayStation")
        else:
            raise ValueError(f"Invalid save file magic: {obj.magic.hex()}")
        
        # Read header
        if obj.is_ps:
            header_size = 0x6C
        else:
            header_size = 0x2FC
        
        obj.header = f.read(header_size)
        print(f"Header size: {header_size} bytes")
        
        # Parse 10 character slots
        print("\nParsing character slots...")
        print("=" * 60)
        
        for slot_index in range(10):
            print(f"\n[Slot {slot_index}]")
            
            # Mark the start position of this slot's data
            slot_start = f.tell()
            
            # Read checksum (PC only)
            checksum = None
            if not obj.is_ps:
                checksum = f.read(16)
                
                # Check if we got the full checksum
                if len(checksum) < 16:
                    print(f"  ⚠ WARNING: Incomplete checksum (got {len(checksum)} bytes)")
                    print(f"  Status: End of file or corrupted slot")
                    obj.character_slots.append(UserDataX())
                    break  # No more slots
                
                # Display checksum
                checksum_hex = checksum.hex()
                print(f"  Checksum: {checksum_hex}")
                
                # Check if slot is empty (all zeros checksum)
                if checksum == bytes(16):
                    print(f"  Status: Empty slot (zero checksum)")
                    # Skip the character data for this slot
                    f.read(0x280000)  # Skip empty slot data
                    obj.character_slots.append(UserDataX())  # Add empty slot
                    continue
            
            # Mark where character data starts (after checksum)
            char_data_start = f.tell()
            
            # Calculate slot size (data portion only, without checksum)
            slot_data_size = 0x280000
            
            # Parse character data
            try:
                char = UserDataX.read(f, obj.is_ps, char_data_start, slot_data_size)
                obj.character_slots.append(char)
                
                if char.is_empty():
                    print(f"  Status: Empty slot (version 0)")
                else:
                    print(f"  Character: {char.get_character_name()}")
                    print(f"  Level: {char.get_level()}")
                    print(f"  Version: {char.version}")
                    
                    # Check for issues
                    if char.has_torrent_bug():
                        print(f"  ⚠ WARNING: Torrent bug detected!")
                    if char.has_weather_corruption():
                        print(f"  ⚠ WARNING: Weather corruption detected!")
                    if char.has_time_corruption():
                        print(f"  ⚠ WARNING: Time corruption detected!")
            
            except Exception as e:
                print(f"  ERROR parsing slot {slot_index}: {e}")
                obj.character_slots.append(UserDataX())
                # Skip to next slot boundary
                correct_position = slot_start + 0x280010
                f.seek(correct_position)
        
        # Read and parse USER_DATA_10
        print("\n" + "=" * 60)
        print("Reading USER_DATA_10 (Common section)...")
        
        user_data_10_start = f.tell()
        
        try:
            # Parse USER_DATA_10
            obj.user_data_10_parsed = UserData10.read(f, obj.is_ps)
            print(f"  Steam ID: {obj.user_data_10_parsed.steam_id}")
            print(f"  Version: {obj.user_data_10_parsed.version}")
            
            # Also keep raw bytes
            user_data_10_end = f.tell()
            f.seek(user_data_10_start)
            obj.user_data_10 = f.read(user_data_10_end - user_data_10_start)
            f.seek(user_data_10_end)
        except Exception as e:
            print(f"  WARNING: Failed to parse USER_DATA_10: {e}")
            # Fall back to reading raw bytes
            f.seek(user_data_10_start)
            if not obj.is_ps:
                f.read(16)  # Skip checksum
            obj.user_data_10 = f.read(0x60000)
        
        # Read USER_DATA_11
        print("Reading USER_DATA_11...")
        if not obj.is_ps:
            f.read(16)  # Skip checksum
        
        if obj.is_ps:
            obj.user_data_11 = f.read(0x240010)
        else:
            obj.user_data_11 = f.read(0x240010)
        
        print("\n" + "=" * 60)
        print("Save file parsed successfully!")
        print("=" * 60)
        
        return obj
    
    def to_file(self, filepath: str):
        """
        Write save file to disk.
        
        Args:
            filepath: Path where save file will be written
        """
        print(f"\nWriting save file: {filepath}")
        
        # TODO: Implement complete write functionality
        # This requires implementing write() methods for all structures
        # and recalculating checksums for PC saves
        
        raise NotImplementedError("Save file writing not yet implemented")
    
    def get_active_slots(self) -> List[int]:
        """
        Get list of slot indices that contain characters.
        
        Returns:
            List of slot indices (0-9) that are not empty
        """
        return [i for i, slot in enumerate(self.character_slots) if not slot.is_empty()]
    
    def get_slot(self, index: int) -> UserDataX:
        """
        Get character slot by index.
        
        Args:
            index: Slot index (0-9)
            
        Returns:
            UserDataX for that slot
        """
        if index < 0 or index >= 10:
            raise IndexError(f"Slot index must be 0-9, got {index}")
        return self.character_slots[index]
    
    def print_summary(self):
        """Print a summary of all character slots"""
        print("\n" + "=" * 60)
        print("SAVE FILE SUMMARY")
        print("=" * 60)
        print(f"Platform: {'PlayStation' if self.is_ps else 'PC'}")
        print(f"Magic: {self.magic.hex()}")
        
        if self.user_data_10_parsed:
            print(f"Steam ID: {self.user_data_10_parsed.steam_id}")
        
        active_slots = self.get_active_slots()
        print(f"\nActive slots: {len(active_slots)}/10")
        
        for slot_index in range(10):
            char = self.character_slots[slot_index]
            
            if char.is_empty():
                print(f"\nSlot {slot_index}: [Empty]")
            else:
                print(f"\nSlot {slot_index}: {char.get_character_name()}")
                print(f"  Level: {char.get_level()}")
                print(f"  Vigor: {char.player_game_data.vigor}")
                print(f"  HP: {char.player_game_data.hp}/{char.player_game_data.max_hp}")
                print(f"  Runes: {char.player_game_data.runes:,}")
                print(f"  Deaths: {char.total_deaths_count}")
                
                # Show profile summary time played if available
                if self.user_data_10_parsed and slot_index < len(self.user_data_10_parsed.profile_summary.profiles):
                    profile = self.user_data_10_parsed.profile_summary.profiles[slot_index]
                    hours = profile.seconds_played // 3600
                    minutes = (profile.seconds_played % 3600) // 60
                    print(f"  Time Played: {hours}h {minutes}m")
                
                # Show issues
                issues = []
                if char.has_torrent_bug():
                    issues.append("Torrent bug")
                if char.has_weather_corruption():
                    issues.append("Weather corruption")
                if char.has_time_corruption():
                    issues.append("Time corruption")
                
                if issues:
                    print(f"  ⚠ Issues: {', '.join(issues)}")
        
        print("\n" + "=" * 60)


def load_save(filepath: str) -> Save:
    """
    Convenience function to load a save file.
    
    Args:
        filepath: Path to .sl2 or .co2 file
        
    Returns:
        Parsed Save object
    """
    return Save.from_file(filepath)


# Main entry point for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m er_parser.save <save_file_path>")
        print("\nExample:")
        print("  python -m er_parser.save ER0000.sl2")
        sys.exit(1)
    
    save_path = sys.argv[1]
    
    try:
        # Load and parse save file
        save = load_save(save_path)
        
        # Print summary
        save.print_summary()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)