from pathlib import Path

import soundfile as sf
from kokoro_vietnamese import KokoroVietnamese, SAMPLE_RATE


PROJECT_DIR = Path(__file__).resolve().parent.parent

_tts = None
_tts_voice = None


def get_tts(voice="diem_trinh"):
    global _tts, _tts_voice

    requested_voice = voice or "diem_trinh"

    if _tts is None or _tts_voice != requested_voice:
        _tts = KokoroVietnamese(
            voice=requested_voice,
            device="cpu"
        )
        _tts_voice = requested_voice

    return _tts


def generate_vietnamese_audio(
    text,
    voice="diem_trinh",
    speed=1.0,
    output_path="output/audio_vi.wav"
):
    if not text or not text.strip():
        raise ValueError("Vui long nhap noi dung van ban.")

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
