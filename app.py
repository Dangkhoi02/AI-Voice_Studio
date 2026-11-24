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


# ---------------------------------------------------------
# CUA SO CHINH VA THEME
# ---------------------------------------------------------
root = tk.Tk()
root.title("AI Voice Studio")
root.geometry("1050x860")
root.minsize(880, 720)
root.configure(bg="#F3F6FB")

COLORS = {
    "background": "#F3F6FB",
    "surface": "#FFFFFF",
    "surface_soft": "#F8FAFC",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "navy": "#14213D",
    "text": "#172033",
    "muted": "#64748B",
    "border": "#E2E8F0",
    "success": "#15803D",
    "danger": "#DC2626",
}

FONT = "Segoe UI"

style = ttk.Style()
try:
    style.theme_use("clam")
except tk.TclError:
    pass

style.configure(
    "Studio.TCombobox",
    font=(FONT, 10),
    padding=8,
    fieldbackground=COLORS["surface_soft"],
    background=COLORS["surface_soft"],
    foreground=COLORS["text"],
    arrowcolor=COLORS["muted"],
)
style.map(
    "Studio.TCombobox",
    fieldbackground=[("readonly", COLORS["surface_soft"])],
    foreground=[("readonly", COLORS["text"])],
)
style.configure(
    "Studio.Horizontal.TProgressbar",
    troughcolor="#DBEAFE",
    background=COLORS["primary"],
    bordercolor="#DBEAFE",
    lightcolor=COLORS["primary"],
    darkcolor=COLORS["primary"],
)

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
header = tk.Frame(root, bg=COLORS["navy"], padx=30, pady=22)
header.pack(fill="x")

header_left = tk.Frame(header, bg=COLORS["navy"])
header_left.pack(side="left", fill="x", expand=True)

tk.Label(
    header_left,
    text="AI VOICE STUDIO",
    font=(FONT, 23, "bold"),
    fg="#FFFFFF",
    bg=COLORS["navy"],
).pack(anchor="w")

tk.Label(
    header_left,
    text="Chuyển văn bản thành giọng nói bằng AI",
    font=(FONT, 10),
    fg="#CBD5E1",
    bg=COLORS["navy"],
).pack(anchor="w", pady=(4, 0))

tk.Label(
    header,
    text="TEXT TO SPEECH",
    font=(FONT, 9, "bold"),
    fg="#BFDBFE",
    bg="#263B61",
    padx=12,
    pady=7,
).pack(side="right", anchor="center")

# ---------------------------------------------------------
# NOI DUNG CHINH
# ---------------------------------------------------------
main = tk.Frame(root, bg=COLORS["background"], padx=26, pady=20)
main.pack(fill="both", expand=True)

# Card nhap van ban
input_card = tk.Frame(
    main,
    bg=COLORS["surface"],
    highlightbackground=COLORS["border"],
    highlightthickness=1,
    padx=18,
    pady=15,
)
input_card.pack(fill="x", pady=(0, 14))

tk.Label(
    input_card,
    text="Nội dung văn bản",
    font=(FONT, 13, "bold"),
    fg=COLORS["text"],
    bg=COLORS["surface"],
).pack(anchor="w")

tk.Label(
    input_card,
    text="Nhập hoặc dán nội dung bạn muốn chuyển thành giọng nói.",
    font=(FONT, 9),
    fg=COLORS["muted"],
    bg=COLORS["surface"],
).pack(anchor="w", pady=(3, 10))

text_area_frame = tk.Frame(input_card, bg=COLORS["surface_soft"])
text_area_frame.pack(fill="x")

text_input = tk.Text(
    text_area_frame,
    height=7,
    font=(FONT, 11),
    wrap="word",
    undo=True,
    relief="flat",
    borderwidth=0,
    padx=12,
    pady=10,
    bg=COLORS["surface_soft"],
    fg=COLORS["text"],
    insertbackground=COLORS["primary"],
    selectbackground="#BFDBFE",
)
text_input.pack(side="left", fill="both", expand=True)

text_scrollbar = ttk.Scrollbar(text_area_frame, orient="vertical", command=text_input.yview)
text_scrollbar.pack(side="right", fill="y")
text_input.configure(yscrollcommand=text_scrollbar.set)

# Card tuy chon
options_card = tk.Frame(
    main,
    bg=COLORS["surface"],
    highlightbackground=COLORS["border"],
    highlightthickness=1,
    padx=18,
    pady=15,
)
options_card.pack(fill="x", pady=(0, 14))

tk.Label(
    options_card,
    text="Thiết lập giọng đọc",
    font=(FONT, 13, "bold"),
    fg=COLORS["text"],
    bg=COLORS["surface"],
).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

options_card.columnconfigure(1, weight=1)
options_card.columnconfigure(3, weight=1)

def make_field_label(parent, text, row, column):
    tk.Label(
        parent,
        text=text,
        font=(FONT, 9, "bold"),
        fg=COLORS["muted"],
        bg=COLORS["surface"],
    ).grid(row=row, column=column, sticky="w", padx=(0, 10), pady=7)

make_field_label(options_card, "Ngôn ngữ", 1, 0)
language_options = ttk.Combobox(
    options_card,
    values=["Tự động nhận diện", "Tiếng Việt", "English"],
    state="readonly",
    style="Studio.TCombobox",
)
language_options.current(0)
language_options.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=5)

make_field_label(options_card, "Giọng đọc", 1, 2)
voice_options = ttk.Combobox(
    options_card,
    values=["Tự động theo ngôn ngữ", "Diễm Trinh", "af_heart"],
    state="readonly",
    style="Studio.TCombobox",
)
voice_options.current(0)
voice_options.grid(row=1, column=3, sticky="ew", pady=5)

make_field_label(options_card, "Tên bản ghi", 2, 0)
filename_input = tk.Entry(
    options_card,
    font=(FONT, 10),
    relief="flat",
    bg=COLORS["surface_soft"],
    fg=COLORS["text"],
    insertbackground=COLORS["primary"],
    highlightthickness=1,
    highlightbackground=COLORS["border"],
    highlightcolor=COLORS["primary"],
)
filename_input.insert(0, "ban_ghi_moi")
filename_input.grid(row=2, column=1, columnspan=3, sticky="ew", pady=5, ipady=8)

# Trang thai va nut tao
action_row = tk.Frame(main, bg=COLORS["background"])
action_row.pack(fill="x", pady=(0, 14))

status = tk.Label(
    action_row,
    text="Sẵn sàng tạo giọng nói",
    font=(FONT, 9),
    fg=COLORS["muted"],
    bg=COLORS["background"],
    anchor="w",
)
status.pack(side="left", fill="x", expand=True)

progress_bar = ttk.Progressbar(
    action_row,
    mode="indeterminate",
    length=115,
    style="Studio.Horizontal.TProgressbar",
)
progress_bar.pack(side="right", padx=(10, 0))

# ---------------------------------------------------------
# THU VIEN BAN GHI
# ---------------------------------------------------------
library_card = tk.Frame(
    main,
    bg=COLORS["surface"],
    highlightbackground=COLORS["border"],
    highlightthickness=1,
    padx=18,
    pady=15,
)
library_card.pack(fill="both", expand=True)

library_header = tk.Frame(library_card, bg=COLORS["surface"])
library_header.pack(fill="x", pady=(0, 10))

library_title_frame = tk.Frame(library_header, bg=COLORS["surface"])
library_title_frame.pack(side="left", fill="x", expand=True)

tk.Label(
    library_title_frame,
    text="Thư viện bản ghi",
    font=(FONT, 13, "bold"),
    fg=COLORS["text"],
    bg=COLORS["surface"],
).pack(anchor="w")

tk.Label(
    library_title_frame,
    text="Các tệp âm thanh WAV đã tạo",
    font=(FONT, 9),
    fg=COLORS["muted"],
    bg=COLORS["surface"],
).pack(anchor="w", pady=(2, 0))

tk.Label(
    library_header,
    text="WAV",
    font=(FONT, 9, "bold"),
    fg=COLORS["primary"],
    bg="#EFF6FF",
    padx=11,
    pady=5,
).pack(side="right")

list_frame = tk.Frame(library_card, bg=COLORS["surface_soft"])
list_frame.pack(fill="both", expand=True)

audio_scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
audio_list = tk.Listbox(
    list_frame,
    height=8,
    font=(FONT, 10),
    activestyle="none",
    relief="flat",
    borderwidth=0,
    highlightthickness=0,
    bg=COLORS["surface_soft"],
    fg=COLORS["text"],
    selectbackground="#DBEAFE",
    selectforeground=COLORS["navy"],
    yscrollcommand=audio_scrollbar.set,
    selectmode=tk.SINGLE,
)
audio_scrollbar.config(command=audio_list.yview)
audio_scrollbar.pack(side="right", fill="y")
audio_list.pack(side="left", fill="both", expand=True, padx=5, pady=5)


def update_status(message, color=None):
    status.config(text=message, fg=color or COLORS["muted"])


def refresh_audio_list(select_path=None):
    audio_list.delete(0, tk.END)
    files = list_audio_files()

    for file_path in files:
        audio_list.insert(tk.END, file_path.name)

    if select_path:
        selected_path = Path(select_path)
        for index, file_path in enumerate(files):
            if file_path == selected_path:
                audio_list.selection_set(index)
                audio_list.activate(index)
                audio_list.see(index)
                break

    if not files:
        update_status("Thư viện chưa có bản ghi nào.")

    return files


def get_selected_audio():
    selection = audio_list.curselection()
    if not selection:
        messagebox.showinfo("Thông báo", "Vui lòng chọn một bản ghi.")
        return None

    return OUTPUT_DIR / audio_list.get(selection[0])


# ---------------------------------------------------------
# CAC CHUC NANG THU VIEN
# ---------------------------------------------------------
def stop_playback(show_status=False):
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except pygame.error:
        pass

    if show_status:
        update_status("Đã dừng phát âm thanh.")


def play_selected_audio():
    file_path = get_selected_audio()
    if file_path is None:
        return

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(str(file_path))
        pygame.mixer.music.play()
        update_status(f"Đang phát: {file_path.name}", COLORS["success"])
    except (pygame.error, OSError) as error:
        messagebox.showerror("Không thể phát âm thanh", str(error))
        update_status("Không thể phát bản ghi.", COLORS["danger"])


def rename_selected_audio():
    file_path = get_selected_audio()
    if file_path is None:
        return

    new_name = simpledialog.askstring(
        "Đổi tên bản ghi",
        "Nhập tên mới (không cần thêm .wav):",
        initialvalue=file_path.stem,
        parent=root,
    )
    if new_name is None:
        return

    try:
        stop_playback()
        renamed_path = rename_audio_file(file_path, new_name)
        refresh_audio_list(renamed_path)
        update_status(f"Đã đổi tên: {renamed_path.name}", COLORS["success"])
    except (ValueError, FileExistsError, FileNotFoundError, OSError) as error:
        messagebox.showerror("Không thể đổi tên", str(error))
        update_status("Đổi tên thất bại.", COLORS["danger"])


def delete_selected_audio():
    file_path = get_selected_audio()
    if file_path is None:
        return

    confirmed = messagebox.askyesno(
        "Xác nhận xóa",
        f"Bạn có chắc muốn xóa bản ghi '{file_path.name}' không?",
        parent=root,
    )
    if not confirmed:
        return

    try:
        stop_playback()
        delete_audio_file(file_path)
        refresh_audio_list()
        update_status(f"Đã xóa: {file_path.name}", COLORS["success"])
    except (ValueError, FileNotFoundError, OSError) as error:
        messagebox.showerror("Không thể xóa", str(error))
        update_status("Xóa bản ghi thất bại.", COLORS["danger"])


def open_output_folder():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if os.name == "nt":
            os.startfile(str(OUTPUT_DIR))
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(OUTPUT_DIR)])
    except OSError as error:
        messagebox.showerror("Không thể mở thư mục", str(error))


# Cac nut thao tac thu vien
button_frame = tk.Frame(library_card, bg=COLORS["surface"])
button_frame.pack(fill="x", pady=(11, 0))


def make_action_button(text, command, primary=False):
    if primary:
        button = tk.Button(
            button_frame,
            text=text,
            command=command,
            font=(FONT, 9, "bold"),
            bg=COLORS["primary"],
            fg="#FFFFFF",
            activebackground=COLORS["primary_hover"],
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=15,
            pady=9,
            cursor="hand2",
        )
    else:
        button = tk.Button(
            button_frame,
            text=text,
            command=command,
            font=(FONT, 9),
            bg="#F1F5F9",
            fg=COLORS["text"],
            activebackground="#E2E8F0",
            activeforeground=COLORS["text"],
            relief="flat",
            bd=0,
            padx=12,
            pady=9,
            cursor="hand2",
        )
    return button


make_action_button("▶  Phát", play_selected_audio, primary=True).pack(side="left", padx=(0, 6))
make_action_button("■  Dừng", lambda: stop_playback(True)).pack(side="left", padx=3)
make_action_button("Đổi tên", rename_selected_audio).pack(side="left", padx=3)
make_action_button("Xóa", delete_selected_audio).pack(side="left", padx=3)
make_action_button("Làm mới", refresh_audio_list).pack(side="left", padx=3)
make_action_button("Mở thư mục", open_output_folder).pack(side="right")

audio_list.bind("<Double-Button-1>", lambda event: play_selected_audio())

# ---------------------------------------------------------
# TAO GIONG NOI
# ---------------------------------------------------------
def on_success(file_path):
    progress_bar.stop()
    refresh_audio_list(file_path)
    update_status(f"Đã tạo âm thanh thành công: {file_path.name}", COLORS["success"])
    generate_button.config(state="normal")


def on_error(error_message):
    progress_bar.stop()
    update_status(f"Lỗi: {error_message}", COLORS["danger"])
    generate_button.config(state="normal")
    messagebox.showerror("Không thể tạo giọng nói", error_message)


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
        update_status("Vui lòng nhập nội dung văn bản.", COLORS["danger"])
        text_input.focus_set()
        return

    if not language or not voice:
        update_status("Vui lòng chọn ngôn ngữ và giọng đọc.", COLORS["danger"])
        return

    generate_button.config(state="disabled")
    progress_bar.start(12)
    update_status("Đang xử lý văn bản và tạo giọng nói...", COLORS["primary"])

    worker = threading.Thread(
        target=generate_audio_worker,
        args=(content, language, voice, file_name),
        daemon=True,
    )
    worker.start()


generate_button = tk.Button(
    main,
    text="▶   TẠO GIỌNG NÓI AI",
    font=(FONT, 11, "bold"),
    bg=COLORS["primary"],
    fg="#FFFFFF",
    activebackground=COLORS["primary_hover"],
    activeforeground="#FFFFFF",
    disabledforeground="#DBEAFE",
    relief="flat",
    bd=0,
    cursor="hand2",
    command=generate_audio,
    padx=24,
    pady=13,
)
generate_button.pack(fill="x", pady=(0, 14))

# Khoi tao danh sach ban ghi
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
