from pathlib import Path

from WebSocket.core.config import MODEL_PATH
from WebSocket.model import load_model, load_folder_frames, predict_sequence

import os, psutil, torch

# 테스트용 random
# from random import randint

def _format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


class ModelService:
    brain_buddy = None
    device = None

    @classmethod
    def init_model(cls):
        if cls.brain_buddy is None:
            root = Path(__file__).resolve().parents[1]     # .../WebSocket/
            ckpt = root / "model" / "the_best.pth"
            model, device = load_model(str(ckpt))
            cls.brain_buddy = model
            cls.device = device

    @classmethod
    def footprint(cls) -> dict:
        m, dev = cls.brain_buddy, cls.device
        if m is None:
            raise RuntimeError("Model not initialized")

        # 모델 자체 용량(파라미터 + 버퍼)
        param_bytes  = sum(p.numel() * p.element_size() for p in m.parameters())
        buffer_bytes = sum(b.numel() * b.element_size() for b in m.buffers())
        model_bytes  = param_bytes + buffer_bytes

        # device 메모리(CUDA/MPS)
        device_stats = None
        if dev and dev.type == "cuda":
            torch.cuda.synchronize(dev)
            device_stats = {
                "allocated": torch.cuda.memory_allocated(dev),
                "reserved":  torch.cuda.memory_reserved(dev),
                "max_alloc": torch.cuda.max_memory_allocated(dev),
            }
        elif dev and dev.type == "mps":
            try:
                import torch.mps as mps
                device_stats = {
                    "allocated": mps.current_allocated_memory(),  # 현재 할당
                    "driver":    mps.driver_allocated_memory(),   # 드라이버 측
                }
            except Exception:
                device_stats = {"note": "MPS memory stats not available"}

        # 프로세스 RSS(전체 프로세스 메모리)
        rss = psutil.Process(os.getpid()).memory_info().rss

        return {"model_bytes": model_bytes,
                "param_bytes": param_bytes,
                "buffer_bytes": buffer_bytes,
                "process_rss_bytes": rss,
                "device_stats": device_stats}

    @classmethod
    def print_footprint(cls) -> None:
        fp = cls.footprint()
        print(
            "[Memory] model(params+buffers) =",
            _format_bytes(fp["model_bytes"]),
            f"(params={_format_bytes(fp['param_bytes'])}, buffers={_format_bytes(fp['buffer_bytes'])})",
        )
        print("[Memory] process RSS =", _format_bytes(fp["process_rss_bytes"]))
        if fp["device_stats"]:
            ds = fp["device_stats"]
            if "allocated" in ds:
                print("[Memory] device allocated =", _format_bytes(ds["allocated"]))
            if "reserved" in ds:
                print("[Memory] device reserved  =", _format_bytes(ds["reserved"]))
            if "max_alloc" in ds:
                print("[Memory] device max_alloc =", _format_bytes(ds["max_alloc"]))
            if "driver" in ds:
                print("[Memory] device driver    =", _format_bytes(ds["driver"]))
            if "note" in ds:
                print("[Memory]", ds["note"])

    @classmethod
    async def inference_focus(cls, img_dir: str) -> int:
        frames = load_folder_frames(folder=img_dir)
        focus, prob = predict_sequence(cls.brain_buddy, cls.device, frames)
        print(f"[DEBUG] :   focus = {focus} , prob = {prob}")
        return focus