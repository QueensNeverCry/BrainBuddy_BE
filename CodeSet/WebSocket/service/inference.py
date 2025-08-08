import torch
import asyncio
import pickle

from WebSocket.core.config import MODEL_PATH
from WebSocket.model import save_bytes_list_as_jpegs

# 테스트용 random
from random import randint

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
#
# input_tensor 를 모델 입력 형식에 맞게 변환 해야함
# List[bytes] → 전처리 → tensor 변환 → stack/unsqueeze → device로 이동
#              여기서 모델의 입력 shape(차원, 형태) 알아야함...
#
            input_tensor = input_tensor.to(ModelService.device)
            with torch.no_grad():
                output = ModelService.brain_buddy(input_tensor)
            return output.argmax().item()
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, sync_inference)
        return result

    # model 연동 전 테스트 추론 함수
    async def test_inference(file_name: str) -> int:
        with open(file_name, "rb") as f:
            input_tensor = pickle.load(f)
        print(f"[LOG] :     ModelService.test_inference() : {len(input_tensor)} frames...")
        print(f"[LOG] :     ModelService.test_inference() : input data writed as {type(input_tensor)}")
        print(f"[LOG] :     ModelService.test_inference() : each frame type is {type(input_tensor[0])}")
        jpg_dir = save_bytes_list_as_jpegs(input_tensor, file_name)
        return randint(0, 1)