"""Isolated Kokoro English engine with timeout and cancellation support."""
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from services.voice_manager import LANGUAGES

PROJECT_DIR = Path(__file__).resolve().parent.parent
_PROCESS_LOCK = threading.RLock()
_ACTIVE_PROCESS = None


def _venv_python():
    override = os.environ.get("AVS_EN_PYTHON")
    if override:
        return Path(override).expanduser()
    parts = ("Scripts", "python.exe") if sys.platform.startswith("win") else ("bin", "python")
    return PROJECT_DIR.joinpath(".venv_en", *parts)


ENGLISH_PYTHON = _venv_python()


def cancel_active_generation():
    """Terminate the active English worker, if one is running."""
    with _PROCESS_LOCK:
        process = _ACTIVE_PROCESS
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()


def get_kokoro_language_code(voice_id):
    supported_ids = {voice["id"] for voice in LANGUAGES["en"]["voices"]}
    if voice_id not in supported_ids:
        raise ValueError(f"Giọng tiếng Anh Kokoro không hợp lệ: {voice_id}")
    return voice_id[0]


def generate_english_audio(
    text, voice="af_heart", speed=1.0, output_path="output/audio_en.wav",
    expression="natural", timeout=300, cancel_event=None,
):
    global _ACTIVE_PROCESS
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Vui lòng nhập nội dung văn bản.")
    python_executable = _venv_python()
    if not python_executable.is_file():
        raise FileNotFoundError(
            f"Không tìm thấy Python engine tiếng Anh: {python_executable}. "
            "Hãy chạy scripts/setup_envs.ps1 hoặc scripts/setup_envs.sh."
        )
    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Đã hủy tạo giọng nói.")

    pipeline_language = get_kokoro_language_code(voice)
    script = r'''
import json
import os
import re
import sys
import numpy as np
import soundfile as sf
from kokoro import KPipeline

text = sys.stdin.read()
voice, speed, output, expression, language_code = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
pause_profiles = {
    "natural": (220, 100), "enthusiastic": (150, 70),
    "gentle": (320, 150), "serious": (280, 120),
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
temporary = output + ".part"
sf.write(temporary, np.concatenate(parts), 24000)
os.replace(temporary, output)
print("ENGLISH_AUDIO_CREATED")
'''
    save_path = Path(output_path)
    if not save_path.is_absolute():
        save_path = PROJECT_DIR / save_path
    save_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = save_path.with_name(save_path.name + ".part")
    temporary_path.unlink(missing_ok=True)
    env = {**os.environ, "PYTHONUTF8": "1"}
    process = subprocess.Popen(
        [str(python_executable), "-u", "-c", script, voice, str(speed),
         str(save_path), expression, pipeline_language],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", cwd=PROJECT_DIR, env=env,
    )
    with _PROCESS_LOCK:
        _ACTIVE_PROCESS = process
    try:
        try:
            stdout, stderr = process.communicate(input=text, timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise TimeoutError(
                "Quá thời gian chờ tạo giọng tiếng Anh. Hãy kiểm tra kết nối mạng "
                "(lần đầu có thể cần tải model) rồi thử lại."
            )
        if cancel_event is not None and cancel_event.is_set():
            raise RuntimeError("Đã hủy tạo giọng nói.")
        if process.returncode != 0:
            detail = (stderr or "").strip()
            raise RuntimeError(detail[-1800:] if detail else "Không thể tạo giọng tiếng Anh.")
        if not save_path.is_file():
            raise RuntimeError("Engine tiếng Anh kết thúc nhưng không tạo được tệp WAV.")
        return save_path
    finally:
        with _PROCESS_LOCK:
            if _ACTIVE_PROCESS is process:
                _ACTIVE_PROCESS = None
        if process.poll() is None:
            process.kill()
            process.wait()
        temporary_path.unlink(missing_ok=True)
