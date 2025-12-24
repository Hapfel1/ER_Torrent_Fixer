# Elden Ring Save File Fixer

Fixes infinite loading screens and corrupted save files in Elden Ring.

## What does this fix?

**Torrent Stuck Loading Bug**
When you die on Torrent and crash or alt+F4, Torrent can get stuck in an "Active" state with 0 HP, causing infinite loading screens.

**Save File Corruption**
Fixes corrupted world state data.

**DLC Location Bug**
If you are stuck in a DLC location without owning the DLC, the game will not load. This tool teleports you back to Limgrave.

**General Loading Issues**
Can teleport you back to Limgrave as a fallback fix for other infinite loading screen problems.

## Download

[Get the latest release here](../../releases/latest)

## How to Use

1. Close Elden Ring completely
2. Run the application
3. Click "Auto-Find" or "Browse" to select your save file
4. Click "Load Characters"
5. Select the affected character from the list
6. Click "Fix Selected Character"

The tool automatically creates a backup before making changes. Use "Restore Backup" if needed.

## Running from Source

Requires Python 3.7+ with tkinter:

```bash
python elden_ring_save_fixer_gui.py
```

## Building

```bash
pyinstaller "Elden Ring Save Fixer.spec"
```

## Safety

All changes are made to a copy of your save file. The original is backed up with a timestamp. You can restore any backup using the "Restore Backup" button.

## Credits

Save file parsing based on [ClayAmore's Elden Ring Save Templates](https://github.com/ClayAmore/EldenRingSaveTemplate)
