
from pathlib import Path
import re

from services.kokoro_service import generate_vietnamese_audio
from services.kokoro_english_service import generate_english_audio
from services.voice_manager import get_default_voice


PROJECT_DIR = Path(__file__).resolve().parent.parent


def detect_language(text):
    vietnamese_chars = (
        "ăâđêôơư"
        "áàảãạ"
        "ấầẩẫậ"
        "ắằẳẵặ"
        "éèẻẽẹ"
        "ếềểễệ"
        "íìỉĩị"
        "óòỏõọ"
        "ốồổỗộ"
        "ớờởỡợ"
        "úùủũụ"
        "ứừửữự"
        "ýỳỷỹỵ"
    )

    if any(char in text.lower() for char in vietnamese_chars):
        return "vi"

    return "en"


def create_unique_filename(file_name):
    # Loai bo ky tu khong hop le tren Windows
    safe_name = re.sub(r'[<>:"/\\|?*]', "", file_name).strip()
    safe_name = safe_name.rstrip(".")

    if not safe_name:
        raise ValueError("Vui long nhap ten file hop le.")

    output_dir = PROJECT_DIR / "output"
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
    speed=1.0,
    file_name="audio"
):
    if not text or not text.strip():
        raise ValueError("Vui long nhap noi dung van ban.")

    auto_language = language == "auto"
    if auto_language:
        language = detect_language(text)

    # Resolve the default voice from the central voice catalog.
    # Automatic language detection keeps the existing behavior: use that
    # language's default voice rather than a voice from another language.
    if auto_language or voice in (None, "auto"):
        voice = get_default_voice(language)

    save_path = create_unique_filename(file_name)

    output_path = str(save_path.relative_to(PROJECT_DIR))

    if language == "vi":
        return generate_vietnamese_audio(
            text=text,
            voice=voice or "diem_trinh",
            speed=speed,
            output_path=output_path
        )

    elif language == "en":
        return generate_english_audio(
            text=text,
            voice=voice or "af_heart",
            speed=speed,
            output_path=output_path
        )

    else:
        raise ValueError("Ngon ngu khong duoc ho tro.")
