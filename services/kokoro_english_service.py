"""Persistent isolated Kokoro English engine with timeout and cancellation."""
import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

from services.voice_manager import LANGUAGES

PROJECT_DIR = Path(__file__).resolve().parent.parent
ENGLISH_PYTHON = (
    Path(os.environ["AVS_EN_PYTHON"]).expanduser()
    if os.environ.get("AVS_EN_PYTHON")
    else PROJECT_DIR / (".venv_en/Scripts/python.exe" if sys.platform.startswith("win") else ".venv_en/bin/python")
)
_WORKER_LOCK = threading.RLock()
_REQUEST_LOCK = threading.Lock()
_WORKER = None
_RESPONSE_QUEUE = None
_REQUEST_ID = 0


def _read_worker_output(process, responses):
    try:
        for line in process.stdout:
            try:
                responses.put(json.loads(line))
            except json.JSONDecodeError:
                responses.put({"ok": False, "error": "Phản hồi không hợp lệ từ English worker."})
    finally:
        responses.put({"ok": False, "error": "English worker đã kết thúc."})


def _stop_worker_locked():
    global _WORKER, _RESPONSE_QUEUE
    process = _WORKER
    _WORKER = None
    _RESPONSE_QUEUE = None
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)


def _ensure_worker():
    global _WORKER, _RESPONSE_QUEUE
    if _WORKER is not None and _WORKER.poll() is None:
        return
    if not ENGLISH_PYTHON.is_file():
        raise FileNotFoundError(
            f"Không tìm thấy Python engine tiếng Anh: {ENGLISH_PYTHON}. "
            "Hãy chạy scripts/setup_envs.ps1 hoặc scripts/setup_envs.sh."
        )
    process = subprocess.Popen(
        [str(ENGLISH_PYTHON), "-u", "-m", "services.kokoro_english_worker"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding="utf-8", errors="replace", cwd=PROJECT_DIR, bufsize=1,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    responses = queue.Queue()
    _WORKER = process
    _RESPONSE_QUEUE = responses
    threading.Thread(
        target=_read_worker_output, args=(process, responses), daemon=True
    ).start()


def cancel_active_generation():
    """Stop and reset the persistent English worker."""
    with _WORKER_LOCK:
        _stop_worker_locked()


def get_kokoro_language_code(voice_id):
    supported_ids = {voice["id"] for voice in LANGUAGES["en"]["voices"]}
    if voice_id not in supported_ids:
        raise ValueError(f"Giọng tiếng Anh Kokoro không hợp lệ: {voice_id}")
    return voice_id[0]


def generate_english_audio(
    text, voice="af_heart", speed=1.0, output_path="output/audio_en.wav",
    expression="natural", timeout=300, cancel_event=None,
):
    global _REQUEST_ID
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Vui lòng nhập nội dung văn bản.")
    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Đã hủy tạo giọng nói.")
    language_code = get_kokoro_language_code(voice)
    save_path = Path(output_path)
    if not save_path.is_absolute():
        save_path = PROJECT_DIR / save_path
    save_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = save_path.with_name(save_path.name + ".part")
    temporary_path.unlink(missing_ok=True)

    try:
        with _REQUEST_LOCK:
            with _WORKER_LOCK:
                _ensure_worker()
                process = _WORKER
                responses = _RESPONSE_QUEUE
                _REQUEST_ID += 1
                request_id = _REQUEST_ID
                request = {
                    "id": request_id, "text": text, "voice": voice,
                    "speed": float(speed), "output": str(save_path),
                    "expression": expression, "language_code": language_code,
                }
                try:
                    process.stdin.write(json.dumps(request, ensure_ascii=False) + "\\n")
                    process.stdin.flush()
                except (BrokenPipeError, OSError) as error:
                    _stop_worker_locked()
                    raise RuntimeError("Không thể gửi yêu cầu tới English worker.") from error
    
            deadline = time.monotonic() + timeout
            while True:
                if cancel_event is not None and cancel_event.is_set():
                    with _WORKER_LOCK:
                        _stop_worker_locked()
                    raise RuntimeError("Đã hủy tạo giọng nói.")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    with _WORKER_LOCK:
                        _stop_worker_locked()
                    raise TimeoutError(
                        "Quá thời gian chờ tạo giọng tiếng Anh. Hãy kiểm tra mạng "
                        "(lần đầu có thể cần tải model) rồi thử lại."
                    )
                try:
                    response = responses.get(timeout=min(0.2, remaining))
                except queue.Empty:
                    if process.poll() is not None:
                        with _WORKER_LOCK:
                            _stop_worker_locked()
                        raise RuntimeError("English worker đã dừng ngoài dự kiến.")
                    continue
                if response.get("id") != request_id:
                    if response.get("error"):
                        with _WORKER_LOCK:
                            _stop_worker_locked()
                        raise RuntimeError(response["error"])
                    continue
                if not response.get("ok"):
                    raise RuntimeError(response.get("error", "Không thể tạo giọng tiếng Anh."))
                break
    
        if not save_path.is_file():
            raise RuntimeError("English worker kết thúc nhưng không tạo được tệp WAV.")
        temporary_path.unlink(missing_ok=True)
        return save_path
    finally:
        temporary_path.unlink(missing_ok=True)
