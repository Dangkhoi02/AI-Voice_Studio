from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_vietnamese import KokoroVietnamese, SAMPLE_RATE

from services.speech_analyzer import split_text_segments, pause_after_segment


PROJECT_DIR = Path(__file__).resolve().parent.parent
_tts = None
_tts_voice = None


def get_tts(voice="diem_trinh"):
    global _tts, _tts_voice
    requested_voice = voice or "diem_trinh"
    if _tts is None or _tts_voice != requested_voice:
        _tts = KokoroVietnamese(voice=requested_voice, device="cpu")
        _tts_voice = requested_voice
    return _tts


def generate_vietnamese_audio(
    text,
    voice="diem_trinh",
    speed=1.0,
    output_path="output/audio_vi.wav",
    expression="natural",
):
    if not text or not text.strip():
        raise ValueError("Vui lòng nhập nội dung văn bản.")

    tts = get_tts(voice)
    segments = split_text_segments(text)
    audio_parts = []

    for index, segment in enumerate(segments):
        audio, _ = tts.synthesize(segment, speed=speed)
        audio_parts.append(np.asarray(audio, dtype=np.float32))
        if index < len(segments) - 1:
            pause_ms = pause_after_segment(segment, expression)
            if pause_ms:
                silence = np.zeros(int(SAMPLE_RATE * pause_ms / 1000), dtype=np.float32)
                audio_parts.append(silence)

    if not audio_parts:
        raise RuntimeError("Không tạo được âm thanh từ văn bản.")

    combined_audio = np.concatenate(audio_parts)
    save_path = PROJECT_DIR / output_path
    save_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(save_path), combined_audio, SAMPLE_RATE)
    return save_path
