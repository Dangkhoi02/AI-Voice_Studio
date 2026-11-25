from pathlib import Path
import re

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"
_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_stem(name, max_len=100):
    """Normalize a user-provided WAV name consistently on all platforms."""
    if not isinstance(max_len, int) or max_len < 1:
        raise ValueError("max_len must be a positive integer.")
    raw = str(name)
    # A path is a filename, not a request to select a nested directory.
    stem = raw
    stem = "".join("_" if (ord(char) < 32 or char in '<>:"/\\|?*') else char for char in stem)
    stem = stem.strip().rstrip(". ")
    if stem.lower().endswith(".wav"):
        stem = stem[:-4].rstrip(". ")
    stem = stem[:max_len].rstrip(". ")
    if not stem or stem in {".", ".."}:
        raise ValueError("Vui lòng nhập tên file hợp lệ.")
    if stem.split(".", 1)[0].upper() in _RESERVED_NAMES:
        stem = f"_{stem}"
    return stem


def list_audio_files():
    """Return WAV recordings, newest first."""
    if not OUTPUT_DIR.exists():
        return []
    return sorted(
        (path for path in OUTPUT_DIR.iterdir() if path.is_file() and path.suffix.lower() == ".wav"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def _validate_audio_path(file_path):
    output_dir = OUTPUT_DIR.resolve()
    path = Path(file_path).resolve()
    if path.parent != output_dir or path.suffix.lower() != ".wav":
        raise ValueError("Chỉ được thao tác với file WAV trong thư mục output.")
    if not path.is_file():
        raise FileNotFoundError("Không tìm thấy bản ghi âm.")
    return path


def rename_audio_file(file_path, new_name):
    source = _validate_audio_path(file_path)
    destination = OUTPUT_DIR / f"{sanitize_stem(new_name)}.wav"
    if destination.exists() and destination != source:
        raise FileExistsError("Tên file này đã tồn tại. Vui lòng chọn tên khác.")
    if destination == source:
        return source
    source.rename(destination)
    return destination


def delete_audio_file(file_path):
    path = _validate_audio_path(file_path)
    path.unlink()
    return path
