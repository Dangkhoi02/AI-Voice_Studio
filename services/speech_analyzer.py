"""Text segmentation and pause profiles for expressive speech delivery."""
import re

EXPRESSION_PROFILES = {
    "natural": {"label": "Tự nhiên", "sentence_pause_ms": 220, "clause_pause_ms": 100},
    "enthusiastic": {"label": "Hào hứng", "sentence_pause_ms": 150, "clause_pause_ms": 70},
    "gentle": {"label": "Nhẹ nhàng", "sentence_pause_ms": 320, "clause_pause_ms": 150},
    "serious": {"label": "Nghiêm túc", "sentence_pause_ms": 280, "clause_pause_ms": 120},
}

_SEGMENT_PATTERN = re.compile(r"(?<=[,;:])\s+|(?<=[.!?…])\s+")
_ABBREVIATIONS = {
    "tp.", "q.", "p.", "tt.", "mr.", "mrs.", "ms.", "dr.", "st.", "vs.",
    "pgs.", "gs.", "ts.", "ths.", "etc.",
}
_NUMBERING_PATTERN = re.compile(r"\d{1,3}[.)]")


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
    return (
        words[-1].lower() in _ABBREVIATIONS
        or bool(_NUMBERING_PATTERN.fullmatch(words[-1]))
        or bool(_INITIAL_PATTERN.fullmatch(words[-1]))
    )


def _merge_non_boundaries(parts):
    merged = []
    carry = ""
    for part in parts:
        part = (carry + " " + part).strip() if carry else part
        carry = ""
        if _is_non_boundary(part):
            carry = part
        else:
            merged.append(part)
    if carry:
        if merged:
            merged[-1] = (merged[-1] + " " + carry).strip()
        else:
            merged.append(carry)
    return merged


def _split_long_segment(segment, max_chars):
    words = segment.split()
    chunks = []
    current = ""
    for word in words:
        if len(word) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(
                word[index:index + max_chars]
                for index in range(0, len(word), max_chars)
            )
            continue
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def split_text_segments(text, max_chars=180):
    """Split at punctuation, then wrap long punctuation-free text by words."""
    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    if not normalized:
        return []
    if not isinstance(max_chars, int) or max_chars < 20:
        raise ValueError("max_chars must be an integer of at least 20.")
    parts = [part.strip() for part in _SEGMENT_PATTERN.split(normalized) if part.strip()]
    parts = _merge_non_boundaries(parts)
    segments = []
    for part in parts:
        chunks = _split_long_segment(part, max_chars)
        if len(chunks) > 1:
            # Keep punctuation attached to the final chunk of its sentence.
            segments.extend(chunks)
        else:
            segments.append(part)
    return segments


def pause_after_segment(segment, expression="natural"):
    profile = EXPRESSION_PROFILES.get(expression)
    if profile is None:
        raise ValueError(f"Sắc thái đọc không hợp lệ: {expression}")
    ending = segment.rstrip()[-1:] if isinstance(segment, str) and segment.strip() else ""
    if not ending:
        return 0
    if ending in ".!?…":
        return profile["sentence_pause_ms"]
    if ending in ",;:":
        return profile["clause_pause_ms"]
    return 0
