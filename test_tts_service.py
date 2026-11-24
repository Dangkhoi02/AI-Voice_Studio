
import os

from services.tts_service import MODEL, SAMPLE_RATE, PROJECT_DIR

print("=== AI VOICE STUDIO - CONFIG TEST ===")

print("Model:", MODEL)
print("Sample rate:", SAMPLE_RATE)
print("Project directory:", PROJECT_DIR)

api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print("API Key: Da duoc cau hinh (khong hien thi gia tri)")
else:
    print("API Key: Chua cau hinh (binh thuong)")

print("TTS configuration: OK")
