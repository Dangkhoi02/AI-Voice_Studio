
import os
from pathlib import Path
from dotenv import load_dotenv

# Xac dinh vi tri file .env
env_path = Path(__file__).with_name(".env")

# Kiem tra file .env co ton tai khong
if env_path.exists():
    print("Da tim thay file .env")

    # Doc cau hinh
    load_dotenv(dotenv_path=env_path)

    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        print("Da tim thay API Key.")
    else:
        print("Chua co API Key. Day la dieu binh thuong.")

else:
    print("Khong tim thay file .env")
