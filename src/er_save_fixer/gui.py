"""
Elden Ring Save File Fixer - Character Selection GUI
Fixes Torrent bug and DLC location issues as well as corruption issues.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .parser import MapId, Save


class SaveFileFixer:
    def __init__(self, root):
        self.root = root
        self.root.title("Elden Ring Save File Fixer")
        self.root.geometry("700x520")
        self.root.resizable(False, False)

        style = ttk.Style()
        style.theme_use("clam")

        self.pink_colors = {"pink": "#F5A9B8", "text": "#1f1f1f"}
        style.configure("Accent.TButton", padding=6)
        style.map(
            "Accent.TButton",
            background=[("active", self.pink_colors["pink"])],
            foreground=[("active", self.pink_colors["text"])],
        )

        self.default_save_path = Path(os.environ.get("APPDATA", "")) / "EldenRing"
        self.save_file = None
        self.selected_character = None
        self.detail_popup = None
        self.clear_dlc_flag_var = None
        self.clear_invalid_dlc_var = None
        self.current_dlc_flag = False
        self.current_invalid_dlc = False

        self.setup_ui()

    def setup_ui(self):
        title_frame = ttk.Frame(self.root, padding="15")
        title_frame.pack(fill=tk.X)

        ttk.Label(
            title_frame,
            text="Elden Ring Save File Fixer",
            font=("Segoe UI", 18, "bold"),
        ).pack()

        ttk.Label(
            title_frame,
            text="Fixes infinite loading screens, corrupted save files and event flag related bugs in Elden Ring.",
            font=("Segoe UI", 10),
        ).pack()

        # File Selection
        file_frame = ttk.LabelFrame(
            self.root, text="Step 1: Select Save File", padding="15"
        )
        file_frame.pack(fill=tk.X, padx=15, pady=10)

        self.file_path_var = tk.StringVar()

        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X)

        ttk.Entry(path_frame, textvariable=self.file_path_var, width=50).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5)
        )

        ttk.Button(
            path_frame,
            text="Browse",
            command=self.browse_file,
            width=10,
            style="Accent.TButton",
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            path_frame,
            text="Auto-Find",
            command=self.auto_detect,
            width=10,
            style="Accent.TButton",
        ).pack(side=tk.LEFT, padx=2)

        buttons_frame = ttk.Frame(file_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            buttons_frame,
            text="Load Characters",
            command=self.load_characters,
            width=20,
            style="Accent.TButton",
        ).pack(side=tk.LEFT)
        ttk.Button(
            buttons_frame,
            text="Restore Backup",
            command=self.restore_backup,
            width=20,
            style="Accent.TButton",
        ).pack(side=tk.RIGHT)

        # Character Selection
        char_frame = ttk.LabelFrame(
            self.root, text="Step 2: Select Character to Fix", padding="10"
        )
        char_frame.pack(fill=tk.X, padx=15, pady=8)

        # Character list
        list_frame = ttk.Frame(char_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.char_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 10),
            height=10,
            selectmode=tk.SINGLE,
        )
        self.char_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.config(command=self.char_listbox.yview)

        # Only open details when clicking an actual list item
        self.char_listbox.bind("<ButtonRelease-1>", self.on_listbox_click)

        # Status
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_var = tk.StringVar(value="Ready - Select a save file to begin")
        ttk.Label(
            status_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2),
        ).pack(fill=tk.X)

    def is_elden_ring_running(self):
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq eldenring.exe", "/NH"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if "eldenring.exe" in result.stdout.lower():
                return True

            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq start_protected_game.exe", "/NH"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if "start_protected_game.exe" in result.stdout.lower():
                return True

            return False
        except Exception:
            return None

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Elden Ring Save File",
            initialdir=self.default_save_path,
            filetypes=[("Elden Ring Saves", "*.sl2 *.co2"), ("All files", "*.*")],
        )
        if filename:
            self.file_path_var.set(filename)
            self.status_var.set(f"Selected: {os.path.basename(filename)}")

    def auto_detect(self):
        if not self.default_save_path.exists():
            messagebox.showerror(
                "Not Found",
                f"Elden Ring save folder not found:\n{self.default_save_path}",
            )
            return

        saves = list(self.default_save_path.rglob("ER*.sl2")) + list(
            self.default_save_path.rglob("ER*.co2")
        )

        if not saves:
            messagebox.showwarning("Not Found", "No Elden Ring save files found.")
            return

        if len(saves) == 1:
            self.file_path_var.set(str(saves[0]))
            self.status_var.set("Save file auto-detected")
        else:
            self.show_save_selector(saves)

    def show_save_selector(self, saves):
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Save File")
        dialog.geometry("500x300")
        dialog.grab_set()

        # Position in center of screen
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"500x300+{x}+{y}")

        ttk.Label(
            dialog,
            text=f"Found {len(saves)} save files:",
            font=("Segoe UI", 10, "bold"),
            padding=10,
        ).pack()

        listbox_frame = ttk.Frame(dialog, padding=10)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(
            listbox_frame, yscrollcommand=scrollbar.set, font=("Consolas", 9)
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        for save in saves:
            listbox.insert(tk.END, str(save))

        def select_save():
            selection = listbox.curselection()
            if selection:
                self.file_path_var.set(str(saves[selection[0]]))
                self.status_var.set(f"Selected: {saves[selection[0]].name}")
                dialog.destroy()

        ttk.Button(dialog, text="Select", command=select_save).pack(pady=10)
        listbox.bind("<Double-Button-1>", lambda e: select_save())

    def load_characters(self):
        save_path = self.file_path_var.get()

        if not save_path or not os.path.exists(save_path):
            messagebox.showerror("Error", "Please select a valid save file first!")
            return

        # Check if game running
        game_running = self.is_elden_ring_running()

        if game_running is True:
            messagebox.showerror(
                "Elden Ring is Running!",
                "Please close Elden Ring before loading the save file.",
            )
            return

        try:
            self.status_var.set("Loading save file...")
            self.root.update()

            self.save_file = Save.from_file(save_path)

            # Clear listbox
            self.char_listbox.delete(0, tk.END)

            active_slots = self.save_file.get_active_slots()

            if not active_slots:
                messagebox.showinfo(
                    "No Characters", "No active characters found in this save file."
                )
                self.status_var.set("No characters found")
                return

            # Populate listbox with characters
            for slot_idx in active_slots:
                slot = self.save_file.characters[slot_idx]
                if not slot:
                    continue

                name = slot.get_character_name() or f"Character {slot_idx + 1}"
                map_id = slot.get_slot_map_id()
                map_str = map_id.to_string_decimal() if map_id else "Unknown"

                display_text = f"Slot {slot_idx + 1:2d} | {name:16s} | Map: {map_str}"
                self.char_listbox.insert(tk.END, display_text)
                self.char_listbox.itemconfig(tk.END, {"fg": "black"})

            self.status_var.set(f"Loaded {len(active_slots)} character(s)")
            messagebox.showinfo(
                "Success",
                f"Found {len(active_slots)} active character(s).\n\nSelect a character to fix.",
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load save file:\n{str(e)}")
            self.status_var.set("Error loading file")
            import traceback

            traceback.print_exc()

    def on_character_select(self, event):
        selection = self.char_listbox.curselection()
        if not selection:
            return

        selected_idx = selection[0]
        active_slots = self.save_file.get_active_slots()
        slot_idx = active_slots[selected_idx]

        # If the same character is re-selected, just bring popup to front
        if (
            self.selected_character == slot_idx
            and self.detail_popup
            and self.detail_popup.winfo_exists()
        ):
            try:
                self.detail_popup.lift()
                self.detail_popup.focus_force()
            except Exception:
                pass
            return

        # Close previous popup if open because a new character was selected
        if self.detail_popup and self.detail_popup.winfo_exists():
            try:
                self.detail_popup.grab_release()
            except Exception:
                pass
            self.detail_popup.destroy()
            self.detail_popup = None

        self.selected_character = slot_idx

        # Show character details in popup
        self.show_character_details(slot_idx)

    def on_listbox_click(self, event):
        """Open details only when clicking inside a real list item."""
        # Determine which index is nearest to the y click
        idx = self.char_listbox.nearest(event.y)
        bbox = self.char_listbox.bbox(idx)
        # If there is no bbox (empty list) or the click is outside the item's bbox, ignore
        if not bbox:
            return
        x, y, w, h = bbox
        if event.y < y or event.y > y + h:
            return  # Clicked in empty area below items; do nothing

        # Ensure selection is set to the clicked item
        self.char_listbox.selection_clear(0, tk.END)
        self.char_listbox.selection_set(idx)
        self.char_listbox.activate(idx)

        # Delegate to the selection handler (which handles dedup/closing)
        self.on_character_select(event)

    def show_character_details(self, slot_idx):
        """Display character details in a popup window"""
        slot = self.save_file.characters[slot_idx]
        name = slot.get_character_name() or f"Character {slot_idx + 1}"
        map_id = slot.get_slot_map_id()

        info = f"Character: {name}\n"
        info += f"Slot: {slot_idx + 1}\n"
        if map_id:
            info += f"Current Map: {map_id.to_string_decimal()}\n"

        # Check all issues upfront
        issues_detected = []

        # Check 1: Torrent bug
        horse = slot.get_horse_data()
        if horse:
            info += f"\nTorrent HP: {horse.hp}\n"
            info += f"Torrent State: {horse.state.name if horse.state.value != 0 else 'DEAD'}\n"
        else:
            info += "\nCould not find Torrent data\n"

        # Check DLC flags status
        has_dlc_flag = slot.has_dlc_flag()
        has_invalid_dlc = False
        if hasattr(slot, "dlc") and slot.dlc:
            dlc = slot.dlc
            info += "\nDLC Flags:\n"
            info += (
                f"  Shadow of the Erdtree: {'Yes' if dlc.shadow_of_erdtree else 'No'}\n"
            )
            info += (
                f"  Pre-order The Ring: {'Yes' if dlc.preorder_the_ring else 'No'}\n"
            )
            info += f"  Pre-order Ring of Miquella: {'Yes' if dlc.preorder_ring_of_miquella else 'No'}\n"
            has_invalid_dlc = dlc.has_invalid_flags()
            if has_invalid_dlc:
                info += "  WARNING: Invalid data in unused slots!\n"

        # Check 2: DLC location
        if map_id and map_id.is_dlc():
            issues_detected.append("DLC infinite loading (needs teleport)")

        # Check 3: Corruption patterns
        # Get correct SteamID from USER_DATA_10
        correct_steam_id = None
        if self.save_file.user_data_10_parsed and hasattr(
            self.save_file.user_data_10_parsed, "steam_id"
        ):
            correct_steam_id = self.save_file.user_data_10_parsed.steam_id

        has_corruption, corruption_issues = slot.has_corruption(correct_steam_id)
        if has_corruption:
            for issue in corruption_issues:
                # User-friendly issue messages
                # Parse issue format: "type:details"
                if ":" in issue:
                    issue_type, details = issue.split(":", 1)
                else:
                    issue_type, details = issue, ""

                # Remove "_sync" suffix if present
                if issue_type.endswith(("_sync", "_corruption")):
                    # Get the base type
                    base_type = issue_type.replace("_sync", "").replace(
                        "_corruption", ""
                    )
                else:
                    base_type = issue_type

                # Format messages with values - use friendly names
                if base_type == "torrent_bug" or base_type == "torrent":
                    issues_detected.append(f"Corruption: Torrent - {details}")
                elif base_type == "weather":
                    issues_detected.append(f"Corruption: Weather - {details}")
                elif base_type == "time":
                    issues_detected.append(f"Corruption: Time - {details}")
                elif base_type == "steamid":
                    issues_detected.append(f"Corruption: SteamId - {details}")
                elif base_type == "eventflag":
                    # Map event flag issue names to user-friendly descriptions
                    friendly_names = {
                        "ranni_softlock": "Ranni's Tower Quest",
                        "radahn_alive_warp": "Radahn Warp (Alive)",
                        "radahn_dead_warp": "Radahn Warp (Dead)",
                        "morgott_warp": "Morgott Warp",
                        "radagon_warp": "Radagon Warp",
                        "sealing_tree_warp": "Sealing Tree Warp (DLC)",
                    }
                    friendly = friendly_names.get(details, details)
                    issues_detected.append(f"Quest/Warp: {friendly}")
                else:
                    issues_detected.append(f"Corruption: {issue}")

        # Display issues or status
        if issues_detected:
            info += "\n" + "=" * 40 + "\n"
            info += "ISSUES DETECTED:\n"
            info += "=" * 40 + "\n"
            for issue in issues_detected:
                info += f"  - {issue}\n"
            info += "\nFix button will correct these issues"
        else:
            info += "\n" + "=" * 40 + "\n"
            info += "NO ISSUES DETECTED\n"
            info += "=" * 40 + "\n"
            info += "\nYou can still teleport to Limgrave if\n"
            info += "you are experiencing an infinite loading screen."

        # Store DLC flag status for checkbox
        self.current_dlc_flag = has_dlc_flag
        self.current_invalid_dlc = has_invalid_dlc

        # Create popup window
        self.detail_popup = tk.Toplevel(self.root)
        # Avoid flicker: position while hidden, then show
        self.detail_popup.withdraw()
        self.detail_popup.title(f"Character Details - {name}")
        width, height = 550, 550  # Increased height for DLC info
        screen_w = self.detail_popup.winfo_screenwidth()
        screen_h = self.detail_popup.winfo_screenheight()
        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)
        self.detail_popup.geometry(f"{width}x{height}+{x}+{y}")
        # Make popup non-resizable
        self.detail_popup.resizable(False, False)
        self.detail_popup.deiconify()
        self.detail_popup.lift()
        self.detail_popup.focus_force()
        # Keep popup on top and modal
        self.detail_popup.attributes("-topmost", True)
        self.detail_popup.grab_set()

        # Text widget to display info - keep as NORMAL to allow selection
        text_widget = tk.Text(
            self.detail_popup,
            font=("Consolas", 9),
            bg="#f0f0f0",
            wrap=tk.WORD,
            state=tk.NORMAL,
            padx=10,
            pady=10,
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        text_widget.insert(1.0, info)

        # Make read-only by preventing editing but keep selection/copy working
        def block_edit(event):
            # Allow Ctrl+A (select all) and Ctrl+C (copy), navigation keys, and shift modifiers
            if (
                event.state & 0x4 and event.keysym.lower() in ("a", "c")
            ) or event.keysym in (
                "Left",
                "Right",
                "Up",
                "Down",
                "Home",
                "End",
                "Prior",
                "Next",
                "Shift_L",
                "Shift_R",
            ):
                return
            return "break"

        text_widget.bind("<Key>", block_edit)
        # Block paste and middle-click insert
        text_widget.bind("<<Paste>>", lambda e: "break")
        text_widget.bind("<Control-v>", lambda e: "break")
        text_widget.bind("<Button-2>", lambda e: "break")

        # DLC flag checkboxes (show if flag is set or invalid data exists)
        self.clear_dlc_flag_var = tk.BooleanVar(value=False)
        self.clear_invalid_dlc_var = tk.BooleanVar(value=False)

        if has_dlc_flag or has_invalid_dlc:
            dlc_frame = ttk.Frame(self.detail_popup, padding="5")
            dlc_frame.pack(fill=tk.X, padx=10)

            if has_dlc_flag:
                dlc_checkbox = ttk.Checkbutton(
                    dlc_frame,
                    text="Clear Shadow of the Erdtree flag (allows loading without DLC)",
                    variable=self.clear_dlc_flag_var,
                )
                dlc_checkbox.pack(anchor=tk.W)

                info_label = ttk.Label(
                    dlc_frame,
                    text="Use if someone teleported you out of the DLC but you cannot load the save file.",
                    font=("Segoe UI", 8),
                    foreground="gray",
                )
                info_label.pack(anchor=tk.W, padx=20)

            if has_invalid_dlc:
                invalid_checkbox = ttk.Checkbutton(
                    dlc_frame,
                    text="Clear invalid DLC data (fixes corrupted DLC flags)",
                    variable=self.clear_invalid_dlc_var,
                )
                invalid_checkbox.pack(anchor=tk.W, pady=(5, 0))

                invalid_info_label = ttk.Label(
                    dlc_frame,
                    text="Invalid data in unused DLC slots can prevent save from loading.",
                    font=("Segoe UI", 8),
                    foreground="gray",
                )
                invalid_info_label.pack(anchor=tk.W, padx=20)

        # Fix button in popup
        button_frame = ttk.Frame(self.detail_popup, padding="10")
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="Fix Selected Character",
            command=self.fix_character,
            width=30,
            style="Accent.TButton",
        ).pack(side=tk.LEFT, padx=5)

    def select_teleport_location(
        self, character_name, has_issues, horse, map_id, corruption_issues
    ):
        """Show dialog to select teleport location"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Teleport Location")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"500x400+{x}+{y}")

        # Title
        title_frame = ttk.Frame(dialog, padding="15")
        title_frame.pack(fill=tk.X)

        ttk.Label(
            title_frame,
            text=f"Fix Character: {character_name}",
            font=("Segoe UI", 12, "bold"),
        ).pack()

        # Issues detected
        if has_issues:
            issues_frame = ttk.LabelFrame(dialog, text="Issues Detected", padding="10")
            issues_frame.pack(fill=tk.X, padx=15, pady=10)

            issues_list = []
            if horse and horse.has_bug():
                issues_list.append("Torrent infinite loading bug")
            if map_id and map_id.is_dlc():
                issues_list.append("DLC location (requires teleport)")
            if corruption_issues:
                issues_list.append(f"Save corruption ({len(corruption_issues)} issues)")

            for issue in issues_list:
                ttk.Label(issues_frame, text=f"  {issue}", font=("Segoe UI", 9)).pack(
                    anchor=tk.W
                )
        else:
            info_frame = ttk.Frame(dialog, padding="10")
            info_frame.pack(fill=tk.X, padx=15, pady=10)

            ttk.Label(
                info_frame,
                text="No issues detected. Teleport can still fix potential\ninfinite loading screens.",
                font=("Segoe UI", 9),
                justify=tk.LEFT,
            ).pack(anchor=tk.W)

        # Location selection
        location_frame = ttk.LabelFrame(
            dialog, text="Select Teleport Destination", padding="15"
        )
        location_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        selected_location = tk.StringVar(value="limgrave")

        # Limgrave option
        limgrave_frame = ttk.Frame(location_frame)
        limgrave_frame.pack(fill=tk.X, pady=5)

        ttk.Radiobutton(
            limgrave_frame,
            text="Limgrave",
            variable=selected_location,
            value="limgrave",
        ).pack(anchor=tk.W)

        ttk.Label(
            limgrave_frame,
            text="  Map ID: 60 42 36 00",
            font=("Segoe UI", 8),
            foreground="#666666",
        ).pack(anchor=tk.W, padx=20)

        # Roundtable Hold option
        roundtable_frame = ttk.Frame(location_frame)
        roundtable_frame.pack(fill=tk.X, pady=5)

        ttk.Radiobutton(
            roundtable_frame,
            text="Roundtable Hold",
            variable=selected_location,
            value="roundtable",
        ).pack(anchor=tk.W)

        ttk.Label(
            roundtable_frame,
            text="  Map ID: 11 10 00 00",
            font=("Segoe UI", 8),
            foreground="#666666",
        ).pack(anchor=tk.W, padx=20)

        # Result variable
        result = [None]

        def confirm():
            result[0] = selected_location.get()
            dialog.destroy()

        def cancel():
            dialog.destroy()

        # Buttons
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Button(
            button_frame,
            text="Confirm & Fix",
            command=confirm,
            width=15,
            style="Accent.TButton",
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Cancel", command=cancel, width=15).pack(
            side=tk.RIGHT, padx=5
        )

        dialog.wait_window()
        return result[0]

    def fix_character(self):
        if self.selected_character is None:
            messagebox.showerror("Error", "Please select a character first!")
            return

        slot_idx = self.selected_character
        slot = self.save_file.characters[slot_idx]
        name = slot.get_character_name() or f"Character {slot_idx + 1}"

        # Check what issues exist
        horse = slot.get_horse_data()
        has_torrent_bug = horse and horse.has_bug()

        map_id = slot.get_slot_map_id()
        has_dlc_location = map_id and map_id.is_dlc()

        # Check corruption
        # Get correct SteamID from USER_DATA_10
        correct_steam_id = None
        if self.save_file.user_data_10_parsed and hasattr(
            self.save_file.user_data_10_parsed, "steam_id"
        ):
            correct_steam_id = self.save_file.user_data_10_parsed.steam_id

        has_corruption, corruption_issues = slot.has_corruption(correct_steam_id)

        # Check if user wants to clear DLC flag
        should_clear_dlc = (
            hasattr(self, "clear_dlc_flag_var")
            and self.clear_dlc_flag_var.get()
            and slot.has_dlc_flag()
        )

        # Check if user wants to clear invalid DLC data
        should_clear_invalid = (
            hasattr(self, "clear_invalid_dlc_var")
            and self.clear_invalid_dlc_var
            and self.clear_invalid_dlc_var.get()
            and hasattr(slot, "dlc")
            and slot.dlc.has_invalid_flags()
        )

        # Determine if teleport selection is needed
        # Only show teleport dialog if:
        # 1. No issues at all and not just clearing DLC flags (user wants preventive teleport)
        # 2. DLC location issue (requires teleport)
        needs_teleport_selection = (
            not has_torrent_bug
            and not has_corruption
            and not should_clear_dlc
            and not should_clear_invalid
        ) or has_dlc_location

        teleport_location = None

        if needs_teleport_selection:
            # Show teleport location selection dialog
            # Temporarily remove topmost to show selection dialog in front
            if self.detail_popup:
                self.detail_popup.attributes("-topmost", False)

            teleport_location = self.select_teleport_location(
                name, has_dlc_location, horse, map_id, corruption_issues
            )

            # Restore topmost
            if self.detail_popup:
                self.detail_popup.attributes("-topmost", True)

            if teleport_location is None:
                return
        else:
            # For Torrent bug and/or corruption and/or DLC flags, show simple confirmation
            issues_list = []
            if has_torrent_bug:
                issues_list.append("Torrent bug")
            if has_corruption:
                issues_list.append(f"Corruption ({len(corruption_issues)} issues)")
            if should_clear_dlc:
                issues_list.append("Clear Shadow of the Erdtree flag")
            if should_clear_invalid:
                issues_list.append("Clear invalid DLC data")

            confirm_msg = (
                f"Fix character: {name}\n\n"
                f"Will fix detected issues:\n"
                + "\n".join(f"  - {issue}" for issue in issues_list)
                + "\n\n"
                "A backup will be created.\n\n"
                "Continue?"
            )

            # Temporarily remove topmost to show confirmation dialog in front
            if self.detail_popup:
                self.detail_popup.attributes("-topmost", False)

            result = messagebox.askyesno(
                "Confirm Fix", confirm_msg, parent=self.detail_popup
            )

            # Restore topmost
            if self.detail_popup:
                self.detail_popup.attributes("-topmost", True)

            if not result:
                return

        try:
            save_path = self.file_path_var.get()
            backup_path = save_path + ".backup"
            self.status_var.set("Creating backup...")
            self.root.update()

            if os.path.exists(backup_path):
                os.remove(backup_path)

            shutil.copy2(save_path, backup_path)

            fixed_issues = []

            # Fix 2: Corruption (SteamId, WorldAreaTime, WorldAreaWeather)
            if has_corruption:
                self.status_var.set("Fixing corruption...")
                self.root.update()
                was_fixed, corruption_fixes = self.save_file.fix_character_corruption(
                    slot_idx
                )
                if was_fixed:
                    for fix in corruption_fixes:
                        fixed_issues.append(f"Corruption: {fix}")

            # Fix DLC flag if checkbox was checked
            should_clear_dlc = (
                hasattr(self, "clear_dlc_flag_var")
                and self.clear_dlc_flag_var
                and self.clear_dlc_flag_var.get()
            )
            if should_clear_dlc and slot.has_dlc_flag():
                self.status_var.set("Clearing DLC flag...")
                self.root.update()
                self.save_file.clear_character_dlc_flag(slot_idx)
                fixed_issues.append("Shadow of the Erdtree flag cleared")

            # Fix invalid DLC data if checkbox was checked
            should_clear_invalid = (
                hasattr(self, "clear_invalid_dlc_var")
                and self.clear_invalid_dlc_var
                and self.clear_invalid_dlc_var.get()
            )
            if (
                should_clear_invalid
                and hasattr(slot, "dlc")
                and slot.dlc.has_invalid_flags()
            ):
                self.status_var.set("Clearing invalid DLC data...")
                self.root.update()
                self.save_file.clear_character_invalid_dlc(slot_idx)
                fixed_issues.append("Invalid DLC data cleared")

            # Fix 3: Teleport (only if user selected a location)
            if teleport_location is not None:
                location_name = ""

                # Set MapID based on selected location
                # Note: MapID bytes are stored reversed in file
                # Display format "AA BB CC DD" = file bytes [DD, CC, BB, AA]
                if teleport_location == "limgrave":
                    new_map = MapId(bytes([0, 36, 42, 60]))  # Display: 60 42 36 00
                    location_name = "Limgrave"
                else:  # roundtable
                    new_map = MapId(bytes([0, 0, 10, 11]))  # Display: 11 10 00 00
                    location_name = "Roundtable Hold"

                self.status_var.set(f"Teleporting to {location_name}...")
                self.root.update()

                map_offset = slot.data_start + 0x4
                self.save_file.data[map_offset : map_offset + 4] = new_map.to_bytes()

                if has_dlc_location:
                    fixed_issues.append(f"DLC location -> {location_name}")
                else:
                    fixed_issues.append(f"Teleported to {location_name}")

            # Recalculate checksums
            self.status_var.set("Recalculating checksums...")
            self.root.update()
            self.save_file.recalculate_checksums()

            # Save
            self.status_var.set("Saving...")
            self.root.update()
            self.save_file.save()

            self.status_var.set("Fix complete!")

            issues_text = "\n".join([f"  - {issue}" for issue in fixed_issues])

            # Close the detail popup before showing success dialog
            if self.detail_popup:
                try:
                    self.detail_popup.grab_release()
                except Exception:
                    pass
                self.detail_popup.destroy()
                self.detail_popup = None

            messagebox.showinfo(
                "Success!",
                f"Character fixed: {name}\n\n"
                f"Actions taken:\n{issues_text}\n\n"
                f"Backup: {os.path.basename(backup_path)}",
            )

            self.load_characters()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fix character:\n{str(e)}")
            self.status_var.set("Error during fix")
            import traceback

            traceback.print_exc()

    def restore_backup(self):
        save_path = self.file_path_var.get()

        if not save_path:
            messagebox.showerror("Error", "Please select a save file first!")
            return

        backup_path = save_path + ".backup"

        if not os.path.exists(backup_path):
            messagebox.showerror("Error", "No backup file found!")
            return

        if messagebox.askyesno(
            "Restore Backup",
            "This will restore your save to the backup.\n\n"
            "Current save will be overwritten.\n\n"
            "Continue?",
        ):
            try:
                shutil.copy2(backup_path, save_path)
                messagebox.showinfo("Success", "Backup restored successfully!")
                self.status_var.set("Backup restored")

                if self.save_file:
                    self.load_characters()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restore backup:\n{str(e)}")


def main():
    root = tk.Tk()
    SaveFileFixer(root)

    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    main()
