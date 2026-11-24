"""Generate a consistent Vietnamese audition set for every registered Kokoro voice.

Run from the project root with:
    py -3.12 scripts/audit_voice_catalog.py

The script writes one WAV per voice under output/voice_audition/.
"""
from pathlib import Path
import csv
import traceback
import sys

# Add the project root so imports work when this file is run from scripts/.
PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import soundfile as sf

from kokoro_vietnamese import KokoroVietnamese, SAMPLE_RATE
from services.voice_manager import LANGUAGES


PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "output" / "voice_audition"
TEST_TEXT = (
    "Xin chào! Hôm nay là một ngày thật đặc biệt. "
    "Dù hành trình phía trước còn nhiều thử thách, chúng ta vẫn hãy tự tin bước tiếp. "
    "Bạn đã sẵn sàng khám phá những điều mới mẻ chưa?"
)
SPEED = 1.0
DEVICE = "cpu"


def main():
    voices = LANGUAGES["vi"]["voices"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "report.csv"
    results = []

    print(f"Đang tạo bộ nghe thử cho {len(voices)} giọng tiếng Việt.")
    print(f"Thư mục lưu: {OUTPUT_DIR}")
    print(f"Tốc độ: {SPEED} | Thiết bị: {DEVICE}")
    print()

    for index, voice in enumerate(voices, start=1):
        voice_id = voice["id"]
        label = voice["label"]
        output_path = OUTPUT_DIR / f"{voice_id}.wav"

        print(f"[{index}/{len(voices)}] Đang tạo: {label} ({voice_id}) ...")
        try:
            tts = KokoroVietnamese(voice=voice_id, device=DEVICE)
            audio, phonemes = tts.synthesize(TEST_TEXT, speed=SPEED)
            sf.write(str(output_path), audio, SAMPLE_RATE)
            results.append({
                "voice_id": voice_id,
                "label": label,
                "status": "success",
                "file": output_path.name,
                "error": "",
            })
            print(f"    Hoàn tất: {output_path.name}")
            del tts
        except Exception as error:
            results.append({
                "voice_id": voice_id,
                "label": label,
                "status": "failed",
                "file": "",
                "error": str(error),
            })
            print(f"    Lỗi: {error}")
            traceback.print_exc()

    with report_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["voice_id", "label", "status", "file", "error"],
        )
        writer.writeheader()
        writer.writerows(results)

    succeeded = sum(item["status"] == "success" for item in results)
    failed = len(results) - succeeded
    print()
    print(f"Hoàn tất: {succeeded}/{len(results)} giọng tạo thành công.")
    if failed:
        print(f"Có {failed} giọng gặp lỗi. Xem report.csv để biết chi tiết.")
    print(f"Mở thư mục để nghe: {OUTPUT_DIR}")
    print(f"Báo cáo: {report_path}")


if __name__ == "__main__":
    main()
