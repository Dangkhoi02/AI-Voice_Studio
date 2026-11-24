"""Generate a consistent audition set for the English Kokoro voices.

Run from the project root with:
    .venv_en\\Scripts\\python.exe scripts/audit_english_voice_catalog.py

WAV files and report.csv are written to output/voice_audition_english/.
"""
from pathlib import Path
import csv
import traceback

import numpy as np
import soundfile as sf
from kokoro import KPipeline

from services.voice_manager import LANGUAGES


PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "output" / "voice_audition_english"
TEST_TEXT = (
    "Hello, and welcome to AI Voice Studio. "
    "Today, we are exploring how different voices can bring the same words to life. "
    "Take your time, listen carefully, and enjoy the experience."
)
SPEED = 1.0
SAMPLE_RATE = 24000


def main():
    voices = LANGUAGES["en"]["voices"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "report.csv"
    results = []
    pipelines = {}

    print(f"Generating audition samples for {len(voices)} English voices.")
    print(f"Output folder: {OUTPUT_DIR}")

    for index, voice in enumerate(voices, start=1):
        voice_id = voice["id"]
        label = voice["label"]
        language_code = voice_id[:1]
        output_path = OUTPUT_DIR / f"{voice_id}.wav"

        print(f"[{index}/{len(voices)}] {label} ({voice_id})")
        try:
            if language_code not in ("a", "b"):
                raise ValueError(f"Unsupported English voice ID: {voice_id}")
            pipeline = pipelines.get(language_code)
            if pipeline is None:
                pipeline = KPipeline(lang_code=language_code)
                pipelines[language_code] = pipeline

            audio_chunks = [
                audio
                for _, _, audio in pipeline(TEST_TEXT, voice=voice_id, speed=SPEED)
            ]
            if not audio_chunks:
                raise RuntimeError("Kokoro returned no audio chunks.")

            audio = np.concatenate(audio_chunks).astype(np.float32, copy=False)
            sf.write(str(output_path), audio, SAMPLE_RATE)
            results.append({
                "voice_id": voice_id,
                "label": label,
                "accent_family": "American" if language_code == "a" else "British",
                "status": "success",
                "sample_file": output_path.name,
                "error": "",
            })
            print(f"    Created: {output_path.name}")
        except Exception as error:
            results.append({
                "voice_id": voice_id,
                "label": label,
                "accent_family": "American" if language_code == "a" else "British",
                "status": "failed",
                "sample_file": "",
                "error": str(error),
            })
            print(f"    Failed: {error}")
            traceback.print_exc()

    with report_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "voice_id", "label", "accent_family",
                "status", "sample_file", "error",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    succeeded = sum(item["status"] == "success" for item in results)
    print()
    print(f"Completed: {succeeded}/{len(voices)} voices generated successfully.")
    print(f"Listen to samples in: {OUTPUT_DIR}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
