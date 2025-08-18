import os, glob
from typing import List, Literal, Optional, Dict, Any
import torch
import torch.nn as nn
from torchvision import transforms, models
from torchvision.transforms import InterpolationMode
from PIL import Image

# ===== Model =====
class CNNEncoder(nn.Module):
    def __init__(self, output_dim: int = 512, dropout2d: float = 0.1, proj_dropout: float = 0.4):
        super().__init__()
        # 주의: 사전학습 백본 다운로드를 피하려면 weights=None 권장
        backbone = models.mobilenet_v3_large(weights=None)
        self.features = backbone.features
        self.feat_channels = backbone.classifier[0].in_features  # 960

        self.avgpool = nn.AdaptiveAvgPool2d((2, 2))
        self.drop2d  = nn.Dropout2d(dropout2d)

        flat_dim = self.feat_channels * 2 * 2  # 960*4 = 3840
        self.fc = nn.Sequential(
            nn.Linear(flat_dim, 256), nn.GELU(), nn.Dropout(proj_dropout),
            nn.Linear(256, output_dim), nn.GELU()
        )

    def forward(self, x):  # x: (B, T, 3, H, W)
        B, T, C, H, W = x.shape
        x = x.view(B*T, C, H, W)
        x = self.features(x)             # (B*T, 960, h, w)
        x = self.avgpool(x)              # (B*T, 960, 2, 2)
        x = self.drop2d(x)
        x = x.view(B*T, -1)              # (B*T, 3840)
        x = self.fc(x)                   # (B*T, 512)
        return x.view(B, T, -1)          # (B, T, 512)

class EngagementModelNoFusion(nn.Module):
    def __init__(self, cnn_feat_dim: int = 512, hidden_dim: int = 128):
        super().__init__()
        self.lstm = nn.LSTM(input_size=cnn_feat_dim, hidden_size=hidden_dim, batch_first=True)
        self.fc = nn.Sequential(nn.Linear(hidden_dim, 64),
                                nn.ReLU(),
                                nn.Dropout(0.3),
                                nn.Linear(64, 1)) # logit

    def forward(self, cnn_feats):
        _, (hn, _) = self.lstm(cnn_feats)  # hn: (1, B, H)
        x = hn.squeeze(0)                  # (B, H)
        return self.fc(x)                  # (B, 1)

# 학습과 동일하게 전처리
NUM_FRAMES_DEFAULT = 30

preprocess = transforms.Compose(transforms=[
    transforms.Resize((224, 224), interpolation=InterpolationMode.BILINEAR, antialias=True),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

# 폴더에서 프레임을 읽어 (T,3,224,224) 텐서 반환. 프레임 수가 부족하면 마지막 프레임을 반복해 채움
def load_frames_from_folder(folder_path: str,
                            num_frames: int = NUM_FRAMES_DEFAULT) -> torch.Tensor:
    files = [f for f in sorted(os.listdir(folder_path)) if f.lower().endswith(IMAGE_EXTS)]
    if len(files) == 0:
        raise FileNotFoundError(f"No image frames found in: {folder_path}")

    # 학습은 정렬 후 앞에서부터 30장을 사용했음 -> 동일하게 맞춤
    # 부족할 경우 마지막 프레임을 반복해 T=30을 보장
    selected = files[:num_frames]
    if len(selected) < num_frames:
        selected = selected + [selected[-1]] * (num_frames - len(selected))

    frames: List[torch.Tensor] = []
    for name in selected:
        img = Image.open(os.path.join(folder_path, name)).convert("RGB")
        frames.append(preprocess(img))  # (3,224,224)
    video = torch.stack(frames, dim=0)  # (T,3,224,224)
    return video

# ===== Checkpoint loading =====
def build_models(device: torch.device):
    cnn = CNNEncoder().to(device)
    head = EngagementModelNoFusion().to(device)
    cnn.eval(); head.eval()
    return cnn, head

# 훈련에서 저장한 dict(가중치+메타)를 로드
def load_checkpoint(cnn: nn.Module,
                    head: nn.Module,
                    ckpt_path: str,
                    device: torch.device) -> Dict[str, Any]:
    ckpt = torch.load(ckpt_path, map_location=device)
    cnn.load_state_dict(ckpt["cnn_state_dict"])
    head.load_state_dict(ckpt["model_state_dict"])
    # 임계값/기타 메타 포함 가능(thr_acc, thr_rec 등)
    meta = {"epoch": ckpt.get("epoch"),
            "val_loss": ckpt.get("val_loss"),
            "thr_acc": ckpt.get("thr_acc"),
            "thr_rec": ckpt.get("thr_rec")}
    return meta

# best_model_epoch_*.pt 중 가장 최근 파일을 반환. 지정 파일이 없을 때 폴백.
def find_latest_best_model(model_dir: str) -> str:
    candidates = glob.glob(os.path.join(model_dir, "best_model_epoch_*.pt"))
    if not candidates:
        raise FileNotFoundError(f"No best_model_epoch_*.pt found in {model_dir}")
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]

# ===== Inference API (코어 함수) =====
@torch.inference_mode()
def predict_from_folder(folder_path: str,
                        ckpt_path: Optional[str] = "best_model.pt",
                        threshold_type: Literal["acc", "rec", "custom"] = "acc",
                        custom_threshold: Optional[float] = None,
                        device_str: Optional[str] = None) -> tuple[float, int]:
    device = torch.device(device_str or ("cuda" if torch.cuda.is_available() else "cpu"))
    if os.path.isdir(ckpt_path):
        ckpt_path = find_latest_best_model(ckpt_path)

    cnn, head = build_models(device)
    meta = load_checkpoint(cnn, head, ckpt_path, device)

    video = load_frames_from_folder(folder_path, num_frames=NUM_FRAMES_DEFAULT)
    video = video.unsqueeze(0).to(device)

    feats = cnn(video)
    logit = head(feats)
    prob = torch.sigmoid(logit).item()

    # best threshold 가져오는 거긴 한데 불안정해서 0.5로 해도 될것 같습니다
    # if threshold_type == "custom" and custom_threshold is not None:
    #     thr = float(custom_threshold)
    # elif threshold_type == "rec" and meta.get("thr_rec") is not None:
    #     thr = float(meta["thr_rec"])
    # elif threshold_type == "acc" and meta.get("thr_acc") is not None:
    #     thr = float(meta["thr_acc"])
    # else:
    #     thr = 0.5

    thr=0.5
    pred = int(prob >= thr)
    return prob, pred
    # return pred #예측값 반환

# if __name__ == "__main__":
#     # 간단한 수동 테스트 ( 30프레임이 담긴 폴더, best_model.pt 경로)
#     print(predict_from_folder("/Users/v/SUN_RAT/QUEEN/BrainBuddy_BE/Test/IMG/로컬웹서버테스트/images_1755243282", "best_model_epoch_4.pt"))
#     pass