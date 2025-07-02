import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import xml.etree.ElementTree as ET
import os
import re

# ============================================================================
# GLOBAL VARIABLES
# ============================================================================
xml_file_path = ""
dark_mode = True

# ============================================================================
# THEME CONFIGURATION
# ============================================================================
themes = {
    "light": {
        "bg": "#ffffff",
        "fg": "#000000",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        "frame_bg": "#e0e0e0",
        "button_bg": "#f0f0f0",
        "button_fg": "#000000"
    },
    "dark": {
        "bg": "#2b2b2b",
        "fg": "#ffffff",
        "entry_bg": "#404040",
        "entry_fg": "#ffffff",
        "frame_bg": "#404040",
        "button_bg": "#505050",
        "button_fg": "#ffffff"
    }
}

# ============================================================================
# THEME FUNCTIONS
# ============================================================================
def toggle_dark_mode():
    """Toggle between dark and light mode"""
    global dark_mode
    dark_mode = not dark_mode
    apply_theme()

def apply_theme():
    """Apply current theme to all UI elements"""
    theme = themes["dark"] if dark_mode else themes["light"]
    
    # Root window
    root.configure(bg=theme["bg"])
    
    # Frame and labels
    frame_drop.configure(bg=theme["frame_bg"], fg=theme["fg"])
    button_frame.configure(bg=theme["bg"])
    
    # Update all container frames
    for widget in root.winfo_children():
        if isinstance(widget, tk.Frame):
            widget.configure(bg=theme["bg"])
            # Update child widgets in frames
            for child in widget.winfo_children():
                if isinstance(child, tk.Label) and child != label_xml:
                    child.configure(bg=theme["bg"], fg=theme["fg"])
                elif isinstance(child, tk.Frame):
                    child.configure(bg=theme["bg"])
    
    # Update main level labels
    for widget in root.winfo_children():
        if isinstance(widget, tk.Label) and widget != frame_drop and widget != label_xml:
            widget.configure(bg=theme["bg"], fg=theme["fg"])
    
    # Special label handling
    label_xml.configure(bg=theme["bg"], fg="gray")
    
    # Text boxes
    input_box.configure(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["fg"])
    result_box.configure(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["fg"])
    
    # Buttons
    browse_btn.configure(bg=theme["button_bg"], fg=theme["button_fg"])
    dark_mode_btn.configure(text="Light Mode" if dark_mode else "Dark Mode")

# ============================================================================
# XML PROCESSING FUNCTIONS
# ============================================================================
def parse_manual_translation(text_input):
    """Parse manual translation input text into dictionary"""
    translations = {}
    lines = text_input.strip().splitlines()
    for line in lines:
        match = re.match(r"\[ID (\d+)\]\s+(.+)", line.strip())
        if match:
            entry_id, translated = match.groups()
            translations[entry_id] = translated
    return translations

def merge_translation_to_xml(xml_path, translations_dict):
    """Merge translations into XML file"""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Clean namespace
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    modified_count = 0
    modified_ids = []

    # Update entries
    for entry in root.findall(".//Entry"):
        entry_id = entry.get("Id")
        if entry_id in translations_dict:
            lines = entry.find("Lines")
            if lines is not None:
                for line in lines.findall("Line"):
                    old_text = line.get("Text")
                    if old_text is not None:
                        line.set("Text", translations_dict[entry_id])
                        modified_count += 1
                        modified_ids.append(f"[ID {entry_id}] => {translations_dict[entry_id]}")

    # Save file
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    return modified_count, xml_path, modified_ids

def extract_text_lines_from_xml():
    """Extract all text lines from XML file"""
    if not xml_file_path:
        messagebox.showwarning("Peringatan", "Pilih file XML terlebih dahulu.")
        return

    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        # Clean namespace
        for elem in root.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]

        # Extract lines
        extracted_lines = []
        for entry in root.findall(".//Entry"):
            entry_id = entry.get("Id")
            lines = entry.find("Lines")
            if lines is not None:
                for line in lines.findall("Line"):
                    text = line.get("Text")
                    if text:
                        extracted_lines.append(f"[ID {entry_id}] {text}")

        # Display results
        result_box.delete("1.0", tk.END)
        result_box.insert(tk.END, f"Berhasil mengambil {len(extracted_lines)} baris teks dari XML.\n\n")
        for line in extracted_lines:
            result_box.insert(tk.END, line + "\n")

    except Exception as e:
        messagebox.showerror("Error", str(e))

# ============================================================================
# UI EVENT HANDLERS
# ============================================================================
def browse_xml():
    """Browse and select XML file"""
    global xml_file_path
    xml_file_path = filedialog.askopenfilename(filetypes=[("XML Files", "*.xml")])
    if xml_file_path:
        label_xml.config(text=os.path.basename(xml_file_path))

def start_merge():
    """Start the translation merge process"""
    if not xml_file_path:
        messagebox.showwarning("Peringatan", "Pilih file XML terlebih dahulu.")
        return

    manual_text = input_box.get("1.0", tk.END)
    if not manual_text.strip():
        messagebox.showwarning("Peringatan", "Masukkan terjemahan manual di kotak teks.")
        return

    try:
        translations = parse_manual_translation(manual_text)
        count, output_file, updated = merge_translation_to_xml(xml_file_path, translations)
        messagebox.showinfo("Sukses", f"{count} baris berhasil diperbarui.\nFile ditimpa: {output_file}")
        
        # Display results
        result_box.delete("1.0", tk.END)
        result_box.insert(tk.END, f"File ditulis ulang: {output_file}\n")
        result_box.insert(tk.END, f"Total diterjemahkan: {count} baris\n\n")
        for line in updated:
            result_box.insert(tk.END, line + "\n")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def copy_result_to_clipboard():
    """Copy result text to clipboard"""
    result = result_box.get("1.0", tk.END)
    if not result.strip():
        messagebox.showwarning("Peringatan", "Tidak ada teks untuk disalin.")
        return
    root.clipboard_clear()
    root.clipboard_append(result.strip())
    root.update()
    messagebox.showinfo("Disalin", "Hasil telah disalin ke clipboard.")

def on_drop(event):
    """Handle drag and drop file event"""
    global xml_file_path
    dropped_files = root.tk.splitlist(event.data)
    if dropped_files:
        xml_file_path = dropped_files[0]
        if not xml_file_path.lower().endswith(".xml"):
            messagebox.showwarning("File Tidak Valid", "Hanya file XML yang didukung.")
            return
        label_xml.config(text=os.path.basename(xml_file_path))
        messagebox.showinfo("Berhasil", f"File dimuat: {os.path.basename(xml_file_path)}")

# ============================================================================
# GUI SETUP FUNCTIONS
# ============================================================================
def setup_drag_drop():
    """Setup drag and drop functionality"""
    try:
        import tkinterdnd2 as tkdnd
        root_window = tkdnd.TkinterDnD.Tk()
        dnd_available = True
    except ImportError:
        root_window = tk.Tk()
        dnd_available = False
        messagebox.showwarning("Perhatian", "tkinterdnd2 tidak ditemukan.\nFitur drag & drop dinonaktifkan.")
    
    return root_window, dnd_available

def create_widgets():
    """Create all GUI widgets"""
    global frame_drop, label_xml, input_box, result_box, button_frame
    global browse_btn, merge_btn, extract_btn, copy_btn, dark_mode_btn
    
    # Configure root window for responsive resizing
    root.geometry("900x800")  # Set initial size
    root.minsize(400, 600)    # Set minimum size (width, height)
    root.maxsize(1400, 1200)  # Set maximum size (width, height)
    
    # Configure root grid weights for vertical expansion
    root.grid_rowconfigure(0, weight=0)  # Dark mode button - fixed
    root.grid_rowconfigure(1, weight=0)  # Drag drop area - fixed
    root.grid_rowconfigure(2, weight=0)  # File selection - fixed
    root.grid_rowconfigure(3, weight=1)  # Input box - expandable
    root.grid_rowconfigure(4, weight=0)  # Buttons - fixed
    root.grid_rowconfigure(5, weight=2)  # Result box - more expandable
    root.grid_columnconfigure(0, weight=1)  # Full width
    
    # Title
    root.title("Input Manual Terjemahan & Timpa XML")
    
    # Dark mode toggle
    dark_mode_btn = tk.Button(root, text="Light Mode", command=toggle_dark_mode, 
                             bg="#333333", fg="white", width=15, height=1)
    dark_mode_btn.grid(row=0, column=0, pady=5)
    
    # Drag & drop area
    frame_drop = tk.Label(root, text="(Atau drag & drop file XML ke sini)", 
                         bg="#e0e0e0", relief="groove", padx=10, pady=10)
    frame_drop.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
    
    # File selection section container
    file_section = tk.Frame(root)
    file_section.grid(row=2, column=0, pady=5)
    
    tk.Label(file_section, text="1. Pilih File XML Asli", font=("Arial", 10, "bold")).pack(pady=5)
    browse_btn = tk.Button(file_section, text="Pilih File XML", command=browse_xml, width=20, height=1)
    browse_btn.pack()
    label_xml = tk.Label(file_section, text="Belum dipilih", fg="gray")
    label_xml.pack()
    
    # Translation input section container
    input_section = tk.Frame(root)
    input_section.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
    input_section.grid_rowconfigure(1, weight=1)
    input_section.grid_columnconfigure(0, weight=1)
    
    tk.Label(input_section, text="2. Masukkan Terjemahan Manual", font=("Arial", 10, "bold")).grid(row=0, column=0, pady=(0, 8))
    input_box = scrolledtext.ScrolledText(input_section, width=80, height=8, wrap=tk.WORD)
    input_box.grid(row=1, column=0, sticky="nsew")
    input_box.insert(tk.END, "[ID 600831] Tembakan lengan.\n[ID 7158447] Mode Senjata.")
    
    # Buttons section container
    buttons_section = tk.Frame(root)
    buttons_section.grid(row=4, column=0, pady=10)
    
    # Main action button
    merge_btn = tk.Button(buttons_section, text="Gabungkan & Timpa File XML", command=start_merge, 
                         bg="#f44336", fg="white", width=40, height=2)
    merge_btn.pack(pady=(0, 10))
    
    # Secondary buttons frame
    button_frame = tk.Frame(buttons_section)
    button_frame.pack()
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)
    
    extract_btn = tk.Button(button_frame, text="Ekstrak Semua Teks dari XML", 
                           command=extract_text_lines_from_xml, bg="#2196F3", fg="white", 
                           width=35, height=2)
    extract_btn.grid(row=0, column=0, padx=5, sticky="ew")
    
    copy_btn = tk.Button(button_frame, text="Salin Hasil ke Clipboard", 
                        command=copy_result_to_clipboard, bg="#4CAF50", fg="white", 
                        width=35, height=2)
    copy_btn.grid(row=0, column=1, padx=5, sticky="ew")
    
    # Result display section
    result_section = tk.Frame(root)
    result_section.grid(row=5, column=0, sticky="nsew", padx=10, pady=5)
    result_section.grid_rowconfigure(0, weight=1)
    result_section.grid_columnconfigure(0, weight=1)
    
    result_box = scrolledtext.ScrolledText(result_section, width=90, height=12, wrap=tk.WORD)
    result_box.grid(row=0, column=0, sticky="nsew")

def setup_drag_drop_events(dnd_available):
    """Setup drag and drop events if available"""
    if dnd_available:
        import tkinterdnd2 as tkdnd
        frame_drop.drop_target_register(tkdnd.DND_FILES)
        frame_drop.dnd_bind("<<Drop>>", on_drop)

# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    """Main application function"""
    global root
    
    # Setup root window and drag & drop
    root, dnd_available = setup_drag_drop()
    
    # Create all widgets
    create_widgets()
    
    # Setup drag & drop events
    setup_drag_drop_events(dnd_available)
    
    # Apply initial theme
    apply_theme()
    
    # Start main loop
    root.mainloop()

if __name__ == "__main__":
    main()
