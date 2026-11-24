
from pathlib import Path
import soundfile as sf

from kokoro_vietnamese import KokoroVietnamese, SAMPLE_RATE


def main():
    print("Đang khởi tạo Kokoro Vietnamese...")

    # Máy hiện tại sử dụng CPU
    tts = KokoroVietnamese(
        voice="diem_trinh",
        device="cpu"
    )

    print("Đang tạo giọng nói...")

    audio, phonemes = tts.synthesize(
        "Xin chào! Đây là bài kiểm tra giọng nói tiếng Việt của AI Voice Studio.",
        speed=1.0
    )

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "test_vi.wav"

    sf.write(str(output_file), audio, SAMPLE_RATE)

    print("Đã tạo âm thanh thành công!")
    print(f"File: {output_file.resolve()}")
    print(f"Sample rate: {SAMPLE_RATE}")
    print("Phiên âm:", phonemes)


if __name__ == "__main__":
    main()
