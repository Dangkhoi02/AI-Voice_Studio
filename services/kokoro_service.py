
from pathlib import Path

import soundfile as sf
from kokoro_vietnamese import KokoroVietnamese, SAMPLE_RATE


PROJECT_DIR = Path(__file__).resolve().parent.parent

# Lưu model để không phải khởi tạo lại mỗi lần tạo âm thanh
_tts = None


def get_tts(voice="diem_trinh"):
    global _tts

    if _tts is None:
        _tts = KokoroVietnamese(
            voice=voice,
            device="cpu"
        )

    return _tts


def generate_vietnamese_audio(
    text,
    voice="diem_trinh",
    speed=1.0,
    output_path="output/audio_vi.wav"
):
    if not text.strip():
        raise ValueError("Vui lòng nhập nội dung văn bản.")

    tts = get_tts(voice)

    audio, phonemes = tts.synthesize(
        text,
        speed=speed
    )

    save_path = PROJECT_DIR / output_path
    save_path.parent.mkdir(parents=True, exist_ok=True)

    sf.write(
        str(save_path),
        audio,
        SAMPLE_RATE
    )

    return save_path
