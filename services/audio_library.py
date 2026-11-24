from pathlib import Path
import re


PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"


def list_audio_files():
    """Return WAV recordings, newest first."""
    if not OUTPUT_DIR.exists():
        return []

    return sorted(
        (path for path in OUTPUT_DIR.iterdir() if path.is_file() and path.suffix.lower() == ".wav"),
        key=lambda path: path.stat().st_mtime,
        reverse=True
    )


def _safe_stem(name):
    stem = Path(str(name)).name
    stem = re.sub(r'[<>:"/\\|?*]', "", stem).strip().rstrip(". ")
    if stem.lower().endswith(".wav"):
        stem = stem[:-4].rstrip(". ")
    if not stem or stem in {".", ".."}:
        raise ValueError("Vui lòng nhập tên file hợp lệ.")

    # Tránh các tên thiết bị đặc biệt trên Windows.
    if re.fullmatch(r"(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", stem, re.IGNORECASE):
        stem = f"_{stem}"

    return stem


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
    destination = OUTPUT_DIR / f"{_safe_stem(new_name)}.wav"

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
