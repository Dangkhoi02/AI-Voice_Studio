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


root = tk.Tk()
root.title("AI Voice Studio")
root.geometry("950x820")
root.minsize(760, 700)


title = tk.Label(root, text="AI VOICE STUDIO", font=("Arial", 24, "bold"))
title.pack(pady=(18, 4))

subtitle = tk.Label(
    root,
    text="Cong cu chuyen van ban thanh giong noi AI",
    font=("Arial", 11)
)
subtitle.pack()


input_frame = tk.LabelFrame(root, text="Noi dung", font=("Arial", 11, "bold"), padx=12, pady=10)
input_frame.pack(fill="x", padx=24, pady=(18, 8))

text_input = tk.Text(input_frame, height=8, font=("Arial", 12), wrap="word")
text_input.pack(fill="x")


options_frame = tk.Frame(root)
options_frame.pack(fill="x", padx=24, pady=6)
options_frame.columnconfigure(1, weight=1)
options_frame.columnconfigure(3, weight=1)

tk.Label(options_frame, text="Ngon ngu:", font=("Arial", 10, "bold")).grid(
    row=0, column=0, sticky="w", padx=(0, 8), pady=5
)
language_options = ttk.Combobox(
    options_frame,
    values=["Tu dong nhan dien", "Tieng Viet", "English"],
    state="readonly",
    width=24
)
language_options.current(0)
language_options.grid(row=0, column=1, sticky="ew", padx=(0, 18), pady=5)

tk.Label(options_frame, text="Giong doc:", font=("Arial", 10, "bold")).grid(
    row=0, column=2, sticky="w", padx=(0, 8), pady=5
)
voice_options = ttk.Combobox(
    options_frame,
    values=["Tu dong theo ngon ngu", "Diem Trinh", "af_heart"],
    state="readonly",
    width=24
)
voice_options.current(0)
voice_options.grid(row=0, column=3, sticky="ew", pady=5)

tk.Label(options_frame, text="Ten file:", font=("Arial", 10, "bold")).grid(
    row=1, column=0, sticky="w", padx=(0, 8), pady=5
)
filename_input = tk.Entry(options_frame, font=("Arial", 11))
filename_input.insert(0, "ban_ghi_moi")
filename_input.grid(row=1, column=1, columnspan=3, sticky="ew", pady=5)


status = tk.Label(root, text="Trang thai: San sang", font=("Arial", 10), fg="green")
status.pack(pady=8)


def update_status(message, color="blue"):
    status.config(text=f"Trang thai: {message}", fg=color)


library_frame = tk.LabelFrame(
    root,
    text="Thu vien ban ghi (WAV)",
    font=("Arial", 11, "bold"),
    padx=10,
    pady=8
)
library_frame.pack(fill="both", expand=True, padx=24, pady=(6, 12))

list_frame = tk.Frame(library_frame)
list_frame.pack(fill="both", expand=True)

audio_scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
audio_list = tk.Listbox(
    list_frame,
    height=8,
    font=("Arial", 10),
    activestyle="dotbox",
    yscrollcommand=audio_scrollbar.set
)
audio_scrollbar.config(command=audio_list.yview)
audio_scrollbar.pack(side="right", fill="y")
audio_list.pack(side="left", fill="both", expand=True)


def refresh_audio_list(select_path=None):
    audio_list.delete(0, tk.END)
    files = list_audio_files()

    for file_path in files:
        audio_list.insert(tk.END, file_path.name)

    if select_path:
        for index, file_path in enumerate(files):
            if file_path == Path(select_path):
                audio_list.selection_set(index)
                audio_list.activate(index)
                audio_list.see(index)
                break

    if not files:
        update_status("Chua co ban ghi nao trong thu vien.", "blue")

    return files


def get_selected_audio():
    selection = audio_list.curselection()
    if not selection:
        messagebox.showinfo("Thong bao", "Vui long chon mot ban ghi.")
        return None

    return OUTPUT_DIR / audio_list.get(selection[0])


def stop_playback(show_status=False):
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except pygame.error:
        pass

    if show_status:
        update_status("Da dung phat am thanh.", "blue")


def play_selected_audio():
    file_path = get_selected_audio()
    if file_path is None:
        return

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(str(file_path))
        pygame.mixer.music.play()
        update_status(f"Dang phat: {file_path.name}", "green")
    except (pygame.error, OSError) as error:
        messagebox.showerror("Khong the phat am thanh", str(error))
        update_status("Khong the phat ban ghi.", "red")


def rename_selected_audio():
    file_path = get_selected_audio()
    if file_path is None:
        return

    new_name = simpledialog.askstring(
        "Doi ten ban ghi",
        "Nhap ten moi (khong can them .wav):",
        initialvalue=file_path.stem,
        parent=root
    )
    if new_name is None:
        return

    try:
        stop_playback()
        renamed_path = rename_audio_file(file_path, new_name)
        refresh_audio_list(renamed_path)
        update_status(f"Da doi ten thanh: {renamed_path.name}", "green")
    except (ValueError, FileExistsError, FileNotFoundError, OSError) as error:
        messagebox.showerror("Khong the doi ten", str(error))
        update_status("Doi ten that bai.", "red")


def delete_selected_audio():
    file_path = get_selected_audio()
    if file_path is None:
        return

    confirmed = messagebox.askyesno(
        "Xac nhan xoa",
        f"Ban co chac muon xoa ban ghi '{file_path.name}' khong?",
        parent=root
    )
    if not confirmed:
        return

    try:
        stop_playback()
        delete_audio_file(file_path)
        refresh_audio_list()
        update_status(f"Da xoa: {file_path.name}", "green")
    except (ValueError, FileNotFoundError, OSError) as error:
        messagebox.showerror("Khong the xoa", str(error))
        update_status("Xoa ban ghi that bai.", "red")


def open_output_folder():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if os.name == "nt":
            os.startfile(str(OUTPUT_DIR))
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(OUTPUT_DIR)])
    except OSError as error:
        messagebox.showerror("Khong the mo thu muc", str(error))


button_frame = tk.Frame(library_frame)
button_frame.pack(fill="x", pady=(8, 0))

tk.Button(button_frame, text="Phat", command=play_selected_audio, width=12).pack(side="left", padx=(0, 6))
tk.Button(button_frame, text="Dung", command=lambda: stop_playback(True), width=12).pack(side="left", padx=6)
tk.Button(button_frame, text="Doi ten", command=rename_selected_audio, width=12).pack(side="left", padx=6)
tk.Button(button_frame, text="Xoa", command=delete_selected_audio, width=12).pack(side="left", padx=6)
tk.Button(button_frame, text="Lam moi", command=refresh_audio_list, width=12).pack(side="left", padx=6)
tk.Button(button_frame, text="Mo thu muc", command=open_output_folder, width=14).pack(side="right")

audio_list.bind("<Double-Button-1>", lambda event: play_selected_audio())


def on_success(file_path):
    refresh_audio_list(file_path)
    update_status(f"Tao am thanh thanh cong: {file_path.name}", "green")
    generate_button.config(state="normal")


def on_error(error_message):
    update_status(f"Loi: {error_message}", "red")
    generate_button.config(state="normal")


def generate_audio_worker(content, language, voice, file_name):
    try:
        language_map = {
            "Tu dong nhan dien": "auto",
            "Tieng Viet": "vi",
            "English": "en"
        }
        voice_map = {
            "Tu dong theo ngon ngu": "auto",
            "Diem Trinh": "diem_trinh",
            "af_heart": "af_heart"
        }

        file_path = create_audio(
            text=content,
            language=language_map[language],
            voice=voice_map[voice],
            speed=1.0,
            file_name=file_name
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
        update_status("Vui long nhap noi dung!", "red")
        return

    if not language or not voice:
        update_status("Vui long chon ngon ngu va giong doc!", "red")
        return

    generate_button.config(state="disabled")
    update_status("Dang tao giong noi...", "blue")

    worker = threading.Thread(
        target=generate_audio_worker,
        args=(content, language, voice, file_name),
        daemon=True
    )
    worker.start()


generate_button = tk.Button(
    root,
    text="TAO GIONG NOI AI",
    font=("Arial", 12, "bold"),
    bg="#2563eb",
    fg="white",
    command=generate_audio,
    padx=20,
    pady=10
)
generate_button.pack(pady=(0, 14))

refresh_audio_list()


def close_application():
    stop_playback()
    try:
        pygame.mixer.quit()
    except pygame.error:
        pass
    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_application)
root.mainloop()
