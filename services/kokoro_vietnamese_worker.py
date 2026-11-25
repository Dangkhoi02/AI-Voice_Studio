"""Persistent Kokoro Vietnamese worker process."""
import json
import os
import re
import sys
import traceback
import contextlib

import numpy as np
import soundfile as sf

_PROTOCOL_OUT = sys.stdout
with contextlib.redirect_stdout(sys.stderr):
    from kokoro_vietnamese import KokoroVietnamese, SAMPLE_RATE
from services.speech_analyzer import split_text_segments
_MODEL = None
_VOICE = None
_PAUSES = {
    "natural": (220, 100), "enthusiastic": (150, 70),
    "gentle": (320, 150), "serious": (280, 120),
}


def _synthesize(request):
    voice = request["voice"]
    global _MODEL, _VOICE
    if _MODEL is None or _VOICE != voice:
        _MODEL = KokoroVietnamese(voice=voice, device="cpu")
        _VOICE = voice
    model = _MODEL
    normalized = re.sub(r"\s+", " ", request["text"].strip())
    segments = split_text_segments(normalized)
    sentence_pause, clause_pause = _PAUSES.get(
        request.get("expression", "natural"), _PAUSES["natural"]
    )
    audio_parts = []
    for index, segment in enumerate(segments):
        with contextlib.redirect_stdout(sys.stderr):
            audio, _ = model.synthesize(segment, speed=float(request["speed"]))
        audio_parts.append(np.asarray(audio, dtype=np.float32))
        if index < len(segments) - 1:
            ending = segment.rstrip()[-1:]
            pause_ms = (
                sentence_pause if ending in ".!?…"
                else clause_pause if ending in ",;:"
                else 0
            )
            if pause_ms:
                audio_parts.append(
                    np.zeros(int(SAMPLE_RATE * pause_ms / 1000), dtype=np.float32)
                )
    if not audio_parts:
        raise RuntimeError("Không tạo được âm thanh từ văn bản.")
    destination = request["output"]
    temporary = destination + ".part"
    sf.write(temporary, np.concatenate(audio_parts), SAMPLE_RATE, format="WAV")
    os.replace(temporary, destination)
    return destination


def main():
    for line in sys.stdin:
        try:
            request = json.loads(line)
            request_id = request.get("id")
            try:
                path = _synthesize(request)
                response = {"id": request_id, "ok": True, "path": path}
            except Exception as error:
                response = {
                    "id": request_id, "ok": False,
                    "error": f"{type(error).__name__}: {error}\\n{traceback.format_exc()}",
                }
            _PROTOCOL_OUT.write(json.dumps(response, ensure_ascii=False) + "\n")
            _PROTOCOL_OUT.flush()
        except Exception:
            traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    main()
