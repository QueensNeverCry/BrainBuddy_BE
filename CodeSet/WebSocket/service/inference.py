import torch
import asyncio
import time, os, pickle

from WebSocket.core.config import MODEL_PATH

class ModelService:
    brain_buddy = None
    device = None

    @classmethod
    def load_model(cls):
        if cls.brain_buddy is None:
            cls.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            cls.brain_buddy = torch.load(MODEL_PATH, map_location=cls.device)
            cls.brain_buddy.eval()


    # 모델 추론 이거 맞냐 ? 확실해지면 주석 지우셈 ㅇㅇ
    async def inference_focus(file_name: str) -> int:
        def sync_inference():
            with open(file_name, "rb") as f:
                input_tensor = pickle.load(f)
            input_tensor = input_tensor.to(ModelService.device)
            with torch.no_grad():
                output = ModelService.brain_buddy(input_tensor)
            return output.argmax().item()
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, sync_inference)
        return result
    
    # @staticmethod
    # async def inference_focus(file_name: str) -> int:
    #     input_tensor = ...  # 이미지 전처리 코드
    #     input_tensor = input_tensor.to(ModelService.device)
    #     with torch.no_grad():
    #         output = ModelService.brain_buddy(input_tensor)
    #     return output.argmax().item()