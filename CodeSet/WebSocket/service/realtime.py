from fastapi import WebSocket
import asyncio
import time, os, pickle

from WebSocket.core.config import TIME_OUT, N_FRAMES, FRAME_DIR

class RealTimeService:        
    @staticmethod
    async def collect_frames(websocket: WebSocket, user_name: str) -> str:
        frames = []
        start = time.time()
        while len(frames) < N_FRAMES and (time.time() - start) < TIME_OUT:
            try:
                frame = await asyncio.wait_for(websocket.receive_bytes(), 1.5)
                frames.append(frame)
            except asyncio.TimeoutError:
                continue
        if len(frames) < N_FRAMES:
            raise asyncio.TimeoutError()
        file_path = os.path.join(FRAME_DIR, user_name)
        os.makedirs(file_path, exist_ok=True)
        file_name = os.path.join(file_path, f"frames_{str(int(start))}.pkl")
        with open(file_name, "wb") as f:
            pickle.dump(frames, f)
        return file_name
