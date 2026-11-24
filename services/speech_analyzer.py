"""Text segmentation and pause profiles for expressive speech delivery."""
import re


EXPRESSION_PROFILES = {
    "natural": {"label": "Tự nhiên", "sentence_pause_ms": 220, "clause_pause_ms": 100},
    "enthusiastic": {"label": "Hào hứng", "sentence_pause_ms": 150, "clause_pause_ms": 70},
    "gentle": {"label": "Nhẹ nhàng", "sentence_pause_ms": 320, "clause_pause_ms": 150},
    "serious": {"label": "Nghiêm túc", "sentence_pause_ms": 280, "clause_pause_ms": 120},
}

_SEGMENT_PATTERN = re.compile(r"(?<=[,;:])\s+|(?<=[.!?…])\s+")


def get_expression_options():
    return [profile["label"] for profile in EXPRESSION_PROFILES.values()]


def get_expression_id(label):
    for expression_id, profile in EXPRESSION_PROFILES.items():
        if profile["label"] == label:
            return expression_id
    raise ValueError(f"Không tìm thấy sắc thái đọc: {label}")


def split_text_segments(text):
    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    if not normalized:
        return []
    return [part.strip() for part in _SEGMENT_PATTERN.split(normalized) if part.strip()]


def pause_after_segment(segment, expression="natural"):
    profile = EXPRESSION_PROFILES.get(expression)
    if profile is None:
        raise ValueError(f"Sắc thái đọc không hợp lệ: {expression}")
    ending = segment.rstrip()[-1:] if segment and segment.rstrip() else ""
    if ending in ".!?…":
        return profile["sentence_pause_ms"]
    if ending in ",;:":
        return profile["clause_pause_ms"]
    return 0
