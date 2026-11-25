"""Persistent worker process for the isolated Kokoro English environment."""
import contextlib
import json
import os
import re
import sys
import traceback

import numpy as np
import soundfile as sf

_PROTOCOL_OUT = sys.stdout
with contextlib.redirect_stdout(sys.stderr):
    from kokoro import KPipeline
_PIPELINES = {}


def _synthesize(request):
    language_code = request["language_code"]
    if language_code not in _PIPELINES:
        with contextlib.redirect_stdout(sys.stderr):
            _PIPELINES[language_code] = KPipeline(lang_code=language_code)
    pipeline = _PIPELINES[language_code]
    text = re.sub(r"\s+", " ", request["text"].strip())
    segments = [
        part.strip()
        for part in re.split(r"(?<=[,;:])\s+|(?<=[.!?…])\s+", text)
        if part.strip()
    ]
    pauses = {
        "natural": (220, 100), "enthusiastic": (150, 70),
        "gentle": (320, 150), "serious": (280, 120),
    }
    sentence_pause, clause_pause = pauses.get(
        request.get("expression", "natural"), pauses["natural"]
    )
    parts = []
    for index, segment in enumerate(segments):
        with contextlib.redirect_stdout(sys.stderr):
            chunks = [
                audio for _, _, audio in pipeline(
                    segment, voice=request["voice"], speed=float(request["speed"])
                )
            ]
        if chunks:
            parts.append(np.concatenate(chunks))
        if index < len(segments) - 1:
            ending = segment.rstrip()[-1:]
            pause_ms = (
                sentence_pause if ending in ".!?…"
                else clause_pause if ending in ",;:"
                else 0
            )
            if pause_ms:
                parts.append(np.zeros(int(24000 * pause_ms / 1000), dtype=np.float32))
    if not parts:
        raise RuntimeError("Kokoro không tạo được âm thanh.")
    destination = request["output"]
    temporary = destination + ".part"
    sf.write(temporary, np.concatenate(parts), 24000, format="WAV")
    os.replace(temporary, destination)
    return destination


def main():
    for line in sys.stdin:
        try:
            request = json.loads(line)
            request_id = request.get("id")
            try:
                result = _synthesize(request)
                response = {"id": request_id, "ok": True, "path": result}
            except Exception as error:
                response = {
                    "id": request_id, "ok": False,
                    "error": f"{type(error).__name__}: {error}",
                }
            _PROTOCOL_OUT.write(json.dumps(response, ensure_ascii=False) + "\n")
            _PROTOCOL_OUT.flush()
        except Exception:
            traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    main()
