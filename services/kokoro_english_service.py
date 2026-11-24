
import subprocess
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent

# Sử dụng Python 3.12 trong môi trường riêng
ENGLISH_PYTHON = PROJECT_DIR / ".venv_en" / "Scripts" / "python.exe"


def generate_english_audio(
    text,
    voice="af_heart",
    speed=1.0,
    output_path="output/audio_en.wav"
):
    if not text or not text.strip():
        raise ValueError("Vui lòng nhập nội dung văn bản.")

    if not ENGLISH_PYTHON.exists():
        raise FileNotFoundError("Không tìm thấy môi trường .venv_en.")

    script = r'''
import sys
import numpy as np
import soundfile as sf
from kokoro import KPipeline

text = sys.argv[1]
voice = sys.argv[2]
speed = float(sys.argv[3])
output = sys.argv[4]

pipeline = KPipeline(lang_code="a")
chunks = []

for _, _, audio in pipeline(text, voice=voice, speed=speed):
    chunks.append(audio)

if not chunks:
    raise RuntimeError("Kokoro không tạo được âm thanh.")

audio = np.concatenate(chunks)
sf.write(output, audio, 24000)

print("ENGLISH_AUDIO_CREATED")
'''

    save_path = PROJECT_DIR / output_path
    save_path.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            str(ENGLISH_PYTHON),
            "-c",
            script,
            text,
            voice,
            str(speed),
            str(save_path)
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Lỗi tạo giọng tiếng Anh.")

    return save_path
