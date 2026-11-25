"""Vietnamese Kokoro engine with serialized model access and atomic WAV writes."""
from pathlib import Path
import threading

import numpy as np
import soundfile as sf
from kokoro_vietnamese import KokoroVietnamese, SAMPLE_RATE

from services.speech_analyzer import split_text_segments, pause_after_segment

PROJECT_DIR = Path(__file__).resolve().parent.parent
_tts = None
_tts_voice = None
_TTS_LOCK = threading.RLock()


def get_tts(voice="diem_trinh"):
    global _tts, _tts_voice
    requested_voice = voice or "diem_trinh"
    with _TTS_LOCK:
        if _tts is None or _tts_voice != requested_voice:
            _tts = KokoroVietnamese(voice=requested_voice, device="cpu")
            _tts_voice = requested_voice
        return _tts


def generate_vietnamese_audio(
    text, voice="diem_trinh", speed=1.0, output_path="output/audio_vi.wav",
    expression="natural", cancel_event=None,
):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Vui lòng nhập nội dung văn bản.")
    segments = split_text_segments(text)
    if not segments:
        raise ValueError("Không có nội dung hợp lệ để tạo giọng nói.")
    audio_parts = []
    with _TTS_LOCK:
        tts = get_tts(voice)
        for index, segment in enumerate(segments):
            if cancel_event is not None and cancel_event.is_set():
                raise RuntimeError("Đã hủy tạo giọng nói.")
            try:
                audio, _ = tts.synthesize(segment, speed=speed)
            except ValueError as error:
                if "too long" in str(error).lower() or "phoneme" in str(error).lower():
                    raise ValueError(
                        "Một đoạn văn bản vẫn quá dài để tổng hợp. "
                        "Hãy thêm dấu câu hoặc chia nhỏ nội dung."
                    ) from error
                raise
            audio_parts.append(np.asarray(audio, dtype=np.float32))
            if index < len(segments) - 1:
                pause_ms = pause_after_segment(segment, expression)
                if pause_ms:
                    audio_parts.append(
                        np.zeros(int(SAMPLE_RATE * pause_ms / 1000), dtype=np.float32)
                    )
    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Đã hủy tạo giọng nói.")
    if not audio_parts:
        raise RuntimeError("Không tạo được âm thanh từ văn bản.")
    combined_audio = np.concatenate(audio_parts)
    save_path = Path(output_path)
    if not save_path.is_absolute():
        save_path = PROJECT_DIR / save_path
    save_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = save_path.with_name(save_path.name + ".part")
    try:
        sf.write(str(temporary_path), combined_audio, SAMPLE_RATE)
        if cancel_event is not None and cancel_event.is_set():
            raise RuntimeError("Đã hủy tạo giọng nói.")
        temporary_path.replace(save_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return save_path
