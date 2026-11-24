"""Central catalog for supported languages and TTS voices.

Add new languages and voices here before connecting their TTS engines.
The catalog contains only voices that are already integrated and usable.
"""

AUTO_LANGUAGE_LABEL = "Tự động nhận diện"
AUTO_VOICE_LABEL = "Tự động theo ngôn ngữ"

LANGUAGES = {
    "vi": {
        "label": "Tiếng Việt",
        "engine": "kokoro_vi",
        "default_voice": "diem_trinh",
        "voices": [
            {"id": "diem_trinh", "label": "Diễm Trinh"},
            {"id": "hung_thinh", "label": "Hưng Thịnh"},
            {"id": "mai_linh", "label": "Mai Linh"},
            {"id": "mai_loan", "label": "Mai Loan"},
            {"id": "manh_dung", "label": "Mạnh Dũng"},
            {"id": "my_yen", "label": "Mỹ Yến"},
            {"id": "ngoc_huyen", "label": "Ngọc Huyền"},
            {"id": "phat_tai", "label": "Phát Tài"},
            {"id": "thanh_dat", "label": "Thành Đạt"},
            {"id": "thuc_trinh", "label": "Thục Trinh"},
            {"id": "tuan_ngoc", "label": "Tuấn Ngọc"},
            {"id": "storyvert", "label": "Storyvert"},
            {"id": "duc_an", "label": "Đức An"},
            {"id": "duc_duy", "label": "Đức Duy"},
        ],
    },
    "en": {
        "label": "English",
        "engine": "kokoro_en",
        "default_voice": "af_heart",
        "voices": [
            {"id": "af_heart", "label": "af_heart"},
        ],
    },
}

LANGUAGE_LABEL_TO_CODE = {
    AUTO_LANGUAGE_LABEL: "auto",
    **{details["label"]: code for code, details in LANGUAGES.items()},
}


def get_language_options():
    """Return the language labels shown in the UI."""
    return [AUTO_LANGUAGE_LABEL] + [
        details["label"] for details in LANGUAGES.values()
    ]


def get_language_code(language_label):
    """Convert a UI language label to its internal language code."""
    try:
        return LANGUAGE_LABEL_TO_CODE[language_label]
    except KeyError as error:
        raise ValueError(f"Ngôn ngữ không được hỗ trợ: {language_label}") from error


def get_voice_options(language_code):
    """Return voices available for a language, including automatic selection."""
    if language_code == "auto":
        return [AUTO_VOICE_LABEL]

    language = LANGUAGES.get(language_code)
    if language is None:
        raise ValueError(f"Ngôn ngữ không được hỗ trợ: {language_code}")

    return [AUTO_VOICE_LABEL] + [
        voice["label"] for voice in language["voices"]
    ]


def get_voice_id(language_code, voice_label):
    """Convert a UI voice label to its engine voice ID."""
    if voice_label == AUTO_VOICE_LABEL:
        return "auto"

    language = LANGUAGES.get(language_code)
    if language is None:
        raise ValueError(f"Ngôn ngữ không được hỗ trợ: {language_code}")

    for voice in language["voices"]:
        if voice["label"] == voice_label:
            return voice["id"]

    raise ValueError(
        f"Giọng đọc '{voice_label}' không khả dụng cho ngôn ngữ này."
    )


def get_default_voice(language_code):
    """Return the configured default voice ID for a language."""
    language = LANGUAGES.get(language_code)
    if language is None:
        raise ValueError(f"Ngôn ngữ không được hỗ trợ: {language_code}")
    return language["default_voice"]
