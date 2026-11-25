"""Text segmentation and pause profiles for expressive speech delivery."""
import re

EXPRESSION_PROFILES = {
    "natural": {"label": "Tự nhiên", "sentence_pause_ms": 220, "clause_pause_ms": 100},
    "enthusiastic": {"label": "Hào hứng", "sentence_pause_ms": 150, "clause_pause_ms": 70},
    "gentle": {"label": "Nhẹ nhàng", "sentence_pause_ms": 320, "clause_pause_ms": 150},
    "serious": {"label": "Nghiêm túc", "sentence_pause_ms": 280, "clause_pause_ms": 120},
}

_SEGMENT_PATTERN = re.compile(r"(?<=[,;:])\\s+|(?<=[.!?…])\\s+")
_ABBREVIATIONS = {
    "tp.", "q.", "p.", "tt.", "mr.", "mrs.", "ms.", "dr.", "st.", "vs.",
    "ths.", "ts.", "pgs.", "gs.", "vd.", "etc.",
}
_NUMBERING = re.compile(r"\\d{1,3}[.)]")
_INITIAL = re.compile(r"[A-ZĐ]\\.", re.IGNORECASE)


def get_expression_options():
    return [profile["label"] for profile in EXPRESSION_PROFILES.values()]


def get_expression_id(label):
    for expression_id, profile in EXPRESSION_PROFILES.items():
        if profile["label"] == label:
            return expression_id
    raise ValueError(f"Không tìm thấy sắc thái đọc: {label}")


def _is_non_boundary(part):
    words = part.split()
    if not words:
        return False
    last = words[-1].lower()
    return last in _ABBREVIATIONS or bool(_NUMBERING.fullmatch(last)) or bool(_INITIAL.fullmatch(words[-1]))


def _merge_non_boundaries(parts):
    merged, carry = [], ""
    for part in parts:
        current = f"{carry} {part}".strip() if carry else part
        carry = ""
        if _is_non_boundary(current):
            carry = current
        else:
            merged.append(current)
    if carry:
        merged.append(carry)
    return merged


def _wrap_long(segment, limit=180):
    words = segment.split()
    if not words:
        return []
    result, current = [], ""
    for word in words:
        if current and len(current) + 1 + len(word) > limit:
            result.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        result.append(current)
    return result


def split_text_segments(text, max_chars=180):
    normalized = re.sub(r"\\s+", " ", str(text or "")).strip()
    if not normalized:
        return []
    raw_parts = [part.strip() for part in _SEGMENT_PATTERN.split(normalized) if part.strip()]
    merged = _merge_non_boundaries(raw_parts)
    return [chunk for part in merged for chunk in _wrap_long(part, max_chars)]


def pause_after_segment(segment, expression="natural"):
    profile = EXPRESSION_PROFILES.get(expression)
    if profile is None:
        raise ValueError(f"Sắc thái đọc không hợp lệ: {expression}")
    ending = segment.rstrip()[-1:] if segment and segment.rstrip() else ""
    if not ending:
        return 0
    if ending in ".!?…":
        return profile["sentence_pause_ms"]
    if ending in ",;:":
        return profile["clause_pause_ms"]
    return 0
