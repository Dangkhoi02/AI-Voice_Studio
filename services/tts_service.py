
import asyncio
import base64
import wave
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAIError
import os


# Đọc API Key từ file .env ở thư mục gốc
PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

MODEL = "gpt-realtime-2.1-mini"
SAMPLE_RATE = 24000


async def generate_audio(
    text: str,
    voice: str = "marin",
    output_path: str = "output/audio.wav"
):
    """
    Chuyển văn bản thành giọng nói và lưu thành file WAV.
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "Chưa tìm thấy OPENAI_API_KEY trong file .env"
        )

    if not text.strip():
        raise ValueError("Vui lòng nhập nội dung văn bản.")

    client = AsyncOpenAI(api_key=api_key)
    audio_chunks = []

    try:
        async with client.realtime.connect(model=MODEL) as connection:

            # Cấu hình đầu ra âm thanh
            await connection.session.update(
                session={
                    "type": "realtime",
                    "output_modalities": ["audio"],
                    "audio": {
                        "output": {
                            "format": {
                                "type": "audio/pcm",
                                "rate": 24000
                            },
                            "voice": voice
                        }
                    }
                }
            )

            # Gửi văn bản cần đọc
            await connection.conversation.item.create(
                item={
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": text
                        }
                    ]
                }
            )

            # Yêu cầu AI tạo giọng nói
            await connection.response.create()

            # Nhận dữ liệu âm thanh
            async for event in connection:

                if event.type == "response.output_audio.delta":
                    audio_chunks.append(
                        base64.b64decode(event.delta)
                    )

                elif event.type == "error":
                    raise OpenAIError(event.error.message)

                elif event.type == "response.done":
                    if event.response.status != "completed":
                        raise OpenAIError(
                            "Quá trình tạo âm thanh không hoàn thành."
                        )
                    break

        if not audio_chunks:
            raise RuntimeError("Không nhận được dữ liệu âm thanh.")

        # Ghép các đoạn âm thanh
        audio_data = b"".join(audio_chunks)

        # Tạo thư mục output nếu chưa có
        save_path = PROJECT_DIR / output_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Lưu thành file WAV
        with wave.open(str(save_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(audio_data)

        return save_path

    finally:
        await client.close()
