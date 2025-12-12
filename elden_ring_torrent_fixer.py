"""
Elden Ring - Torrent State Fixer (GUI Version)
Fixes the loading screen freeze caused by Torrent being Active with 0 HP
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import struct
import os
import shutil
import hashlib
from pathlib import Path

class TorrentStateFixer:
    def __init__(self, root):
        self.root = root
        self.root.title("Elden Ring - Torrent State Fixer")
        self.root.geometry("700x550")
        self.root.resizable(False, False)
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Default save location for Elden Ring
        self.default_save_path = Path(os.environ.get('APPDATA', '')) / "EldenRing"
        
        self.HEADER_SIZE = 0x300
        self.CHARACTER_FILE_SIZE = 0x280000
        self.CHECKSUM_SIZE = 0x10
        self.USERDATA_10_SIZE = 0x60000
        self.MAX_CHARACTER_COUNT = 10
        self.ACTIVE_SLOTS_OFFSET = 0x1901D04
        
        self.setup_ui()
        
    def setup_ui(self):
        # Title Section
        title_frame = ttk.Frame(self.root, padding="15")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame, 
            text="Elden Ring Torrent State Fixer",
            font=('Segoe UI', 18, 'bold')
        )
        title_label.pack()
        
        subtitle = ttk.Label(
            title_frame,
            text="Fix the stuck loading screen bug",
            font=('Segoe UI', 10)
        )
        subtitle.pack()
        
        # Info Panel
        info_frame = ttk.LabelFrame(self.root, text="How It Works", padding="15")
        info_frame.pack(fill=tk.X, padx=15, pady=10)
        
        info_text = """Works with: Standard saves (.sl2) and Seamless Co-op saves (.co2)"""
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT, wraplength=650)
        info_label.pack()
        
        # File Selection
        file_frame = ttk.LabelFrame(self.root, text="Select Save File", padding="15")
        file_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.file_path_var = tk.StringVar()
        
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X)
        
        ttk.Label(path_frame, text="File:", font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        
        file_entry = ttk.Entry(path_frame, textvariable=self.file_path_var, width=50)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        btn_frame = ttk.Frame(path_frame)
        btn_frame.pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="Browse", command=self.browse_file, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Auto-Find", command=self.auto_detect, width=10).pack(side=tk.LEFT, padx=2)
        
        # Action Buttons
        action_frame = ttk.Frame(self.root, padding="15")
        action_frame.pack(fill=tk.X)
        
        self.fix_button = ttk.Button(
            action_frame,
            text="Fix Torrent State",
            command=self.fix_save,
            width=25
        )
        self.fix_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="Restore Backup",
            command=self.restore_backup,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="Clear Log",
            command=self.clear_log,
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        # Log Output
        log_frame = ttk.LabelFrame(self.root, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            width=80,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Status Bar
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2)
        )
        status_bar.pack(fill=tk.X)
        
        # Initial log message
        self.log("Welcome! Select your save file and click 'Fix Torrent State'")
        self.log("WARNING: Make sure Elden Ring is CLOSED before fixing!\n")
    
    def log(self, message, color=None):
        """Add message to log"""
        self.log_text.insert(tk.END, message + "\n")
        if color:
            pass
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.delete(1.0, tk.END)
    
    def browse_file(self):
        """Browse for save file"""
        filename = filedialog.askopenfilename(
            title="Select Elden Ring Save File",
            initialdir=self.default_save_path,
            filetypes=[
                ("Elden Ring Saves", ".sl2 .co2"),
                ("Standard Save", ".sl2"),
                ("Seamless Co-op Save", ".co2"),
                ("All files", ".*")
            ]
        )
        if filename:
            self.file_path_var.set(filename)
            self.log(f"Selected: {os.path.basename(filename)}")
            self.status_var.set(f"File selected: {os.path.basename(filename)}")
    
    def auto_detect(self):
        """Auto-detect save files"""
        if not self.default_save_path.exists():
            messagebox.showerror(
                "Not Found",
                f"Elden Ring save folder not found:\n{self.default_save_path}"
            )
            return
        
        # Find save files
        saves = list(self.default_save_path.rglob("ER*.sl2")) + \
                list(self.default_save_path.rglob("ER*.co2"))
        
        if not saves:
            messagebox.showwarning(
                "Not Found",
                "No Elden Ring save files found.\nPlease select manually."
            )
            return
        
        if len(saves) == 1:
            # Only one save found
            self.file_path_var.set(str(saves[0]))
            self.log(f"Auto-detected: {saves[0].name}")
            self.status_var.set("Save file auto-detected")
        else:
            # Multiple saves - show selection dialog
            self.show_save_selector(saves)
    
    def show_save_selector(self, saves):
        """Show dialog to select from multiple saves"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Save File")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(
            dialog,
            text=f"Found {len(saves)} save files. Select one:",
            font=('Segoe UI', 10, 'bold'),
            padding=10
        ).pack()
        
        listbox_frame = ttk.Frame(dialog, padding=10)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(
            listbox_frame,
            yscrollcommand=scrollbar.set,
            font=('Consolas', 9)
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for save in saves:
            listbox.insert(tk.END, str(save))
        
        def select_save():
            selection = listbox.curselection()
            if selection:
                self.file_path_var.set(str(saves[selection[0]]))
                self.log(f"Selected: {saves[selection[0]].name}")
                dialog.destroy()
        
        ttk.Button(
            dialog,
            text="Select",
            command=select_save
        ).pack(pady=10)
        
        listbox.bind('<Double-Button-1>', lambda e: select_save())
    
    def recalculate_checksums(self, data):
        """
        Recalculate MD5 checksums for character slots and USER_DATA_10
        Based on the 010 Editor script by ClayAmore
        """
        try:
            # Count active slots
            slots_count = 0
            for i in range(10):
                if data[self.ACTIVE_SLOTS_OFFSET + i] == 1:
                    slots_count += 1
            
            self.log(f"   Found {slots_count} active character slot(s)")
            
            # Recalculate checksum for each active character slot
            for i in range(slots_count):
                # Calculate offset to start of character (skipping checksum bytes)
                offset = self.HEADER_SIZE + ((self.CHARACTER_FILE_SIZE + self.CHECKSUM_SIZE) * i)
                
                # Read character data (skip the 16-byte checksum at the start)
                char_data_start = offset + self.CHECKSUM_SIZE
                char_data = data[char_data_start:char_data_start + self.CHARACTER_FILE_SIZE]
                
                # Calculate MD5 checksum
                md5_hash = hashlib.md5(char_data).digest()
                
                # Write new checksum at the offset (before character data)
                data[offset:offset + self.CHECKSUM_SIZE] = md5_hash
                
                self.log(f"   [OK] Updated checksum for character slot {i + 1}")
            
            # Recalculate checksum for USER_DATA_10
            offset = self.HEADER_SIZE + (self.CHARACTER_FILE_SIZE * self.MAX_CHARACTER_COUNT)
            userdata_start = offset + self.CHECKSUM_SIZE
            userdata = data[userdata_start:userdata_start + self.USERDATA_10_SIZE]
            
            # Calculate MD5 checksum for USER_DATA_10
            md5_hash = hashlib.md5(userdata).digest()
            
            # Write new checksum
            data[offset:offset + self.CHECKSUM_SIZE] = md5_hash
            
            self.log(f"   [OK] Updated checksum for USER_DATA_10")
            
            return True
            
        except Exception as e:
            self.log(f"   [ERROR] Checksum calculation failed: {str(e)}")
            return False
    
    def fix_save(self):
        """Main fix function"""
        save_path = self.file_path_var.get()
        
        if not save_path or not os.path.exists(save_path):
            messagebox.showerror("Error", "Please select a valid save file first!")
            return
        
        # Confirm
        if not messagebox.askyesno(
            "Confirm",
            "This will modify your save file.\n"
            "A backup will be created automatically next to your original save file.\n\n"
            "Is Elden Ring closed?\n\n"
            "Continue?"
        ):
            return
        
        self.clear_log()
        self.log("="*70)
        self.log("STARTING FIX PROCESS")
        self.log("="*70)
        self.status_var.set("Processing...")
        self.fix_button.config(state=tk.DISABLED)
        
        try:
            # Create backup
            backup_path = save_path + ".backup"
            self.log(f"\nCreating backup...")
            self.log(f"Backup: {os.path.basename(backup_path)}")
            shutil.copy2(save_path, backup_path)
            self.log("[OK] Backup created successfully")
            
            # Read file
            self.log(f"\nReading save file...")
            with open(save_path, 'rb') as f:
                data = bytearray(f.read())
            
            self.log(f"Loaded {len(data):,} bytes")
            
            # Search for pattern
            self.log("\nSearching for Torrent state issues...")
            self.log("   Pattern: HP=0 (4 bytes) + State=13 (4 bytes)")
            
            fixes = []
            
            for i in range(len(data) - 8):
                try:
                    hp = struct.unpack('<I', data[i:i+4])[0]
                    state = struct.unpack('<I', data[i+4:i+8])[0]
                    
                    if hp == 0 and state == 13:
                        self.log(f"\n   [!] Found at offset 0x{i:08X}")
                        self.log(f"       HP={hp}, State={state} (Active)")
                        
                        # Fix: Change state from 13 to 3
                        data[i+4] = 0x03
                        data[i+5] = 0x00
                        data[i+6] = 0x00
                        data[i+7] = 0x00
                        
                        fixes.append(i)
                        self.log(f"   [OK] Changed State: Active (13) -> Dead (3)")
                
                except (struct.error, IndexError):
                    pass
            
            if not fixes:
                self.log("\n[OK] No issues found!")
                self.log("   Your save file is already fine.")
                messagebox.showinfo(
                    "No Issues Found",
                    "Your save doesn't have the Torrent state bug.\n"
                    "A backup was created for safety."
                )
                self.status_var.set("No issues detected")
                self.fix_button.config(state=tk.NORMAL)
                return
            
            self.log(f"\nFixed {len(fixes)} issue(s)")
            
            # Recalculate checksums
            self.log("\n" + "="*70)
            self.log("RECALCULATING CHECKSUMS")
            self.log("="*70)
            
            if not self.recalculate_checksums(data):
                raise Exception("Checksum recalculation failed")
            
            # Write changes with updated checksums
            self.log(f"\nWriting fixed save file...")
            with open(save_path, 'wb') as f:
                bytes_written = f.write(data)
                f.flush()
                os.fsync(f.fileno())
            
            self.log(f"Wrote {bytes_written:,} bytes")
            
            # Verify
            self.log("\n" + "="*70)
            self.log("VERIFYING CHANGES")
            self.log("="*70)
            
            with open(save_path, 'rb') as f:
                verify_data = bytearray(f.read())
            
            all_verified = True
            for offset in fixes:
                hp = struct.unpack('<I', verify_data[offset:offset+4])[0]
                state = struct.unpack('<I', verify_data[offset+4:offset+8])[0]
                
                if state == 3:
                    self.log(f"   [OK] Offset 0x{offset:08X}: HP={hp}, State=Dead (3)")
                else:
                    self.log(f"   [FAIL] Offset 0x{offset:08X}: State={state} (should be 3)")
                    all_verified = False
            
            
            self.log("\n" + "="*70)
            if all_verified:
                self.log("SUCCESS! All fixes verified!")
                self.log(f"Fixed {len(fixes)} issue(s)")
                self.log(f"Checksums recalculated successfully")
                self.log(f"Backup: {os.path.basename(backup_path)}")
                self.log("="*70)
                
                messagebox.showinfo(
                    "Success!",
                    f"Torrent state fixed successfully!\n\n"
                    f"Fixed {len(fixes)} issue(s)\n"
                    f"Checksums updated\n\n"
                    f"Backup saved:\n{os.path.basename(backup_path)}\n\n"
                    f"You can now load your save in Elden Ring!"
                )
                self.status_var.set(f"Fixed {len(fixes)} issue(s)")
            else:
                self.log("WARNING: Some verifications failed")
                self.log("="*70)
                messagebox.showwarning(
                    "Partial Success",
                    "Some changes may not have been saved properly.\n"
                    "Check the log for details."
                )
                self.status_var.set("Partial success")
        
        except Exception as e:
            self.log(f"\nERROR: {str(e)}")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
            self.status_var.set("Error occurred")
            import traceback
            traceback.print_exc()
        
        finally:
            self.fix_button.config(state=tk.NORMAL)
    
    def restore_backup(self):
        """Restore from backup"""
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
                self.log("\n[OK] Backup restored successfully!")
                messagebox.showinfo("Success", "Backup restored successfully!")
                self.status_var.set("Backup restored")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restore backup:\n{str(e)}")

def main():
    root = tk.Tk()
    app = TorrentStateFixer(root)
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()
