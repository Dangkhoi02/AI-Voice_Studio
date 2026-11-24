
from pathlib import Path
import re
import sys

import soundfile as sf
from kokoro import KPipeline
import numpy as np


def create_unique_output(output_dir, file_name):
    safe_name = re.sub(r'[<>:"/\\|?*]', "", file_name).strip()
    safe_name = Path(safe_name).stem.rstrip(".")

    if not safe_name:
        raise ValueError("Ten file khong hop le.")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{safe_name}.wav"
    counter = 2

    while output_file.exists():
        output_file = output_dir / f"{safe_name}_{counter}.wav"
        counter += 1

    return output_file


def generate_english_audio(text, file_name="test_en", voice="af_heart", speed=1.0):
    print("Dang khoi tao Kokoro English...")

    pipeline = KPipeline(lang_code="a")

    print("Dang tao am thanh...")

    audio_chunks = []

    for _, _, audio in pipeline(text, voice=voice, speed=speed):
        audio_chunks.append(audio)

    if not audio_chunks:
        raise RuntimeError("Khong tao duoc am thanh.")

    audio = np.concatenate(audio_chunks)

    output_dir = Path("output")
    output_file = create_unique_output(output_dir, file_name)

    sf.write(str(output_file), audio, 24000)

    print("Tao am thanh thanh cong!")
    print(f"File: {output_file.resolve()}")
    return output_file


def main():
    text = "Hello! Welcome to AI Voice Studio. This is an English voice test."
    file_name = sys.argv[1] if len(sys.argv) > 1 else "test_en"
    generate_english_audio(text, file_name=file_name)

if __name__ == "__main__":
    main()
