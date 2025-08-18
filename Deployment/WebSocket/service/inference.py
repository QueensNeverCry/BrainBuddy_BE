# service/model_service.py
from __future__ import annotations
from pathlib import Path
from threading import Lock
from typing import Optional, Literal, Dict, Any

import torch
import asyncio

from WebSocket.model.inference import (NUM_FRAMES_DEFAULT,
                                       build_models,            # (device) -> (cnn, head). eval() 설정 포함
                                       load_checkpoint,         # (cnn, head, ckpt_path, device) -> meta(dict)
                                       load_frames_from_folder, # (folder, num_frames) -> (T,3,224,224) tensor
                                       find_latest_best_model)  # (model_dir) -> latest best path


# ---------------------------------------------------------------------------------
# 전역 싱글톤(Global Singleton) ModelService
# ---------------------------------------------------------------------------------
class ModelService:
    _lock = Lock()
    _initialized: bool = False

    # 전역 상태(global state)
    device: torch.device | None = None
    cnn = None
    head = None
    threshold: float = 0.5
    meta: Dict[str, Any] = {}

    @classmethod
    def _select_device(cls, device_str: Optional[str]) -> torch.device:
        if device_str:
            return torch.device(device_str)
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")  # Apple Silicon
        return torch.device("cpu")

    @classmethod
    def _resolve_ckpt(cls, ckpt_path_or_dir: Optional[str]) -> Path:
        """파일 또는 디렉토리 입력 지원. 없으면 기본 model 디렉토리에서 최신(best)을 탐색."""
        if ckpt_path_or_dir:
            p = Path(ckpt_path_or_dir).expanduser().resolve()
        else:
            # WebSocket/ 폴더 기준으로 ../model/ 최신 best 선택
            root = Path(__file__).resolve().parents[1]   # .../WebSocket/
            p = (root / "model").resolve()

        if p.is_dir():
            ckpt = Path(find_latest_best_model(str(p))).resolve()
        else:
            ckpt = p

        if not ckpt.exists():
            raise FileNotFoundError(f"[ModelService] checkpoint not found: {ckpt}")
        return ckpt

    # -----------------------------------------------------------------------------
    # 초기화(Initialization): 앱 시작 시 1회 호출 (lifespan에서 호출)
    # -----------------------------------------------------------------------------
    @classmethod
    def init_model(cls,
                   ckpt_path_or_dir: Optional[str] = None,
                   device_str: Optional[str] = None,
                   threshold_type: Literal["acc", "rec", "custom"] = "acc",
                   custom_threshold: Optional[float] = None) -> None:
        if cls._initialized:
            return
        with cls._lock:
            if cls._initialized:
                return

            # 1) 디바이스 선택(device)
            cls.device = cls._select_device(device_str)

            # 2) 체크포인트 경로(resolve)
            ckpt_path = cls._resolve_ckpt(ckpt_path_or_dir)

            # 3) 모델 빌드(build) + 가중치 로드(load)
            cls.cnn, cls.head = build_models(cls.device)                     # 팀원 함수
            cls.meta = load_checkpoint(cls.cnn, cls.head, str(ckpt_path),    # 팀원 함수
                                       cls.device)

            # 4) 임계값(threshold) 결정
            if threshold_type == "custom" and (custom_threshold is not None):
                cls.threshold = float(custom_threshold)
            elif threshold_type == "rec" and (cls.meta.get("thr_rec") is not None):
                cls.threshold = float(cls.meta["thr_rec"])
            elif threshold_type == "acc" and (cls.meta.get("thr_acc") is not None):
                cls.threshold = float(cls.meta["thr_acc"])
            # else: 기본 0.5 유지

            # 5) 워밍업(warm-up)으로 첫 추론 지연(latency) 감소
            with torch.inference_mode():
                dummy = torch.zeros((1, NUM_FRAMES_DEFAULT, 3, 224, 224),
                                    dtype=torch.float32, device=cls.device)
                _ = cls.head(cls.cnn(dummy))

            cls._initialized = True
            print(f"[Startup] Model loaded on {cls.device} | ckpt={ckpt_path} | thr={cls.threshold}")

    # -----------------------------------------------------------------------------
    # 추론(Inference): 프레임 폴더 경로를 받아 예측값 반환
    # -----------------------------------------------------------------------------
    @classmethod
    async def inference_focus(cls, img_dir: str) -> int:
        """
        비동기(async) 엔드포인트(WebSocket)에서 안전하게 호출.
        내부는 CPU/GPU 바운드이므로 to_thread로 이벤트 루프 블로킹 방지.
        반환: pred(int) 0/1
        """
        if not cls._initialized:
            # lifespan에서 보통 init_model을 호출하지만, 혹시 누락 시 방어적으로 로드
            cls.init_model()

        def _run_sync() -> int:
            vid = load_frames_from_folder(img_dir, num_frames=NUM_FRAMES_DEFAULT)  # (T,3,224,224)
            x = vid.unsqueeze(0).to(cls.device)                                    # (1,T,3,224,224)
            with torch.inference_mode():
                logit = cls.head(cls.cnn(x))
                prob = torch.sigmoid(logit).item()
                print(f"[DEBUG] :       probability : {prob} and focus : {prob >= cls.threshold}")
            return int(prob >= float(cls.threshold))

        return await asyncio.to_thread(_run_sync)

    # -----------------------------------------------------------------------------
    # 메모리 풋프린트 출력(footprint)
    # -----------------------------------------------------------------------------
    @classmethod
    def print_footprint(cls) -> None:
        if not cls._initialized:
            print("[Memory] Model not initialized")
            return
        # 1) 모델 파라미터/버퍼 용량
        param_bytes = sum(p.numel() * p.element_size() for p in cls.cnn.parameters()) \
                    + sum(p.numel() * p.element_size() for p in cls.head.parameters())
        buffer_bytes = sum(b.numel() * b.element_size() for b in cls.cnn.buffers()) \
                     + sum(b.numel() * b.element_size() for b in cls.head.buffers())
        model_bytes = param_bytes + buffer_bytes

        def fmt(n: int) -> str:
            u = ["B","KB","MB","GB","TB"]
            i = 0; f = float(n)
            while f >= 1024 and i < len(u)-1:
                f /= 1024; i += 1
            return f"{f:.2f} {u[i]}"

        print(f"[Memory] model(params+buffers) = {fmt(model_bytes)} "
              f"(params={fmt(param_bytes)}, buffers={fmt(buffer_bytes)})")

        # 2) 프로세스 RSS
        try:
            import psutil, os
            rss = psutil.Process(os.getpid()).memory_info().rss
            print(f"[Memory] process RSS = {fmt(rss)}")
        except Exception:
            pass

        # 3) 장치 메모리(device memory)
        if cls.device and cls.device.type == "cuda":
            try:
                alloc = torch.cuda.memory_allocated(cls.device)
                resv  = torch.cuda.memory_reserved(cls.device)
                mx    = torch.cuda.max_memory_allocated(cls.device)
                print(f"[Memory] device allocated={fmt(alloc)} reserved={fmt(resv)} max_alloc={fmt(mx)}")
            except Exception:
                pass
        elif cls.device and cls.device.type == "mps":
            try:
                import torch.mps as mps
                print(f"[Memory] device allocated={fmt(mps.current_allocated_memory())} "
                      f"driver={fmt(mps.driver_allocated_memory())}")
            except Exception:
                pass