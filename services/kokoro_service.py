"""Persistent Vietnamese Kokoro engine with cancellation and bounded waits."""
import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
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
                responses.put({"ok": False, "error": "Phản hồi không hợp lệ từ Vietnamese worker."})
    finally:
        responses.put({"ok": False, "error": "Vietnamese worker đã kết thúc."})


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


def cancel_active_generation():
    """Terminate the active Vietnamese synthesis worker."""
    with _WORKER_LOCK:
        _stop_worker_locked()


def _ensure_worker():
    global _WORKER, _RESPONSE_QUEUE
    if _WORKER is not None and _WORKER.poll() is None:
        return
    process = subprocess.Popen(
        [sys.executable, "-u", "-m", "services.kokoro_vietnamese_worker"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding="utf-8", errors="replace", cwd=PROJECT_DIR, bufsize=1,
    )
    responses = queue.Queue()
    _WORKER = process
    _RESPONSE_QUEUE = responses
    threading.Thread(
        target=_read_worker_output, args=(process, responses), daemon=True
    ).start()


def generate_vietnamese_audio(
    text, voice="diem_trinh", speed=1.0, output_path="output/audio_vi.wav",
    expression="natural", cancel_event=None, timeout=300,
):
    global _REQUEST_ID
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Vui lòng nhập nội dung văn bản.")
    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Đã hủy tạo giọng nói.")
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
                    "expression": expression,
                }
                try:
                    process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
                    process.stdin.flush()
                except (BrokenPipeError, OSError) as error:
                    _stop_worker_locked()
                    raise RuntimeError("Không thể gửi yêu cầu tới Vietnamese worker.") from error
    
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
                    raise TimeoutError("Quá thời gian chờ tạo giọng tiếng Việt. Hãy thử lại.")
                try:
                    response = responses.get(timeout=min(0.2, remaining))
                except queue.Empty:
                    if process.poll() is not None:
                        with _WORKER_LOCK:
                            _stop_worker_locked()
                        raise RuntimeError("Vietnamese worker đã dừng ngoài dự kiến.")
                    continue
                if response.get("id") != request_id:
                    if response.get("error"):
                        with _WORKER_LOCK:
                            _stop_worker_locked()
                        raise RuntimeError(response["error"])
                    continue
                if not response.get("ok"):
                    raise RuntimeError(response.get("error", "Không thể tạo giọng tiếng Việt."))
                break
    
        if not save_path.is_file():
            raise RuntimeError("Vietnamese worker kết thúc nhưng không tạo được tệp WAV.")
        temporary_path.unlink(missing_ok=True)
        return save_path
    finally:
        temporary_path.unlink(missing_ok=True)
