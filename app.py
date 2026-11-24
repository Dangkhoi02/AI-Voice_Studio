
import threading
import tkinter as tk
from tkinter import ttk

from services.tts_manager import generate_audio as create_audio


# Khoi tao cua so chinh
root = tk.Tk()
root.title("AI Voice Studio")
root.geometry("800x650")
root.minsize(650, 550)


# Tieu de
title = tk.Label(
    root,
    text="AI VOICE STUDIO",
    font=("Arial", 24, "bold")
)
title.pack(pady=20)

subtitle = tk.Label(
    root,
    text="Cong cu chuyen van ban thanh giong noi AI",
    font=("Arial", 11)
)
subtitle.pack()


# Khu vuc nhap van ban
label_text = tk.Label(
    root,
    text="Nhap noi dung can doc:",
    font=("Arial", 12, "bold")
)
label_text.pack(anchor="w", padx=30, pady=(25, 5))

text_input = tk.Text(
    root,
    height=10,
    font=("Arial", 12),
    wrap="word"
)
text_input.pack(fill="x", padx=30)


# Chon ngon ngu
label_language = tk.Label(
    root,
    text="Chon ngon ngu:",
    font=("Arial", 12, "bold")
)
label_language.pack(anchor="w", padx=30, pady=(20, 5))

language_options = ttk.Combobox(
    root,
    values=[
        "Tu dong nhan dien",
        "Tieng Viet",
        "English"
    ],
    state="readonly"
)
language_options.current(0)
language_options.pack(fill="x", padx=30)


# Chon giong doc
label_voice = tk.Label(
    root,
    text="Chon giong doc:",
    font=("Arial", 12, "bold")
)
label_voice.pack(anchor="w", padx=30, pady=(15, 5))

voice_options = ttk.Combobox(
    root,
    values=[
        "Diem Trinh",
        "af_heart"
    ],
    state="readonly"
)
voice_options.current(0)
voice_options.pack(fill="x", padx=30)

# Dat ten file am thanh
label_filename = tk.Label(
    root,
    text="Ten file am thanh:",
    font=("Arial", 12, "bold")
)
label_filename.pack(anchor="w", padx=30, pady=(15, 5))

filename_input = tk.Entry(
    root,
    font=("Arial", 12)
)
filename_input.pack(fill="x", padx=30)

filename_input.insert(0, "ban_ghi_moi")



# Trang thai ung dung
status = tk.Label(
    root,
    text="Trang thai: San sang",
    font=("Arial", 10),
    fg="green"
)
status.pack(pady=20)


# Cap nhat trang thai
def update_status(message, color="blue"):
    status.config(
        text=f"Trang thai: {message}",
        fg=color
    )


# Tao am thanh thanh cong
def on_success(file_path):
    update_status(
        f"Tao am thanh thanh cong: {file_path.name}",
        "green"
    )
    generate_button.config(state="normal")


# Xu ly loi
def on_error(error_message):
    update_status(
        f"Loi: {error_message}",
        "red"
    )
    generate_button.config(state="normal")


# Ham chay trong luong rieng
def generate_audio_worker(content, language, voice, file_name):
    try:
        language_map = {
            "Tu dong nhan dien": "auto",
            "Tieng Viet": "vi",
            "English": "en"
        }

        voice_map = {
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

        root.after(
            0,
            lambda: on_success(file_path)
        )

    except Exception as error:
        error_message = str(error)

        root.after(
            0,
            lambda: on_error(error_message)
        )


# Ham tao giong noi
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


# Nut tao giong noi
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
generate_button.pack(pady=10)


# Chay ung dung
root.mainloop()
