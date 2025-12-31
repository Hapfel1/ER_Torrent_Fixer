"""Command-line interface for ER Save Fixer."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from er_save_fixer.gui import main as gui_main
from er_save_fixer.parser import EldenRingSaveFile, MapID


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _parse_slot(value: str) -> int:
    """Accept slot as 1-10 (preferred) or 0-9 (legacy-ish). Returns 0-based index."""
    try:
        n = int(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError("slot must be an integer") from e

    if 1 <= n <= 10:
        return n - 1
    if 0 <= n <= 9:
        return n
    raise argparse.ArgumentTypeError("slot must be in range 1-10 (or 0-9)")


def _map_for_teleport(name: str) -> MapID:
    # Note: MapID bytes are stored reversed in file
    # Display format "AA BB CC DD" = file bytes [DD, CC, BB, AA]
    if name == "limgrave":
        return MapID(bytes([0, 36, 42, 60]))  # Display: 60 42 36 00
    if name == "roundtable":
        return MapID(bytes([0, 0, 10, 11]))  # Display: 11 10 00 00
    raise ValueError(f"unknown teleport target: {name}")


def cmd_gui(_args: argparse.Namespace) -> int:
    gui_main()
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    save_path = Path(args.save).expanduser()
    save = EldenRingSaveFile.from_file(str(save_path))

    for slot_idx in save.get_active_slots():
        slot = save.characters[slot_idx]
        if not slot:
            continue
        name = slot.get_character_name() or f"Character {slot_idx + 1}"
        map_id = slot.get_slot_map_id()
        map_str = map_id.to_string_decimal() if map_id else "Unknown"
        # Stable, greppable output:
        print(f"slot={slot_idx + 1} name={name} map={map_str}")

    return 0


def cmd_fix(args: argparse.Namespace) -> int:
    save_path = Path(args.save).expanduser()
    slot_idx = args.slot

    save = EldenRingSaveFile.from_file(str(save_path))
    slot = save.characters[slot_idx]
    if not slot:
        raise RuntimeError(f"slot {slot_idx + 1} is empty or could not be parsed")

    actions: list[str] = []

    backup_path = save_path.with_suffix(save_path.suffix + ".backup")
    if args.backup:
        if backup_path.exists():
            backup_path.unlink()
        shutil.copy2(save_path, backup_path)
        actions.append(f"backup={backup_path.name}")

    # Fix 2: Corruption
    has_corruption, _issues = slot.has_corruption()
    if has_corruption:
        was_fixed, fixes = save.fix_character_corruption(slot_idx)
        if was_fixed:
            for fix in fixes:
                actions.append(f"corruption:{fix}")

    # Fix 3: Teleport (optional)
    if args.teleport is not None:
        new_map = _map_for_teleport(args.teleport)
        map_offset = slot.data_start + 0x4
        save.data[map_offset : map_offset + 4] = new_map.to_bytes()
        actions.append(f"teleport:{args.teleport}")

    if not actions:
        actions.append("no_changes_needed")

    save.recalculate_checksums()
    save.save()

    print(f"ok slot={slot_idx + 1} actions=" + ";".join(actions))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="er-save-fixer")
    sub = p.add_subparsers(dest="command")

    p_gui = sub.add_parser("gui", help="Launch the GUI (default)")
    p_gui.set_defaults(_handler=cmd_gui)

    p_list = sub.add_parser("list", help="List characters in a save file")
    p_list.add_argument("--save", required=True, help="Path to ER*.sl2/ER*.co2 save")
    p_list.set_defaults(_handler=cmd_list)

    p_fix = sub.add_parser("fix", help="Fix a character slot (headless)")
    p_fix.add_argument("--save", required=True, help="Path to ER*.sl2/ER*.co2 save")
    p_fix.add_argument(
        "--slot", required=True, type=_parse_slot, help="Character slot (1-10)"
    )
    p_fix.add_argument(
        "--teleport",
        choices=["limgrave", "roundtable"],
        help="Force teleport destination",
    )
    backup_group = p_fix.add_mutually_exclusive_group()
    backup_group.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create .backup copy (default)",
    )
    backup_group.add_argument(
        "--no-backup",
        dest="backup",
        action="store_false",
        help="Do not create .backup copy",
    )
    p_fix.set_defaults(_handler=cmd_fix)

    return p


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()

    # Default subcommand: gui
    if not argv:
        argv = ["gui"]

    args = parser.parse_args(argv)
    handler = getattr(args, "_handler", None)
    if handler is None:
        # `argparse` will already have printed help for invalid usage, but keep exit code consistent.
        parser.print_help()
        return 2

    try:
        return int(handler(args))
    except SystemExit:
        raise
    except Exception as e:
        _eprint(f"error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
