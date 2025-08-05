import torch
import time, os, pickle

class ModelService:
    brain_buddy = None

    @classmethod
    def load_model(cls):
        if cls.model is None:
            # PyTorch 모델 불러오기
            cls.model = torch.load("model.pth", map_location="cpu")
            cls.model.eval()

    @staticmethod
    async def inference_focus(file_name: str) -> int:
        return 0