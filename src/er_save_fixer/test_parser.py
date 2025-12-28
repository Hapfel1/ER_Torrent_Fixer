"""
Test the complete sequential parser
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from save_parser import Save

def test_parser(save_path: str):
    print(f"Testing complete sequential parser on: {save_path}")
    print("="*60)
    
    try:
        save = Save.from_path(save_path)
        
        print(f"\nPlatform: {'PlayStation' if save.is_ps else 'PC/Seamless Co-op'}")
        print(f"Magic: {save.magic.hex()}")
        
        for i, char in enumerate(save.user_data_x):
            if char.version == 0:
                print(f"\nSlot {i}: Empty")
                continue
            
            print(f"\nSlot {i}:")
            print(f"  Version: {char.version}")
            print(f"  Map ID: {char.map_id.to_decimal()}")
            print(f"  Character Name: {char.player.character_name}")
            print(f"  Level: {char.player.level}")
            print(f"  Vigor: {char.player.vigor}")
            print(f"  Mind: {char.player.mind}")
            print(f"  Endurance: {char.player.endurance}")
            print(f"  Strength: {char.player.strength}")
            print(f"  Dexterity: {char.player.dexterity}")
            print(f"  Intelligence: {char.player.intelligence}")
            print(f"  Faith: {char.player.faith}")
            print(f"  Arcane: {char.player.arcane}")
            print(f"  HP: {char.player.hp}/{char.player.max_hp} (base: {char.player.base_max_hp})")
            print(f"  FP: {char.player.fp}/{char.player.max_fp} (base: {char.player.base_max_fp})")
            print(f"  Stamina: {char.player.sp}/{char.player.max_sp}")
            print(f"  Runes: {char.player.runes:,}")
            print(f"  Runes Memory: {char.player.runes_memory:,}")
            print(f"  Total Deaths: {char.total_deaths}")
            
            print(f"\n  Torrent:")
            print(f"    HP: {char.horse.hp}")
            print(f"    State: {char.horse.state.name}")
            if char.horse.has_bug():
                print(f"    *** TORRENT BUG DETECTED ***")
            
            print(f"\n  World State:")
            print(f"    Weather Area ID: {char.world_area_weather.area_id}")
            if char.world_area_weather.is_corrupted():
                print(f"    *** WEATHER CORRUPTED ***")
            print(f"    Time: {char.world_area_time}")
            if char.world_area_time.is_zero():
                print(f"    *** TIME IS 00:00:00 ***")
            print(f"    Game Version: {char.base_version.game_version}")
            print(f"    Steam ID: {char.steam_id}")
            
            print(f"\n  Inventory:")
            print(f"    Held Common Items: {char.inventory_held.common_item_count}")
            print(f"    Held Key Items: {char.inventory_held.key_item_count}")
            print(f"    Storage Common Items: {char.inventory_storage.common_item_count}")
            print(f"    Storage Key Items: {char.inventory_storage.key_item_count}")
            
            print(f"\n  Equipment:")
            print(f"    Crimson Flasks: {char.player.max_crimson_flask_count}")
            print(f"    Cerulean Flasks: {char.player.max_cerulean_flask_count}")
            print(f"    Additional Talisman Slots: {char.player.additional_talisman_slot_count}")
        
        print("\n" + "="*60)
        print("PARSING SUCCESSFUL!")
        print("="*60)
        
        return 0
    
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_complete_parser.py <save_file>")
        sys.exit(1)
    
    sys.exit(test_parser(sys.argv[1]))