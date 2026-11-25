from pathlib import Path
import unicodedata

from services.audio_library import sanitize_stem
from services.kokoro_service import generate_vietnamese_audio, cancel_active_generation as cancel_vietnamese_generation
from services.kokoro_english_service import generate_english_audio, cancel_active_generation as cancel_english_generation
from services.voice_manager import LANGUAGES, get_default_voice
from services.style_manager import get_style_speed, get_speech_style
from services.speech_analyzer import EXPRESSION_PROFILES

PROJECT_DIR = Path(__file__).resolve().parent.parent
_VI_ONLY = set(
    "ăắằẳẵặơớờởỡợưứừửựđạảẹẻẽịỉĩọỏụủũỳỵỷỹ"
    "ấầẩẫậếềểễệốồổộ"
)
_VI_COMMON_WORDS = {
    "xin", "chao", "chào", "toi", "tôi", "la", "là", "cac", "các",
    "ban", "bạn", "minh", "mình", "khong", "không", "nguoi", "người",
    "viet", "việt", "nam", "cam", "cảm", "on", "ơn", "duoc", "được",
    "mot", "một", "xin", "này", "đây", "và", "của", "là", "những",
}


def cancel_active_generation():
    """Cancel either persistent engine worker, if active."""
    cancel_vietnamese_generation()
    cancel_english_generation()


def detect_language(text):
    """Best-effort Vietnamese/English detection for the current two-engine app."""
    normalized = unicodedata.normalize("NFC", str(text or "")).lower()
    letters = [char for char in normalized if char.isalpha()]
    if not letters:
        return "en"
    if any(ord(char) > 0x024F for char in letters):
        raise ValueError("Ngôn ngữ này hiện chưa được hỗ trợ. Hãy chọn Tiếng Việt hoặc English.")
    vi_ratio = sum(char in _VI_ONLY for char in letters) / len(letters)
    if vi_ratio >= 0.02:
        return "vi"
    words = {word.strip(".,!?;:()[]{}\"'") for word in normalized.split()}
    if len(words & _VI_COMMON_WORDS) >= 2:
        return "vi"
    return "en"


def create_unique_filename(file_name, output_dir=None):
    stem = sanitize_stem(file_name)
    output_dir = Path(output_dir) if output_dir is not None else PROJECT_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{stem}.wav"
    counter = 2
    while file_path.exists():
        file_path = output_dir / f"{stem}_{counter}.wav"
        counter += 1
    return file_path


def generate_audio(
    text, language="auto", voice=None, speed=None, style="conversation",
    expression="natural", file_name="audio", output_dir=None, cancel_event=None,
):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Vui lòng nhập nội dung văn bản.")
    if language == "auto":
        language = detect_language(text)
    if language not in LANGUAGES:
        raise ValueError(f"Ngôn ngữ không được hỗ trợ: {language}")
    if expression not in EXPRESSION_PROFILES:
        raise ValueError(f"Sắc thái đọc không hợp lệ: {expression}")

    voice = get_default_voice(language) if voice in (None, "auto") else voice
    supported_voice_ids = {item["id"] for item in LANGUAGES[language]["voices"]}
    if voice not in supported_voice_ids:
        raise ValueError(f"Giọng đọc '{voice}' không khả dụng cho ngôn ngữ {language}.")
    get_speech_style(style, language)
    effective_speed = get_style_speed(style, language) if speed is None else float(speed)
    if not 0.5 <= effective_speed <= 2.0:
        raise ValueError("Tốc độ đọc phải nằm trong khoảng 0.5 đến 2.0.")

    save_path = create_unique_filename(file_name, output_dir=output_dir)
    try:
        output_path = str(save_path.relative_to(PROJECT_DIR))
    except ValueError:
        output_path = str(save_path)

    engine = generate_vietnamese_audio if language == "vi" else generate_english_audio
    return engine(
        text=text, voice=voice, speed=effective_speed,
        output_path=output_path, expression=expression, cancel_event=cancel_event,
    )


def preview_excerpt(text, max_chars=200):
    """Return a short, sentence-aware preview excerpt."""
    normalized = " ".join(str(text or "").split())
    if len(normalized) <= max_chars:
        return normalized
    cut = normalized[:max_chars]
    positions = [cut.rfind(mark) for mark in (". ", "! ", "? ", "… ", ", ")]
    boundary = max(positions)
    return cut[:boundary + 1].strip() if boundary > 40 else cut.rstrip() + "…"


def generate_preview_audio(
    text, language="auto", voice=None, speed=None, style="conversation",
    expression="natural", cancel_event=None,
):
    preview_dir = PROJECT_DIR / "output" / ".preview"
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_file = preview_dir / "voice_preview.wav"
    preview_file.unlink(missing_ok=True)
    return generate_audio(
        text=preview_excerpt(text), language=language, voice=voice, speed=speed,
        style=style, expression=expression, file_name="voice_preview",
        output_dir=preview_dir, cancel_event=cancel_event,
    )
