import os
import queue
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path

import pygame

from services.logging_config import setup_logging
from services.kokoro_english_service import ENGLISH_PYTHON, cancel_active_generation
from services.tts_manager import (
    generate_audio as create_audio,
    generate_preview_audio as create_preview_audio,
)
from services.voice_manager import (
    AUTO_VOICE_LABEL,
    get_language_options,
    get_language_code,
    get_voice_options,
    get_voice_id,
)
from services.style_manager import get_speech_styles, get_style_id
from services.speech_analyzer import get_expression_options, get_expression_id
from services.voice_profile_manager import (
    get_voice_profiles, get_profile_review_summary, save_voice_evaluation,
)
from services.voice_manager import LANGUAGES
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
def main():
    logger = setup_logging()
    root = tk.Tk()
    root.title("AI Voice Studio")
    ui_queue = queue.Queue()
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
    nav_rows = {}
    nav_labels = {}
    for key, symbol, name in [
        ("studio", "▣", "Voice Studio"),
        ("library", "♫", "Audio Library"),
        ("profiles", "◎", "Voice Profiles"),
    ]:
        row = tk.Frame(sidebar, bg=C["sidebar"], padx=16, pady=12, cursor="hand2")
        row.pack(fill="x", padx=12, pady=3)
        symbol_label = label(row, symbol, 13, C["muted"], True, bg=C["sidebar"])
        symbol_label.pack(side="left")
        name_label = label(row, name, 10, C["muted"], False, bg=C["sidebar"])
        name_label.pack(side="left", padx=12)
        nav_rows[key] = row
        nav_labels[key] = (symbol_label, name_label)
    
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
    engine_status = tk.Label(topbar, text="", font=(FONT, 9, "bold"), fg=C["green"],
                             bg="#12352F", padx=12, pady=8)
    engine_status.pack(side="right", anchor="center")
    try:
        import importlib.util
        vi_ready = importlib.util.find_spec("kokoro_vietnamese") is not None
    except (ImportError, ValueError):
        vi_ready = False
    en_ready = ENGLISH_PYTHON.is_file()
    if vi_ready and en_ready:
        engine_status.config(text="●  ENGINE SẴN SÀNG", fg=C["green"])
    elif vi_ready:
        engine_status.config(text="●  THIẾU ENGINE EN", fg="#F5B942")
    else:
        engine_status.config(text="●  THIẾU ENGINE VI", fg="#F5B942")
    
    # Tkinter Frame padx/pady options accept a single distance, not a tuple.
    content = tk.Frame(workspace, bg=C["bg"], padx=24, pady=22)
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
    
    # Voice settings panel with its own vertical scrolling area.
    settings_card = card(content, width=286)
    settings_card.grid(row=0, column=1, sticky="nsew", pady=(0, 14))
    settings_card.grid_propagate(False)
    
    settings_canvas = tk.Canvas(
        settings_card, bg=C["panel"], highlightthickness=0, bd=0
    )
    settings_scrollbar = ttk.Scrollbar(
        settings_card, orient="vertical", command=settings_canvas.yview,
        style="Dark.Vertical.TScrollbar"
    )
    settings_canvas.configure(yscrollcommand=settings_scrollbar.set)
    settings_scrollbar.pack(side="right", fill="y")
    settings_canvas.pack(side="left", fill="both", expand=True)
    
    settings_body = tk.Frame(settings_canvas, bg=C["panel"], padx=17, pady=16)
    settings_window = settings_canvas.create_window(
        (0, 0), window=settings_body, anchor="nw"
    )
    
    def update_settings_scroll_region(event=None):
        settings_canvas.configure(scrollregion=settings_canvas.bbox("all"))
        settings_canvas.itemconfigure(settings_window, width=settings_canvas.winfo_width())
    
    settings_body.bind("<Configure>", update_settings_scroll_region)
    settings_canvas.bind("<Configure>", update_settings_scroll_region)
    
    def scroll_settings(event):
        if settings_canvas.winfo_exists():
            settings_canvas.yview_scroll(int(-event.delta / 120), "units")
    
    def bind_settings_wheel(event):
        settings_canvas.bind_all("<MouseWheel>", scroll_settings)
    
    def unbind_settings_wheel(event):
        settings_canvas.unbind_all("<MouseWheel>")
    
    settings_canvas.bind("<Enter>", bind_settings_wheel)
    settings_canvas.bind("<Leave>", unbind_settings_wheel)
    settings_body.bind("<Enter>", bind_settings_wheel)
    settings_body.bind("<Leave>", unbind_settings_wheel)
    label(settings_body, "VOICE SETTINGS", 9, C["muted"], True).pack(anchor="w")
    label(settings_body, "Configure your output", 14, C["text"], True).pack(anchor="w", pady=(14, 17))
    
    label(settings_body, "LANGUAGE", 8, C["muted"], True).pack(anchor="w", pady=(0, 7))
    language_options = ttk.Combobox(
        settings_body, values=get_language_options(),
        state="readonly", style="Dark.TCombobox"
    )
    language_options.current(0)
    language_options.pack(fill="x", pady=(0, 16))
    
    label(settings_body, "VOICE", 8, C["muted"], True).pack(anchor="w", pady=(0, 7))
    voice_options = ttk.Combobox(
        settings_body, values=[AUTO_VOICE_LABEL],
        state="readonly", style="Dark.TCombobox"
    )
    voice_options.current(0)
    voice_options.pack(fill="x", pady=(0, 7))
    
    label(settings_body, "SPEECH STYLE", 8, C["muted"], True).pack(anchor="w", pady=(10, 7))
    style_options = ttk.Combobox(
        settings_body, values=[], state="readonly", style="Dark.TCombobox"
    )
    style_options.pack(fill="x", pady=(0, 7))
    
    label(settings_body, "EXPRESSION", 8, C["muted"], True).pack(anchor="w", pady=(10, 7))
    expression_options = ttk.Combobox(
        settings_body, values=get_expression_options(), state="readonly", style="Dark.TCombobox"
    )
    expression_options.current(0)
    expression_options.pack(fill="x", pady=(0, 7))
    label(
        settings_body,
        "Điều chỉnh nhịp nghỉ theo dấu câu; chưa thay đổi cảm xúc hoặc cao độ của mô hình.",
        8, C["muted"], wraplength=245, justify="left"
    ).pack(anchor="w", pady=(0, 8))
    
    
    def update_style_options(language_code):
        styles = get_speech_styles(language_code if language_code in ("vi", "en") else "vi")
        style_options["values"] = [item["label"] for item in styles]
        style_options.current(0)
    
    
    def update_voice_options(event=None):
        language_code = get_language_code(language_options.get())
        options = get_voice_options(language_code)
        voice_options["values"] = options
        voice_options.current(0)
        update_style_options(language_code)
    
    
    language_options.bind("<<ComboboxSelected>>", update_voice_options)
    update_voice_options()
    label(settings_body, "Auto voice selects a matching voice for the detected language.", 8, C["muted"], wraplength=245, justify="left").pack(anchor="w", pady=(0, 17))
    
    tk.Frame(settings_body, bg=C["border"], height=1).pack(fill="x", pady=(0, 15))
    label(settings_body, "OUTPUT FILE NAME", 8, C["muted"], True).pack(anchor="w", pady=(0, 7))
    filename_input = tk.Entry(
        settings_body, font=(FONT, 10), relief="flat", bd=0,
        bg=C["input"], fg=C["text"], insertbackground=C["blue"],
        highlightthickness=1, highlightbackground=C["border"],
        highlightcolor=C["blue"]
    )
    filename_input.insert(0, "ban_ghi_moi")
    filename_input.pack(fill="x", ipady=10)
    label(settings_body, "File format: WAV", 8, C["muted"]).pack(anchor="w", pady=(7, 0))
    
    preview_button = action_button(settings_body, "♫   PREVIEW VOICE", lambda: None, compact=True)
    preview_button.pack(fill="x", pady=(16, 7))
    label(
        settings_body,
        "Nghe thử bằng nội dung trong khung soạn thảo. Nếu để trống, ứng dụng dùng câu mẫu theo ngôn ngữ.",
        8, C["muted"], wraplength=245, justify="left"
    ).pack(anchor="w", pady=(0, 8))
    
    generate_button = action_button(settings_body, "▶   GENERATE AUDIO", lambda: None, primary=True)
    generate_button.pack(fill="x", pady=(4, 0))
    
    # Generate controls and status
    generate_area = tk.Frame(settings_body, bg=C["panel"])
    generate_area.pack(side="bottom", fill="x", pady=(18, 0))
    status = label(generate_area, "Ready to generate", 8, C["muted"], wraplength=245, justify="left")
    status.pack(anchor="w", pady=(0, 9))
    progress_bar = ttk.Progressbar(generate_area, mode="indeterminate", style="Dark.Horizontal.TProgressbar")
    progress_bar.pack(fill="x", pady=(0, 10))
    cancel_button = action_button(generate_area, "Hủy tác vụ", lambda: cancel_generation(), compact=True)
    cancel_button.pack(fill="x", pady=(0, 8))
    cancel_button.config(state="disabled")
    is_busy = False
    current_cancel_event = None
    active_worker = None

    def set_busy(flag, message=None, color=None):
        nonlocal is_busy
        is_busy = flag
        state = "disabled" if flag else "normal"
        generate_button.config(state=state)
        preview_button.config(state=state)
        cancel_button.config(state="normal" if flag else "disabled")
        progress_bar.start(12) if flag else progress_bar.stop()
        if message:
            update_status(message, color)

    def cancel_generation():
        if not is_busy or current_cancel_event is None:
            return
        current_cancel_event.set()
        cancel_active_generation()
        cancel_button.config(state="disabled")
        update_status("Đang hủy tác vụ…", "#F5B942")

    def poll_ui_queue():
        try:
            while True:
                ui_queue.get_nowait()()
        except queue.Empty:
            pass
        if root.winfo_exists():
            root.after(80, poll_ui_queue)

    poll_ui_queue()
    
    # Voice Profiles page
    profiles_card = card(content, padx=18, pady=16)
    profiles_card.grid(row=0, column=0, columnspan=2, rowspan=2, sticky="nsew")
    profiles_card.grid_remove()
    profiles_header = tk.Frame(profiles_card, bg=C["panel"])
    profiles_header.pack(fill="x", pady=(0, 14))
    label(profiles_header, "Voice Profiles", 17, C["text"], True).pack(side="left")
    profile_summary_label = label(profiles_header, "", 9, C["muted"])
    profile_summary_label.pack(side="right")
    
    profiles_toolbar = tk.Frame(profiles_card, bg=C["panel"])
    profiles_toolbar.pack(fill="x", pady=(0, 12))
    label(profiles_toolbar, "LANGUAGE", 8, C["muted"], True).pack(side="left", padx=(0, 8))
    profile_language_filter = ttk.Combobox(
        profiles_toolbar, values=["Tất cả", "Tiếng Việt", "English"],
        state="readonly", style="Dark.TCombobox", width=16
    )
    profile_language_filter.current(0)
    profile_language_filter.pack(side="left")
    profile_body = tk.Frame(profiles_card, bg=C["panel"])
    profile_body.pack(fill="both", expand=True)
    profile_body.columnconfigure(0, weight=1)
    profile_body.columnconfigure(1, weight=2)
    profile_body.rowconfigure(0, weight=1)
    
    profile_list_frame = tk.Frame(profile_body, bg=C["input"], highlightbackground=C["border"], highlightthickness=1)
    profile_list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
    profile_list_scroll = ttk.Scrollbar(profile_list_frame, orient="vertical")
    profile_listbox = tk.Listbox(
        profile_list_frame, font=(FONT, 9), activestyle="none", relief="flat", bd=0,
        bg=C["input"], fg=C["text"], selectbackground="#294A7B",
        yscrollcommand=profile_list_scroll.set
    )
    profile_list_scroll.config(command=profile_listbox.yview)
    profile_list_scroll.pack(side="right", fill="y")
    profile_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    
    profile_detail = tk.Frame(profile_body, bg=C["panel"])
    profile_detail.grid(row=0, column=1, sticky="nsew")
    profile_detail.columnconfigure(1, weight=1)
    profile_name_label = label(profile_detail, "Chọn một giọng đọc", 15, C["text"], True)
    profile_name_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
    profile_identity_label = label(profile_detail, "", 9, C["muted"], wraplength=540, justify="left")
    profile_identity_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 14))
    label(profile_detail, "ĐÁNH GIÁ GIỌNG ĐỌC (1–5)", 8, C["muted"], True).grid(
        row=2, column=0, columnspan=2, sticky="w", pady=(0, 8)
    )
    profile_rating_entries = {}
    for row_index, (field, caption_text) in enumerate([
        ("distinctiveness", "Độ khác biệt"),
        ("naturalness", "Độ tự nhiên"),
        ("rhythm", "Nhịp điệu"),
        ("expressiveness", "Biểu cảm"),
    ], start=3):
        label(profile_detail, caption_text, 9, C["muted"]).grid(
            row=row_index, column=0, sticky="w", pady=4
        )
        entry = tk.Entry(
            profile_detail, width=8, font=(FONT, 9), relief="flat",
            bg=C["input"], fg=C["text"], insertbackground=C["blue"],
            highlightthickness=1, highlightbackground=C["border"]
        )
        entry.grid(row=row_index, column=1, sticky="w", pady=4, ipady=4)
        profile_rating_entries[field] = entry
    
    status_row = 7
    label(profile_detail, "TRẠNG THÁI", 8, C["muted"], True).grid(
        row=status_row, column=0, sticky="w", pady=(12, 6)
    )
    profile_status = ttk.Combobox(
        profile_detail, values=["pending", "reviewed", "needs_retest"],
        state="readonly", style="Dark.TCombobox", width=18
    )
    profile_status.grid(row=status_row, column=1, sticky="w", pady=(12, 6))
    label(profile_detail, "GHI CHÚ ĐÁNH GIÁ", 8, C["muted"], True).grid(
        row=8, column=0, columnspan=2, sticky="w", pady=(12, 6)
    )
    profile_notes = tk.Text(
        profile_detail, height=5, wrap="word", font=(FONT, 9),
        bg=C["input"], fg=C["text"], insertbackground=C["blue"],
        relief="flat", bd=0, padx=9, pady=8
    )
    profile_notes.grid(row=9, column=0, columnspan=2, sticky="ew")
    profile_action_row = tk.Frame(profile_detail, bg=C["panel"])
    profile_action_row.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(12, 0))
    profile_save_button = action_button(profile_action_row, "Save evaluation", lambda: save_selected_profile(), primary=True, compact=True)
    profile_save_button.pack(side="left", padx=(0, 8))
    profile_use_button = action_button(profile_action_row, "Use in Studio", lambda: use_selected_profile(), compact=True)
    profile_use_button.pack(side="left")
    
    profile_records = []
    
    def selected_profile():
        selection = profile_listbox.curselection()
        if not selection:
            return None
        index = selection[0]
        if index >= len(profile_records):
            return None
        return profile_records[index]
    
    def refresh_profile_list(select_id=None):
        nonlocal profile_records
        language_label = profile_language_filter.get()
        language_code = {"Tiếng Việt": "vi", "English": "en"}.get(language_label)
        profile_records = get_voice_profiles(language_code)
        profile_listbox.delete(0, tk.END)
        for profile in profile_records:
            language_tag = "VI" if profile["language"] == "vi" else "EN"
            evaluation = profile["evaluation"]
            marker = "✓" if evaluation["status"] == "reviewed" else "○"
            profile_listbox.insert(tk.END, f"{marker} [{language_tag}] {profile['display_name']}")
        summary = get_profile_review_summary(language_code)
        profile_summary_label.config(
            text=f"{summary['reviewed']}/{summary['total']} đã đánh giá · {summary['pending']} còn lại"
        )
        if profile_records:
            target_index = next(
                (i for i, item in enumerate(profile_records) if item["id"] == select_id),
                0
            )
            profile_listbox.selection_set(target_index)
            profile_listbox.activate(target_index)
            show_selected_profile()
        else:
            profile_name_label.config(text="Không có hồ sơ giọng đọc")
            profile_identity_label.config(text="")
    
    def show_selected_profile(event=None):
        profile = selected_profile()
        if profile is None:
            return
        identity = profile.get("identity", {})
        evaluation = profile.get("evaluation", {})
        language_name = "Tiếng Việt" if profile["language"] == "vi" else "English"
        profile_name_label.config(text=profile["display_name"])
        identity_parts = [
            f"Ngôn ngữ: {language_name}",
            f"Giới tính: {identity.get('gender') or 'Chưa xác minh'}",
            f"Khu vực: {identity.get('region') or 'Chưa xác minh'}",
            f"Accent: {identity.get('accent') or 'Chưa xác minh'}",
            f"Chất giọng: {identity.get('timbre') or 'Chưa đánh giá'}",
        ]
        profile_identity_label.config(text="   •   ".join(identity_parts))
        for field, entry in profile_rating_entries.items():
            entry.delete(0, tk.END)
            value = evaluation.get(field)
            if value is not None:
                entry.insert(0, str(value))
        profile_status.set(evaluation.get("status", "pending"))
        profile_notes.delete("1.0", tk.END)
        profile_notes.insert("1.0", evaluation.get("notes") or "")
    
    def save_selected_profile():
        profile = selected_profile()
        if profile is None:
            return
        ratings = {}
        try:
            for field, entry in profile_rating_entries.items():
                raw_value = entry.get().strip()
                if not raw_value:
                    ratings[field] = None
                    continue
                value = int(raw_value)
                if not 1 <= value <= 5:
                    raise ValueError("Điểm đánh giá phải nằm trong khoảng 1 đến 5.")
                ratings[field] = value
            save_voice_evaluation(
                voice_id=profile["id"],
                language_code=profile["language"],
                ratings=ratings,
                status=profile_status.get(),
                notes=profile_notes.get("1.0", "end-1c").strip(),
            )
            refresh_profile_list(profile["id"])
            messagebox.showinfo("Voice Profiles", "Đã lưu đánh giá giọng đọc.")
        except (ValueError, OSError) as error:
            messagebox.showerror("Không thể lưu đánh giá", str(error))
    
    def use_selected_profile():
        profile = selected_profile()
        if profile is None:
            return
        language_options.set("Tiếng Việt" if profile["language"] == "vi" else "English")
        update_voice_options()
        voice_label = next(
            (
                item["label"]
                for item in LANGUAGES[profile["language"]]["voices"]
                if item["id"] == profile["id"]
            ),
            None,
        )
        if voice_label:
            voice_options.set(voice_label)
        show_page("studio")
    
    profile_listbox.bind("<<ListboxSelect>>", show_selected_profile)
    profile_language_filter.bind("<<ComboboxSelected>>", lambda event: refresh_profile_list())
    refresh_profile_list()
    
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
    
    def show_page(page):
        profiles_card.grid_remove()
        if page == "library":
            editor_card.grid_remove()
            settings_card.grid_remove()
            library_card.grid_configure(row=0, column=0, columnspan=2, sticky="nsew")
        elif page == "profiles":
            editor_card.grid_remove()
            settings_card.grid_remove()
            library_card.grid_remove()
            profiles_card.grid(row=0, column=0, columnspan=2, rowspan=2, sticky="nsew")
            refresh_profile_list()
        else:
            library_card.grid_configure(row=1, column=0, columnspan=2, sticky="nsew")
            editor_card.grid()
            settings_card.grid()
            library_card.grid()
    
        for key, row in nav_rows.items():
            active = key == page
            bg = "#1B2B49" if active else C["sidebar"]
            row.configure(bg=bg)
            for item in row.winfo_children():
                item.configure(bg=bg)
            symbol_label, name_label = nav_labels[key]
            symbol_label.configure(fg=C["blue"] if active else C["muted"])
            name_label.configure(fg=C["text"] if active else C["muted"], font=(FONT, 10, "bold" if active else "normal"))
    
        if page == "library":
            refresh_audio_list()
    
    for page_key, row in nav_rows.items():
        row.bind("<Button-1>", lambda event, key=page_key: show_page(key))
        for child in row.winfo_children():
            child.bind("<Button-1>", lambda event, key=page_key: show_page(key))
    
    def update_status(message, color=None):
        status.config(text=message, fg=color or C["muted"])
    
    audio_paths = []

    def refresh_audio_list(select_path=None):
        audio_list.delete(0, tk.END)
        files = list_audio_files()
        audio_paths[:] = files
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
            audio_list.insert(tk.END, "Chưa có bản ghi nào. Hãy tạo giọng nói đầu tiên!")
        return files
    
    def get_selected_audio():
        selection = audio_list.curselection()
        if not selection:
            messagebox.showinfo("Audio Library", "Please select a recording first.")
            return None
        index = selection[0]
        if index >= len(audio_paths):
            return None
        return audio_paths[index]
    
    def stop_playback(show_status=False):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                # stop() pauses playback state but may keep the WAV file handle open.
                # unload() releases the file so Windows can rename or delete it.
                pygame.mixer.music.unload()
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
    
    def start_preview_playback(file_path):
        set_busy(False)
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            stop_playback()
            pygame.mixer.music.load(str(file_path))
            pygame.mixer.music.play()
            update_status("Playing voice preview...", C["green"])
    
            def monitor_preview():
                if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                    root.after(250, monitor_preview)
                else:
                    stop_playback()
                    try:
                        Path(file_path).unlink(missing_ok=True)
                    except OSError:
                        pass
                    update_status("Voice preview finished.")
                    preview_button.config(state="normal")
            root.after(250, monitor_preview)
        except (pygame.error, OSError) as error:
            preview_button.config(state="normal")
            messagebox.showerror("Preview error", str(error))
            update_status("Unable to play preview.", C["red"])
            try:
                Path(file_path).unlink(missing_ok=True)
            except OSError:
                pass
    
    
    def preview_audio_worker(content, language, voice, speech_style, expression_label, task_cancel_event):
        try:
            language_code = get_language_code(language)
            voice_id = get_voice_id(language_code, voice)
            style_language = language_code if language_code in ("vi", "en") else "vi"
            style_id = get_style_id(speech_style, style_language)
            expression_id = get_expression_id(expression_label)
            file_path = create_preview_audio(
                text=content,
                language=language_code,
                voice=voice_id,
                style=style_id,
                expression=expression_id,
                cancel_event=task_cancel_event,
            )
            ui_queue.put(lambda: start_preview_playback(file_path))
        except Exception as error:
            error_message = str(error)
            ui_queue.put(lambda error_message=error_message: on_preview_error(error_message))
    
    
    def on_preview_error(error_message):
        set_busy(False, "Không thể nghe thử. Chi tiết đã được ghi vào logs/app.log.", C["red"])
        logger.exception("Voice preview failed: %s", error_message)
        messagebox.showerror("Không thể nghe thử", "Đã xảy ra lỗi khi tạo bản nghe thử. Chi tiết đã được ghi vào logs/app.log.")
    
    
    def preview_audio():
        nonlocal current_cancel_event, active_worker
        content = text_input.get("1.0", "end-1c").strip()
        language = language_options.get()
        voice = voice_options.get()
        speech_style = style_options.get()
        expression_label = expression_options.get()
    
        if not content:
            language_code = get_language_code(language)
            content = (
                "Xin chào! Đây là bản nghe thử giọng đọc của AI Voice Studio."
                if language_code in ("vi", "auto")
                else "Hello! This is a voice preview from AI Voice Studio."
            )
        if not language or not voice or not speech_style or not expression_label:
            update_status("Choose a language, voice and speech style.", C["red"])
            return
    
        if is_busy:
            return
        stop_playback()
        current_cancel_event = threading.Event()
        set_busy(True, "Đang chuẩn bị bản nghe thử…", C["blue"])
        active_worker = threading.Thread(
            target=preview_audio_worker,
            args=(content, language, voice, speech_style, expression_label, current_cancel_event),
            daemon=True,
        )
        active_worker.start()
    
    
    def on_success(file_path):
        set_busy(False)
        refresh_audio_list(file_path)
        update_status(f"Created successfully: {file_path.name}", C["green"])
        generate_button.config(state="normal")
    
    def on_error(error_message):
        set_busy(False, "Không thể tạo giọng nói. Chi tiết đã được ghi vào logs/app.log.", C["red"])
        logger.exception("Speech generation failed: %s", error_message)
        messagebox.showerror("Không thể tạo giọng nói", "Đã xảy ra lỗi khi tạo âm thanh. Chi tiết đã được ghi vào logs/app.log.")

    def generate_audio_worker(content, language, voice, speech_style, expression_label, file_name, task_cancel_event):
        try:
            language_code = get_language_code(language)
            voice_id = get_voice_id(language_code, voice)
            style_language = language_code if language_code in ("vi", "en") else "vi"
            style_id = get_style_id(speech_style, style_language)
            expression_id = get_expression_id(expression_label)
            file_path = create_audio(
                text=content,
                language=language_code,
                voice=voice_id,
                style=style_id,
                expression=expression_id,
                file_name=file_name,
                cancel_event=task_cancel_event,
            )
            ui_queue.put(lambda: on_success(file_path))
        except Exception as error:
            error_message = str(error)
            ui_queue.put(lambda error_message=error_message: on_error(error_message))
    
    def generate_audio():
        nonlocal current_cancel_event, active_worker
        content = text_input.get("1.0", "end-1c").strip()
        language = language_options.get()
        voice = voice_options.get()
        speech_style = style_options.get()
        expression_label = expression_options.get()
        file_name = filename_input.get().strip() or "ban_ghi_moi"
        if not content:
            update_status("Please enter some text first.", C["red"])
            text_input.focus_set()
            return
        if not language or not voice or not speech_style or not expression_label:
            update_status("Choose a language, voice and speech style.", C["red"])
            return
        if is_busy:
            return
        current_cancel_event = threading.Event()
        set_busy(True, "Đang tạo giọng nói…", C["blue"])
        active_worker = threading.Thread(
            target=generate_audio_worker,
            args=(content, language, voice, speech_style, expression_label, file_name, current_cancel_event),
            daemon=True,
        )
        active_worker.start()
    
    
    generate_button.config(command=generate_audio)
    preview_button.config(command=preview_audio)
    
    refresh_audio_list()
    
    def close_application():
        if current_cancel_event is not None:
            current_cancel_event.set()
        cancel_active_generation()
        if active_worker is not None and active_worker.is_alive():
            active_worker.join(timeout=2)
        stop_playback()
        progress_bar.stop()
        try:
            pygame.mixer.quit()
        except pygame.error:
            pass
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", close_application)
    root.mainloop()
    


if __name__ == "__main__":
    main()
