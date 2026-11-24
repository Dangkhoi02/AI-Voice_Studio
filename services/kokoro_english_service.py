import subprocess
from pathlib import Path

from services.voice_manager import LANGUAGES


PROJECT_DIR = Path(__file__).resolve().parent.parent
ENGLISH_PYTHON = PROJECT_DIR / ".venv_en" / "Scripts" / "python.exe"


def get_kokoro_language_code(voice_id):
    """Resolve Kokoro's pipeline code from a supported English voice ID."""
    supported_ids = {voice["id"] for voice in LANGUAGES["en"]["voices"]}
    if voice_id not in supported_ids:
        raise ValueError(f"Giọng tiếng Anh Kokoro không hợp lệ: {voice_id}")
    return voice_id[0]


def generate_english_audio(
    text,
    voice="af_heart",
    speed=1.0,
    output_path="output/audio_en.wav",
    expression="natural",
):
    if not text or not text.strip():
        raise ValueError("Vui lòng nhập nội dung văn bản.")
    if not ENGLISH_PYTHON.exists():
        raise FileNotFoundError("Không tìm thấy môi trường .venv_en.")

    pipeline_language = get_kokoro_language_code(voice)

    script = r'''
import sys
import re
import numpy as np
import soundfile as sf
from kokoro import KPipeline

text, voice, language_code = sys.argv[1], sys.argv[2], sys.argv[6]
speed, output, expression = float(sys.argv[3]), sys.argv[4], sys.argv[5]
pause_profiles = {
    "natural": (220, 100),
    "enthusiastic": (150, 70),
    "gentle": (320, 150),
    "serious": (280, 120),
}
sentence_pause, clause_pause = pause_profiles.get(expression, pause_profiles["natural"])
segments = [part.strip() for part in re.split(r"(?<=[,;:])\s+|(?<=[.!?…])\s+", re.sub(r"\s+", " ", text.strip())) if part.strip()]
pipeline = KPipeline(lang_code=language_code)
parts = []

for index, segment in enumerate(segments):
    chunks = [audio for _, _, audio in pipeline(segment, voice=voice, speed=speed)]
    if not chunks:
        continue
    parts.append(np.concatenate(chunks))
    if index < len(segments) - 1:
        ending = segment.rstrip()[-1:]
        pause_ms = sentence_pause if ending in ".!?…" else clause_pause if ending in ",;:" else 0
        if pause_ms:
            parts.append(np.zeros(int(24000 * pause_ms / 1000), dtype=np.float32))

if not parts:
    raise RuntimeError("Kokoro không tạo được âm thanh.")
sf.write(output, np.concatenate(parts), 24000)
print("ENGLISH_AUDIO_CREATED")
'''

    save_path = PROJECT_DIR / output_path
    save_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [str(ENGLISH_PYTHON), "-c", script, text, voice, str(speed), str(save_path), expression, pipeline_language],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Lỗi tạo giọng tiếng Anh.")
    return save_path
