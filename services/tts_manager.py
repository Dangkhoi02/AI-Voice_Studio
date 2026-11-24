from pathlib import Path
import re

from services.kokoro_service import generate_vietnamese_audio
from services.kokoro_english_service import generate_english_audio
from services.voice_manager import get_default_voice
from services.style_manager import get_style_speed, get_speech_style
from services.speech_analyzer import EXPRESSION_PROFILES


PROJECT_DIR = Path(__file__).resolve().parent.parent


def detect_language(text):
    vietnamese_chars = (
        "ăâđêôơư" "áàảãạ" "ấầẩẫậ" "ắằẳẵặ" "éèẻẽẹ" "ếềểễệ"
        "íìỉĩị" "óòỏõọ" "ốồổỗộ" "ớờởỡợ" "úùủũụ" "ứừửữự"
        "ýỳỷỹỵ"
    )
    return "vi" if any(char in text.lower() for char in vietnamese_chars) else "en"


def create_unique_filename(file_name, output_dir=None):
    safe_name = re.sub(r'[<>:"/\\|?*]', "", file_name).strip().rstrip(".")
    if not safe_name:
        raise ValueError("Vui lòng nhập tên file hợp lệ.")
    output_dir = Path(output_dir) if output_dir is not None else PROJECT_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{safe_name}.wav"
    counter = 2
    while file_path.exists():
        file_path = output_dir / f"{safe_name}_{counter}.wav"
        counter += 1
    return file_path


def generate_audio(
    text,
    language="auto",
    voice=None,
    speed=None,
    style="conversation",
    expression="natural",
    file_name="audio",
    output_dir=None,
):
    if not text or not text.strip():
        raise ValueError("Vui lòng nhập nội dung văn bản.")
    if expression not in EXPRESSION_PROFILES:
        raise ValueError(f"Sắc thái đọc không hợp lệ: {expression}")

    auto_language = language == "auto"
    if auto_language:
        language = detect_language(text)
    if auto_language or voice in (None, "auto"):
        voice = get_default_voice(language)

    get_speech_style(style, language)
    effective_speed = get_style_speed(style, language) if speed is None else float(speed)
    save_path = create_unique_filename(file_name, output_dir=output_dir)
    output_path = str(save_path.relative_to(PROJECT_DIR))

    if language == "vi":
        return generate_vietnamese_audio(
            text=text, voice=voice or "diem_trinh", speed=effective_speed,
            output_path=output_path, expression=expression,
        )
    if language == "en":
        return generate_english_audio(
            text=text, voice=voice or "af_heart", speed=effective_speed,
            output_path=output_path, expression=expression,
        )
    raise ValueError("Ngôn ngữ không được hỗ trợ.")



def generate_preview_audio(
    text,
    language="auto",
    voice=None,
    speed=None,
    style="conversation",
    expression="natural",
):
    """Generate a temporary preview WAV outside the main Audio Library."""
    preview_dir = PROJECT_DIR / "output" / ".preview"
    preview_file = preview_dir / "voice_preview.wav"
    preview_dir.mkdir(parents=True, exist_ok=True)
    if preview_file.exists():
        preview_file.unlink()

    return generate_audio(
        text=text,
        language=language,
        voice=voice,
        speed=speed,
        style=style,
        expression=expression,
        file_name="voice_preview",
        output_dir=preview_dir,
    )
