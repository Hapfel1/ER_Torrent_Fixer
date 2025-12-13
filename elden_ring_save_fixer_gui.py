"""
Elden Ring Save File Fixer - Character Selection GUI
Fixes Torrent bug and DLC location issues
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import subprocess
from pathlib import Path

from elden_ring_save_parser import EldenRingSaveFile, MapID, HorseState

class SaveFileFixer:
    def __init__(self, root):
        self.root = root
        self.root.title("Elden Ring Save File Fixer")
        self.root.geometry("700x700")
        self.root.resizable(False, False)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        self.default_save_path = Path(os.environ.get('APPDATA', '')) / "EldenRing"
        self.save_file = None
        self.selected_character = None
        
        self.setup_ui()
    def setup_ui(self):
        # Title
        title_frame = ttk.Frame(self.root, padding="15")
        title_frame.pack(fill=tk.X)
        
        ttk.Label(
            title_frame, 
            text="Elden Ring Save File Fixer",
            font=('Segoe UI', 18, 'bold')
        ).pack()
        
        ttk.Label(
            title_frame,
            text="Fix Torrent & DLC infinite loading screen issues",
            font=('Segoe UI', 10)
        ).pack()
        
        # File Selection
        file_frame = ttk.LabelFrame(self.root, text="Step 1: Select Save File", padding="15")
        file_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.file_path_var = tk.StringVar()
        
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X)
        
        ttk.Entry(path_frame, textvariable=self.file_path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(path_frame, text="Browse", command=self.browse_file, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(path_frame, text="Auto-Find", command=self.auto_detect, width=10).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(file_frame, text="Load Characters", command=self.load_characters, width=20).pack(pady=(10, 0))
        
        # Character Selection
        char_frame = ttk.LabelFrame(self.root, text="Step 2: Select Character to Fix", padding="15")
        char_frame.pack(fill=tk.X, padx=15, pady=10) 
        
        # Character list 
        list_frame = ttk.Frame(char_frame)
        list_frame.pack(fill=tk.X) 
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.char_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Consolas', 10),
            height=6,  
            selectmode=tk.SINGLE
        )
        self.char_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)  
        scrollbar.config(command=self.char_listbox.yview)
        
        self.char_listbox.bind('<<ListboxSelect>>', self.on_character_select)
        
       
        info_label_frame = ttk.LabelFrame(self.root, text="Character Info", padding="15")
        info_label_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10)) 
        
        self.info_text = tk.Text(
            info_label_frame,
            height=10,  
            width=80,
            font=('Consolas', 9),
            bg='#f0f0f0',
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)  
        
        # Fix button
        button_frame = ttk.Frame(self.root, padding="15")
        button_frame.pack(fill=tk.X)
        
        self.fix_button = ttk.Button(
            button_frame,
            text="Fix Selected Character",
            command=self.fix_character,
            state=tk.DISABLED,
            width=30
        )
        self.fix_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Restore Backup", command=self.restore_backup, width=20).pack(side=tk.LEFT, padx=5)
        
        # Status
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Ready - Select a save file to begin")
        ttk.Label(
            status_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2)
        ).pack(fill=tk.X)

    def is_elden_ring_running(self):
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq eldenring.exe', '/NH'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if 'eldenring.exe' in result.stdout.lower():
                return True
            
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq start_protected_game.exe', '/NH'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if 'start_protected_game.exe' in result.stdout.lower():
                return True
            
            return False
        except:
            return None
    
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Elden Ring Save File",
            initialdir=self.default_save_path,
            filetypes=[("Elden Ring Saves", "*.sl2 *.co2"), ("All files", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)
            self.status_var.set(f"Selected: {os.path.basename(filename)}")
    
    def auto_detect(self):
        if not self.default_save_path.exists():
            messagebox.showerror("Not Found", f"Elden Ring save folder not found:\n{self.default_save_path}")
            return
        
        saves = list(self.default_save_path.rglob("ER*.sl2")) + list(self.default_save_path.rglob("ER*.co2"))
        
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
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Found {len(saves)} save files:", font=('Segoe UI', 10, 'bold'), padding=10).pack()
        
        listbox_frame = ttk.Frame(dialog, padding=10)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=('Consolas', 9))
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
        listbox.bind('<Double-Button-1>', lambda e: select_save())
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
                "Please close Elden Ring before loading the save file."
            )
            return
        
        try:
            self.status_var.set("Loading save file...")
            self.root.update()
            
            self.save_file = EldenRingSaveFile(save_path)
            
            # Clear listbox
            self.char_listbox.delete(0, tk.END)
            
            active_slots = self.save_file.get_active_slots()
            
            if not active_slots:
                messagebox.showinfo("No Characters", "No active characters found in this save file.")
                self.status_var.set("No characters found")
                return
            
            # Populate listbox with characters
            for slot_idx in active_slots:
                slot = self.save_file.characters[slot_idx]
                if not slot:
                    continue
                
                name = slot.get_character_name() or f"Character {slot_idx + 1}"
                map_id = slot.get_slot_map_id()
                map_str = map_id.to_string() if map_id else "Unknown"
                
                # Format: "Slot 1 | IfLucadidthat | Map: 00_00_01_0A"
                display_text = f"Slot {slot_idx + 1:2d} | {name:16s} | Map: {map_str}"
                self.char_listbox.insert(tk.END, display_text)
                
                # Store slot index as data
                self.char_listbox.itemconfig(tk.END, {'fg': 'black'})
            
            self.status_var.set(f"Loaded {len(active_slots)} character(s)")
            messagebox.showinfo("Success", f"Found {len(active_slots)} active character(s).\n\nSelect a character to fix.")
            
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
        
        self.selected_character = slot_idx
        
        # Show character info
        slot = self.save_file.characters[slot_idx]
        name = slot.get_character_name() or f"Character {slot_idx + 1}"
        map_id = slot.get_slot_map_id()
        
        info = f"Character: {name}\n"
        info += f"Slot: {slot_idx + 1}\n"
        if map_id:
            info += f"Current Map: {map_id.to_string()}\n"
        
        # Check Horse status
        horse = slot.get_horse_data()
        if horse:
            info += f"\nTorrent HP: {horse.hp}\n"
            info += f"Torrent State: {horse.state.name if horse.state.value != 0 else 'DEAD'}\n"
            
            # Check for BUG first (HP=0, State=Active)
            if horse.has_bug():
                info += "\nTORRENT BUG DETECTED!\n"
                info += "Will fix: Change State from Active to Dead"
            # Check if Torrent is dead (HP=0 OR State=Dead OR State=0)
            elif horse.hp == 0 or horse.state == HorseState.DEAD or horse.state.value == 0:
                info += "\n✓ Torrent is dead\n"
                info += "No issues detected"
            else:
                # Check DLC location
                if map_id and map_id.is_dlc():
                    info += "\nDLC LOCATION DETECTED!\n"
                    info += "Will fix: Teleport to Limgrave (60 42 36 00)"
                else:
                    info += "\nNo issues detected\n"
                    info += "\nYou can still teleport to Limgrave if you are\n"
                    info += "experiencing random infinite loading screens."
        else:
            info += "\nCould not find Torrent data"
        
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
        self.info_text.config(state=tk.DISABLED)
        
        
        self.fix_button.config(state=tk.NORMAL)

    def fix_character(self):
        if self.selected_character is None:
            messagebox.showerror("Error", "Please select a character first!")
            return
        
        slot_idx = self.selected_character
        slot = self.save_file.characters[slot_idx]
        name = slot.get_character_name() or f"Character {slot_idx + 1}"
        map_id = slot.get_slot_map_id()
        horse = slot.get_horse_data()
        
        # Determine what needs fixing
        has_torrent_bug = horse and horse.has_bug()
        has_dlc_location = map_id and map_id.is_dlc()
        no_issues = not has_torrent_bug and not has_dlc_location
        
        # If no issues detected, ask user if they want to teleport anyway
        if no_issues:
            if not messagebox.askyesno(
                "Manual Teleport",
                f"Character: {name}\n\n"
                f"No issues detected, but you can still teleport\n"
                f"to Limgrave if you are experiencing loading problems.\n\n"
                f"Teleport to Limgrave anyway?"
            ):
                return
        else:
            # Normal confirmation for detected issues
            if not messagebox.askyesno(
                "Confirm Fix",
                f"Fix character: {name}\n\n"
                f"A backup will be created automatically.\n"
                f"Is Elden Ring closed?\n\n"
                f"Continue?"
            ):
                return
        
        try:
            # Create backup (overwrite if exists)
            save_path = self.file_path_var.get()
            backup_path = save_path + ".backup"
            self.status_var.set("Creating backup...")
            self.root.update()
            
            # Remove old backup if it exists
            if os.path.exists(backup_path):
                os.remove(backup_path)
            
            shutil.copy2(save_path, backup_path)
            
            fixed_something = False
            fix_description = ""
            
            # Check Torrent bug first
            if has_torrent_bug:
                self.status_var.set("Fixing Torrent bug...")
                self.root.update()
                
                horse.fix_bug()
                slot.write_horse_data(horse)
                
                fix_description = "Torrent bug fixed (State: Active → Dead)"
                fixed_something = True
            
            # DLC location OR manual teleport
            if has_dlc_location or no_issues:
                self.status_var.set("Teleporting to Limgrave...")
                self.root.update()
                
                # Teleport to Limgrave: m60_42_36_00 (The First Step)
                # 010 Editor shows: "60 42 36 00" - these are decimal values
                new_map = MapID(bytes([0, 36, 42, 60]))
                
                # Write to slot
                map_offset = slot.data_start + 0x4
                self.save_file.data[map_offset:map_offset+4] = new_map.to_bytes()
                
                if has_dlc_location:
                    fix_description = f"DLC location fixed\nOld Map: {map_id.to_string()}\nNew Map: {new_map.to_string()} (Limgrave)"
                else:
                    fix_description = f"Manual teleport\nOld Map: {map_id.to_string()}\nNew Map: {new_map.to_string()} (Limgrave)"
                fixed_something = True
            
            if not fixed_something:
                messagebox.showinfo("No Changes", f"No changes were made to '{name}'")
                return
            
            # Recalculate checksums
            self.status_var.set("Recalculating checksums...")
            self.root.update()
            self.save_file.recalculate_checksums()
            
            # Save
            self.status_var.set("Saving...")
            self.root.update()
            self.save_file.save()
            
            self.status_var.set("Fix complete!")
            
            messagebox.showinfo(
                "Success!",
                f"Character fixed: {name}\n\n"
                f"{fix_description}\n\n"
                f"Backup: {os.path.basename(backup_path)}"
            )
            
            # Reload to show updated info
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
            f"This will restore your save to the backup.\n\n"
            f"Current save will be overwritten.\n\n"
            f"Continue?"
        ):
            try:
                shutil.copy2(backup_path, save_path)
                messagebox.showinfo("Success", "Backup restored successfully!")
                self.status_var.set("Backup restored")
                
                # Reload
                if self.save_file:
                    self.load_characters()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restore backup:\n{str(e)}")

def main():
    root = tk.Tk()
    app = SaveFileFixer(root)
    
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()