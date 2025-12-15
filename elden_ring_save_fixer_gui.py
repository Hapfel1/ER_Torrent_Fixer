"""
Elden Ring Save File Fixer - Character Selection GUI
Fixes Torrent bug and DLC location issues
Shows all 10 character slots correctly
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
        self.root.geometry("700x800")
        self.root.resizable(False, False)
        
        style = ttk.Style()
        style.theme_use('clam')

        self.pink_colors = {
            'pink': '#F5A9B8',
            'text': '#1f1f1f'
        }
        style.configure('Accent.TButton', padding=6)
        style.map('Accent.TButton',
                  background=[('active', self.pink_colors['pink'])],
                  foreground=[('active', self.pink_colors['text'])])
        
        self.default_save_path = Path(os.environ.get('APPDATA', '')) / "EldenRing"
        self.save_file = None
        self.selected_character = None
        
        self.setup_ui()
    
    def setup_ui(self):
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
        
        ttk.Button(path_frame, text="Browse", command=self.browse_file, width=10, style='Accent.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(path_frame, text="Auto-Find", command=self.auto_detect, width=10, style='Accent.TButton').pack(side=tk.LEFT, padx=2)
        
        ttk.Button(file_frame, text="Load Characters", command=self.load_characters, width=20, style='Accent.TButton').pack(pady=(10, 0))
        
        # Character Selection
        char_frame = ttk.LabelFrame(self.root, text="Step 2: Select Character to Fix", padding="15")
        char_frame.pack(fill=tk.X, padx=15, pady=12) 
        
        # Character list 
        list_frame = ttk.Frame(char_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.char_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Consolas', 10),
            height=8,  
            selectmode=tk.SINGLE
        )
        self.char_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)  
        scrollbar.config(command=self.char_listbox.yview)
        
        self.char_listbox.bind('<<ListboxSelect>>', self.on_character_select)
        
       
        info_label_frame = ttk.LabelFrame(self.root, text="Character Info", padding="15")
        info_label_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10)) 
        
        self.info_text = tk.Text(
            info_label_frame,
            height=14,  
            width=80,
            font=('Consolas', 9),
            bg='#f0f0f0',
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Fix button
        button_frame = ttk.Frame(self.root, padding="15")
        button_frame.pack(fill=tk.X)
        
        self.fix_button = ttk.Button(
            button_frame,
            text="Fix Selected Character",
            command=self.fix_character,
            state=tk.DISABLED,
            width=30,
            style='Accent.TButton'
        )
        self.fix_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Restore Backup", command=self.restore_backup, width=20, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        
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
                map_str = map_id.to_string_decimal() if map_id else "Unknown"
                
                display_text = f"Slot {slot_idx + 1:2d} | {name:16s} | Map: {map_str}"
                self.char_listbox.insert(tk.END, display_text)
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
            info += f"Current Map: {map_id.to_string_decimal()}\n"
        
        # Check all issues upfront
        issues_detected = []
        
        # Check 1: Torrent bug
        horse = slot.get_horse_data()
        if horse:
            info += f"\nTorrent HP: {horse.hp}\n"
            info += f"Torrent State: {horse.state.name if horse.state.value != 0 else 'DEAD'}\n"
            
            if horse.has_bug():
                issues_detected.append("Torrent stuck loading bug")
        else:
            info += "\nCould not find Torrent data\n"
        
        # Check 2: DLC location
        if map_id and map_id.is_dlc():
            issues_detected.append("DLC infinite loading (needs teleport)")
        
        # Display issues or status
        if issues_detected:
            info += "\n" + "="*40 + "\n"
            info += "ISSUES DETECTED:\n"
            info += "="*40 + "\n"
            for issue in issues_detected:
                info += f"  - {issue}\n"
            info += "\nFix button will correct these issues"
        else:
            info += "\n" + "="*40 + "\n"
            info += "NO ISSUES DETECTED\n"
            info += "="*40 + "\n"
            info += "\nYou can still teleport to Limgrave if\n"
            info += "you are experiencing random infinite loading screens."
        
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
        
        # Check what issues exist
        has_any_issues = False
        
        horse = slot.get_horse_data()
        if horse and horse.has_bug():
            has_any_issues = True
        
        map_id = slot.get_slot_map_id()
        if map_id and map_id.is_dlc():
            has_any_issues = True
        
        # Confirmation dialog
        if has_any_issues:
            confirm_msg = (
                f"Fix character: {name}\n\n"
                f"Will fix detected issues:\n"
                f"  - Torrent bug (if present)\n"
                f"  - DLC teleport (if present)\n\n"
                f"A backup will be created.\n"
                f"Is Elden Ring closed?\n\n"
                f"Continue?"
            )
        else:
            confirm_msg = (
                f"Teleport character: {name}\n\n"
                f"No issues detected.\n"
                f"Will teleport to Limgrave (Church of Elleh)\n"
                f"to fix potential infinite loading screens.\n\n"
                f"A backup will be created.\n"
                f"Is Elden Ring closed?\n\n"
                f"Continue?"
            )
        
        if not messagebox.askyesno("Confirm Fix", confirm_msg):
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
            
            # Fix 1: Torrent Bug
            if horse and horse.has_bug():
                self.status_var.set("Fixing Torrent bug...")
                self.root.update()
                horse.fix_bug()
                slot.write_horse_data(horse)
                fixed_issues.append("Torrent bug")
            
            # Fix 2: DLC Location or Always Teleport
            has_dlc_location = map_id and map_id.is_dlc()
            
            # Always teleport if no other fixes, or if DLC location
            if has_dlc_location or not fixed_issues:
                self.status_var.set("Teleporting to Limgrave...")
                self.root.update()
                
                new_map = MapID(bytes([0, 36, 42, 60]))
                map_offset = slot.data_start + 0x4
                self.save_file.data[map_offset:map_offset+4] = new_map.to_bytes()
                
                if has_dlc_location:
                    fixed_issues.append("DLC location")
                else:
                    fixed_issues.append("Teleported to Limgrave")
            
            # Recalculate checksums
            self.status_var.set("Recalculating checksums...")
            self.root.update()
            self.save_file.recalculate_checksums()
            
            # Save
            self.status_var.set("Saving...")
            self.root.update()
            self.save_file.save()
            
            self.status_var.set("Fix complete!")
            
            issues_text = '\n'.join([f"  - {issue}" for issue in fixed_issues])
            messagebox.showinfo(
                "Success!",
                f"Character fixed: {name}\n\n"
                f"Actions taken:\n{issues_text}\n\n"
                f"Backup: {os.path.basename(backup_path)}"
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
            f"This will restore your save to the backup.\n\n"
            f"Current save will be overwritten.\n\n"
            f"Continue?"
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