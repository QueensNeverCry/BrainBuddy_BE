from typing import List
import pickle
from PIL import Image
import io
import os

def save_bytes_list_as_jpegs(bytes_list: List[bytes], origin: str) -> str:
    # 출력 폴더 생성
    file_dir, _ = os.path.splitext(origin)
    os.makedirs(file_dir, exist_ok=True)  # 폴더 자동 생성

    for idx, img_bytes in enumerate(bytes_list):
        try:
            img = Image.open(io.BytesIO(img_bytes))  # bytes → Image 객체
            file_path = os.path.join(file_dir, f"frame_{idx:04d}.jpg")
            img.save(file_path, "JPEG")
        except Exception as e:
            print(f"[ERROR] frame_{idx:04d}: {e}")
    print(f"Saved {len(bytes_list)} images to {file_dir}")
    return file_dir

if __name__ == "__main__":
    origin = os.path.join("/Users/v/SUN_RAT/I_AM_SEXY_QUEEN/BrainBuddy_BE/Test/IMG/카리나", "frames_1754568361.pkl")
    with open(origin, "rb") as f:
        input_tensor = pickle.load(f)
    save_bytes_list_as_jpegs(input_tensor, origin=origin)