from typing import List
from PIL import Image
import io
import os

def save_bytes_list_as_jpegs(bytes_list: List[bytes], origin: str) -> str:
    # 출력 폴더 생성
    file_dir, _ = os.path.splitext(origin)
    os.makedirs(file_dir, exist_ok=True)
    for idx, img_bytes in enumerate(bytes_list):
        try:
            img = Image.open(io.BytesIO(img_bytes))  # bytes → Image 객체
            file_path = os.path.join(file_dir, f"frame_{idx:04d}.jpg")
            img.save(file_path, "JPEG")
        except Exception as e:
            print(f"[ERROR] :    frame_{idx:04d}: {e}")
    print(f"[DEBUG] :        Saved {len(bytes_list)} images to {file_dir}")
    return file_dir