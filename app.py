import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path

import pygame

from services.tts_manager import generate_audio as create_audio
from services.audio_library import (
    OUTPUT_DIR,
    list_audio_files,
    rename_audio_file,
    delete_audio_file,
)

# =========================================================
# AI VOICE STUDIO - DARK PROFESSIONAL UI
# Keep the existing TTS and audio-library services.
# =========================================================
root = tk.Tk()
root.title("AI Voice Studio")
root.geometry("1280x850")
root.minsize(1080, 720)
root.configure(bg="#0B1020")

C = {
    "bg": "#0B1020",
    "sidebar": "#0E1629",
    "panel": "#121C31",
    "panel2": "#17243B",
    "input": "#0D172A",
    "border": "#263650",
    "text": "#F1F5F9",
    "muted": "#91A0B8",
    "blue": "#548BFF",
    "blue_hover": "#3975F2",
    "purple": "#9B8CFF",
    "green": "#35C995",
    "red": "#FF6B78",
    "white": "#FFFFFF",
}
FONT = "Segoe UI"

style = ttk.Style()
style.theme_use("clam")
style.configure(
    "Dark.TCombobox",
    fieldbackground=C["input"],
    background=C["panel2"],
    foreground=C["text"],
    arrowcolor=C["muted"],
    bordercolor=C["border"],
    lightcolor=C["border"],
    darkcolor=C["border"],
    padding=9,
    font=(FONT, 10),
)
style.map(
    "Dark.TCombobox",
    fieldbackground=[("readonly", C["input"])],
    foreground=[("readonly", C["text"])],
    selectbackground=[("readonly", C["input"])],
    selectforeground=[("readonly", C["text"])],
)
style.configure(
    "Dark.Vertical.TScrollbar",
    background=C["panel2"],
    troughcolor=C["input"],
    bordercolor=C["input"],
    arrowcolor=C["muted"],
)
style.configure(
    "Dark.Horizontal.TProgressbar",
    troughcolor=C["input"],
    background=C["blue"],
    bordercolor=C["input"],
    lightcolor=C["blue"],
    darkcolor=C["blue"],
)

def label(parent, text, size=10, color=None, bold=False, **kwargs):
    return tk.Label(
        parent, text=text, font=(FONT, size, "bold" if bold else "normal"),
        fg=color or C["text"], bg=kwargs.pop("bg", C["panel"]), **kwargs
    )

def card(parent, **kwargs):
    return tk.Frame(
        parent, bg=C["panel"], highlightbackground=C["border"],
        highlightthickness=1, bd=0, **kwargs
    )

def action_button(parent, text, command, primary=False, compact=False):
    bg = C["blue"] if primary else C["panel2"]
    active = C["blue_hover"] if primary else "#223452"
    fg = C["white"] if primary else C["text"]
    return tk.Button(
        parent, text=text, command=command, font=(FONT, 9, "bold" if primary else "normal"),
        bg=bg, fg=fg, activebackground=active, activeforeground=C["white"],
        relief="flat", bd=0, cursor="hand2",
        padx=12 if compact else 16, pady=8 if compact else 11,
    )

# Main layout
sidebar = tk.Frame(root, bg=C["sidebar"], width=218)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

brand = tk.Frame(sidebar, bg=C["sidebar"], padx=22, pady=24)
brand.pack(fill="x")
brand_mark = tk.Label(
    brand, text="AI", font=(FONT, 15, "bold"), fg=C["white"],
    bg=C["blue"], width=3, height=1, pady=7
)
brand_mark.pack(side="left")
brand_text = tk.Frame(brand, bg=C["sidebar"])
brand_text.pack(side="left", padx=10)
label(brand_text, "VOICE STUDIO", 12, C["text"], True, bg=C["sidebar"]).pack(anchor="w")
label(brand_text, "CREATIVE WORKSPACE", 7, C["muted"], True, bg=C["sidebar"]).pack(anchor="w", pady=(3, 0))

label(sidebar, "WORKSPACE", 8, C["muted"], True, bg=C["sidebar"]).pack(anchor="w", padx=22, pady=(24, 10))
nav_items = [
    ("▣", "Voice Studio", True),
    ("♫", "Audio Library", False),
]
for symbol, name, active in nav_items:
    row = tk.Frame(sidebar, bg="#1B2B49" if active else C["sidebar"], padx=16, pady=12)
    row.pack(fill="x", padx=12, pady=3)
    label(row, symbol, 13, C["blue"] if active else C["muted"], True, bg=row["bg"]).pack(side="left")
    label(row, name, 10, C["text"] if active else C["muted"], active, bg=row["bg"]).pack(side="left", padx=12)

sidebar_bottom = tk.Frame(sidebar, bg=C["sidebar"], padx=20, pady=18)
sidebar_bottom.pack(side="bottom", fill="x")
tk.Frame(sidebar_bottom, bg=C["border"], height=1).pack(fill="x", pady=(0, 14))
label(sidebar_bottom, "LOCAL WORKSPACE", 8, C["muted"], True, bg=C["sidebar"]).pack(anchor="w")
label(sidebar_bottom, "Your audio stays on this device", 8, C["muted"], bg=C["sidebar"]).pack(anchor="w", pady=(5, 0))

# Right side workspace: top bar + content
workspace = tk.Frame(root, bg=C["bg"])
workspace.pack(side="left", fill="both", expand=True)

topbar = tk.Frame(workspace, bg=C["bg"], padx=28, pady=20)
topbar.pack(fill="x")
top_left = tk.Frame(topbar, bg=C["bg"])
top_left.pack(side="left", fill="x", expand=True)
label(top_left, "Voice Studio", 20, C["text"], True, bg=C["bg"]).pack(anchor="w")
label(top_left, "Transform your text into natural-sounding speech.", 9, C["muted"], bg=C["bg"]).pack(anchor="w", pady=(4, 0))
tk.Label(topbar, text="●  ENGINE READY", font=(FONT, 8, "bold"), fg=C["green"],
         bg="#12352F", padx=12, pady=8).pack(side="right", anchor="center")

content = tk.Frame(workspace, bg=C["bg"], padx=24, pady=(0, 22))
content.pack(fill="both", expand=True)
content.columnconfigure(0, weight=1)
content.columnconfigure(1, weight=0)
content.rowconfigure(0, weight=3)
content.rowconfigure(1, weight=2)

# Editor card
editor_card = card(content, padx=18, pady=16)
editor_card.grid(row=0, column=0, sticky="nsew", padx=(0, 14), pady=(0, 14))
editor_header = tk.Frame(editor_card, bg=C["panel"])
editor_header.pack(fill="x")
label(editor_header, "SCRIPT EDITOR", 9, C["muted"], True).pack(side="left")
label(editor_header, "TEXT INPUT", 8, C["purple"], True, bg="#282447", padx=9, pady=5).pack(side="right")
label(editor_card, "What would you like to say?", 15, C["text"], True).pack(anchor="w", pady=(17, 5))
label(editor_card, "Paste or type your script below. Choose a voice and generate your audio.", 9, C["muted"]).pack(anchor="w", pady=(0, 13))

text_wrap = tk.Frame(editor_card, bg=C["input"], highlightbackground=C["border"], highlightthickness=1)
text_wrap.pack(fill="both", expand=True)
text_input = tk.Text(
    text_wrap, height=10, wrap="word", undo=True, relief="flat", bd=0,
    bg=C["input"], fg=C["text"], insertbackground=C["blue"],
    selectbackground="#294A7B", font=(FONT, 11), padx=14, pady=13,
)
text_input.pack(side="left", fill="both", expand=True)
text_scroll = ttk.Scrollbar(text_wrap, orient="vertical", command=text_input.yview, style="Dark.Vertical.TScrollbar")
text_scroll.pack(side="right", fill="y")
text_input.configure(yscrollcommand=text_scroll.set)

editor_footer = tk.Frame(editor_card, bg=C["panel"])
editor_footer.pack(fill="x", pady=(10, 0))
char_count = label(editor_footer, "0 characters", 8, C["muted"])
char_count.pack(side="left")
label(editor_footer, "Supports Vietnamese and English", 8, C["muted"]).pack(side="right")

def update_char_count(event=None):
    count = len(text_input.get("1.0", "end-1c"))
    char_count.config(text=f"{count:,} characters")
text_input.bind("<KeyRelease>", update_char_count)

# Voice settings panel
settings_card = card(content, width=286, padx=17, pady=16)
settings_card.grid(row=0, column=1, sticky="nsew", pady=(0, 14))
settings_card.grid_propagate(False)
label(settings_card, "VOICE SETTINGS", 9, C["muted"], True).pack(anchor="w")
label(settings_card, "Configure your output", 14, C["text"], True).pack(anchor="w", pady=(14, 17))

label(settings_card, "LANGUAGE", 8, C["muted"], True).pack(anchor="w", pady=(0, 7))
language_options = ttk.Combobox(
    settings_card, values=["Tự động nhận diện", "Tiếng Việt", "English"],
    state="readonly", style="Dark.TCombobox"
)
language_options.current(0)
language_options.pack(fill="x", pady=(0, 16))

label(settings_card, "VOICE", 8, C["muted"], True).pack(anchor="w", pady=(0, 7))
voice_options = ttk.Combobox(
    settings_card, values=["Tự động theo ngôn ngữ", "Diễm Trinh", "af_heart"],
    state="readonly", style="Dark.TCombobox"
)
voice_options.current(0)
voice_options.pack(fill="x", pady=(0, 7))
label(settings_card, "Auto voice selects a matching voice for the detected language.", 8, C["muted"], wraplength=245, justify="left").pack(anchor="w", pady=(0, 17))

tk.Frame(settings_card, bg=C["border"], height=1).pack(fill="x", pady=(0, 15))
label(settings_card, "OUTPUT FILE NAME", 8, C["muted"], True).pack(anchor="w", pady=(0, 7))
filename_input = tk.Entry(
    settings_card, font=(FONT, 10), relief="flat", bd=0,
    bg=C["input"], fg=C["text"], insertbackground=C["blue"],
    highlightthickness=1, highlightbackground=C["border"],
    highlightcolor=C["blue"]
)
filename_input.insert(0, "ban_ghi_moi")
filename_input.pack(fill="x", ipady=10)
label(settings_card, "File format: WAV", 8, C["muted"]).pack(anchor="w", pady=(7, 0))

# Generate controls and status
generate_area = tk.Frame(settings_card, bg=C["panel"])
generate_area.pack(side="bottom", fill="x", pady=(18, 0))
status = label(generate_area, "Ready to generate", 8, C["muted"], wraplength=245, justify="left")
status.pack(anchor="w", pady=(0, 9))
progress_bar = ttk.Progressbar(generate_area, mode="indeterminate", style="Dark.Horizontal.TProgressbar")
progress_bar.pack(fill="x", pady=(0, 10))

# Library card
library_card = card(content, padx=18, pady=14)
library_card.grid(row=1, column=0, columnspan=2, sticky="nsew")
library_header = tk.Frame(library_card, bg=C["panel"])
library_header.pack(fill="x", pady=(0, 11))
library_title_box = tk.Frame(library_header, bg=C["panel"])
library_title_box.pack(side="left", fill="x", expand=True)
label(library_title_box, "Audio Library", 13, C["text"], True).pack(anchor="w")
label(library_title_box, "Your generated recordings", 8, C["muted"]).pack(anchor="w", pady=(3, 0))
label(library_header, "WAV FILES", 8, C["purple"], True, bg="#282447", padx=9, pady=5).pack(side="right")

list_frame = tk.Frame(library_card, bg=C["input"], highlightbackground=C["border"], highlightthickness=1)
list_frame.pack(fill="both", expand=True)
audio_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", style="Dark.Vertical.TScrollbar")
audio_list = tk.Listbox(
    list_frame, height=5, font=(FONT, 9), activestyle="none",
    relief="flat", bd=0, highlightthickness=0, bg=C["input"],
    fg=C["text"], selectbackground="#294A7B", selectforeground=C["white"],
    yscrollcommand=audio_scrollbar.set, selectmode=tk.SINGLE,
)
audio_scrollbar.config(command=audio_list.yview)
audio_scrollbar.pack(side="right", fill="y")
audio_list.pack(side="left", fill="both", expand=True, padx=7, pady=5)

def update_status(message, color=None):
    status.config(text=message, fg=color or C["muted"])

def refresh_audio_list(select_path=None):
    audio_list.delete(0, tk.END)
    files = list_audio_files()
    for file_path in files:
        audio_list.insert(tk.END, f"♫   {file_path.name}")
    if select_path:
        selected_path = Path(select_path)
        for index, file_path in enumerate(files):
            if file_path == selected_path:
                audio_list.selection_set(index)
                audio_list.activate(index)
                audio_list.see(index)
                break
    if not files:
        audio_list.insert(tk.END, "   No recordings yet")
    return files

def get_selected_audio():
    selection = audio_list.curselection()
    if not selection:
        messagebox.showinfo("Audio Library", "Please select a recording first.")
        return None
    selected = audio_list.get(selection[0]).replace("♫   ", "", 1)
    if selected == "No recordings yet":
        return None
    return OUTPUT_DIR / selected

def stop_playback(show_status=False):
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except pygame.error:
        pass
    if show_status:
        update_status("Playback stopped.")

def play_selected_audio():
    file_path = get_selected_audio()
    if file_path is None:
        return
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(str(file_path))
        pygame.mixer.music.play()
        update_status(f"Playing: {file_path.name}", C["green"])
    except (pygame.error, OSError) as error:
        messagebox.showerror("Playback error", str(error))
        update_status("Unable to play recording.", C["red"])

def rename_selected_audio():
    file_path = get_selected_audio()
    if file_path is None:
        return
    new_name = simpledialog.askstring(
        "Rename recording", "Enter a new name (without .wav):",
        initialvalue=file_path.stem, parent=root
    )
    if new_name is None:
        return
    try:
        stop_playback()
        renamed_path = rename_audio_file(file_path, new_name)
        refresh_audio_list(renamed_path)
        update_status(f"Renamed: {renamed_path.name}", C["green"])
    except (ValueError, FileExistsError, FileNotFoundError, OSError) as error:
        messagebox.showerror("Rename failed", str(error))
        update_status("Rename failed.", C["red"])

def delete_selected_audio():
    file_path = get_selected_audio()
    if file_path is None:
        return
    if not messagebox.askyesno("Delete recording", f"Delete '{file_path.name}'?", parent=root):
        return
    try:
        stop_playback()
        delete_audio_file(file_path)
        refresh_audio_list()
        update_status(f"Deleted: {file_path.name}", C["green"])
    except (ValueError, FileNotFoundError, OSError) as error:
        messagebox.showerror("Delete failed", str(error))
        update_status("Delete failed.", C["red"])

def open_output_folder():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if os.name == "nt":
            os.startfile(str(OUTPUT_DIR))
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(OUTPUT_DIR)])
    except OSError as error:
        messagebox.showerror("Cannot open folder", str(error))

library_actions = tk.Frame(library_card, bg=C["panel"])
library_actions.pack(fill="x", pady=(10, 0))
action_button(library_actions, "▶  Play", play_selected_audio, primary=True, compact=True).pack(side="left", padx=(0, 6))
action_button(library_actions, "■  Stop", lambda: stop_playback(True), compact=True).pack(side="left", padx=3)
action_button(library_actions, "Rename", rename_selected_audio, compact=True).pack(side="left", padx=3)
action_button(library_actions, "Delete", delete_selected_audio, compact=True).pack(side="left", padx=3)
action_button(library_actions, "Refresh", refresh_audio_list, compact=True).pack(side="left", padx=3)
action_button(library_actions, "Open folder", open_output_folder, compact=True).pack(side="right")
audio_list.bind("<Double-Button-1>", lambda event: play_selected_audio())

def on_success(file_path):
    progress_bar.stop()
    refresh_audio_list(file_path)
    update_status(f"Created successfully: {file_path.name}", C["green"])
    generate_button.config(state="normal")

def on_error(error_message):
    progress_bar.stop()
    update_status(f"Error: {error_message}", C["red"])
    generate_button.config(state="normal")
    messagebox.showerror("Unable to generate speech", error_message)

def generate_audio_worker(content, language, voice, file_name):
    try:
        language_map = {
            "Tự động nhận diện": "auto",
            "Tiếng Việt": "vi",
            "English": "en",
        }
        voice_map = {
            "Tự động theo ngôn ngữ": "auto",
            "Diễm Trinh": "diem_trinh",
            "af_heart": "af_heart",
        }
        file_path = create_audio(
            text=content,
            language=language_map[language],
            voice=voice_map[voice],
            speed=1.0,
            file_name=file_name,
        )
        root.after(0, lambda: on_success(file_path))
    except Exception as error:
        error_message = str(error)
        root.after(0, lambda: on_error(error_message))

def generate_audio():
    content = text_input.get("1.0", "end-1c").strip()
    language = language_options.get()
    voice = voice_options.get()
    file_name = filename_input.get().strip() or "ban_ghi_moi"
    if not content:
        update_status("Please enter some text first.", C["red"])
        text_input.focus_set()
        return
    if not language or not voice:
        update_status("Choose a language and voice.", C["red"])
        return
    generate_button.config(state="disabled")
    progress_bar.start(12)
    update_status("Generating your voice...", C["blue"])
    threading.Thread(
        target=generate_audio_worker,
        args=(content, language, voice, file_name),
        daemon=True,
    ).start()

generate_button = action_button(settings_card, "▶   GENERATE AUDIO", generate_audio, primary=True)
generate_button.pack(side="bottom", fill="x", pady=(12, 0))

refresh_audio_list()

def close_application():
    stop_playback()
    progress_bar.stop()
    try:
        pygame.mixer.quit()
    except pygame.error:
        pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close_application)
root.mainloop()
