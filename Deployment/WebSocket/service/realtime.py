from fastapi import WebSocket
from PIL import Image
from datetime import datetime
import time, os, pickle, io
import asyncio
import shutil

from WebSocket.core.config import TIME_OUT, N_FRAMES, FRAME_DIR

class RealTimeService:
    @staticmethod
    async def collect_frames(websocket: WebSocket, user_name: str) -> str:
        frames = []
        start = time.time()
        cnt = 0
        while len(frames) < N_FRAMES and (time.time() - start) < TIME_OUT:
            try:
                frame = await asyncio.wait_for(websocket.receive_bytes(), 1.0)
                frames.append(frame)
                cnt += 1
                print(f"[LOG] :     {cnt} - {datetime.now()}")
            except asyncio.TimeoutError:
                continue
        if len(frames) < N_FRAMES:
            raise asyncio.TimeoutError()
        
        user_dir = os.path.join(FRAME_DIR, user_name)
        os.makedirs(name=user_dir, exist_ok=True)
        cur_img_dir = os.path.join(user_dir, f"images_{int(start)}")
        os.makedirs(name=cur_img_dir, exist_ok=True)

        for idx, img_bytes in enumerate(iterable=frames):
            try:
                img = Image.open(io.BytesIO(img_bytes))  # bytes → Image 객체
                file_path = os.path.join(cur_img_dir, f"{idx:04d}.jpg")
                img.save(file_path, "JPEG")
            except Exception as e:
                print(f"[ERROR] :    {file_path}: {e}")
        print(f"[DEBUG] :        Saved {len(frames)} images to {cur_img_dir}")
        return cur_img_dir
    

    @staticmethod
    async def clear(img_dir: str) -> None:
        if img_dir and os.path.exists(img_dir):
            try:
                await asyncio.to_thread(shutil.rmtree, img_dir)
            except Exception as e:
                print(f"[ERROR] Failed to delete {img_dir}: {e}")