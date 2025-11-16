# diem_danh.py (Code hoàn chỉnh - Sửa thông báo)
import os
import cv2
import pickle
from deepface import DeepFace
from ultralytics import YOLO
import warnings
import numpy as np

warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

YOLO_MODEL_PATH = os.path.join(BASE_DIR, "models", "best.pt")
EMBEDDINGS_SAVE_PATH = os.path.join(BASE_DIR, "database_embeddings.pkl")
CNN_MODEL_NAME = "ArcFace"
DIST_THRESHOLD = 0.5


def _safe_crop(img, box):
    h, w = img.shape[:2]
    x1, y1, x2, y2 = box
    x1 = max(0, min(w - 1, int(x1)))
    x2 = max(0, min(w - 1, int(x2)))
    y1 = max(0, min(h - 1, int(y1)))
    y2 = max(0, min(h - 1, int(y2)))
    if x2 <= x1 or y2 <= y1:
        return None
    return img[y1:y2, x1:x2]


def run_attendance_pipeline(checkin_image_path: str, student_id_to_check: str):
    try:
        if not os.path.exists(checkin_image_path):
            return {"success": False, "message": "Không tìm thấy file ảnh check-in"}

        if not os.path.exists(YOLO_MODEL_PATH):
            return {"success": False, "message": f"Không tìm thấy YOLO model tại {YOLO_MODEL_PATH}"}

        if not os.path.exists(EMBEDDINGS_SAVE_PATH):
            return {"success": False, "message": "Không tìm thấy database_embeddings.pkl. Hãy chạy tạo DB trước."}

        # ----- SỬA LỖI PYTORCH & IMPORT -----
        import torch
        import torch.nn
        from ultralytics.nn.tasks import DetectionModel
        from ultralytics.nn.modules.conv import Conv, Concat
        from ultralytics.nn.modules.block import Bottleneck, C2f as C2fr, SPPF, DFL
        from ultralytics.nn.modules.head import Detect
        from torch.nn.modules.upsampling import Upsample
        Upsampler = Upsample

        torch.serialization.add_safe_globals([
            DetectionModel, Conv, Concat, Bottleneck, C2fr, SPPF, DFL, Detect,
            torch.nn.modules.container.Sequential,
            torch.nn.modules.conv.Conv2d,
            torch.nn.modules.batchnorm.BatchNorm2d,
            torch.nn.modules.activation.SiLU,
            torch.nn.modules.container.ModuleList,
            torch.nn.modules.pooling.MaxPool2d,
            Upsample, Upsampler
        ])
        # ----- KẾT THÚC SỬA LỖI -----

        detector = YOLO(YOLO_MODEL_PATH)

        with open(EMBEDDINGS_SAVE_PATH, "rb") as f:
            db = pickle.load(f)

        if student_id_to_check not in db:
            return {"success": False, "message": f"MSSV {student_id_to_check} không có trong database"}

        db_vector = db[student_id_to_check]

        img = cv2.imread(checkin_image_path)
        if img is None:
            return {"success": False, "message": "Không thể đọc ảnh check-in (cv2.imread trả về None)"}

        results = detector(img)
        if len(results) == 0 or len(results[0].boxes) == 0:
            return {"success": False, "message": "Không tìm thấy khuôn mặt trong ảnh"}

        box = results[0].boxes[0].xyxy.cpu().numpy()[0]
        face = _safe_crop(img, box)
        if face is None or face.size == 0:
            return {"success": False, "message": "Không thể crop mặt (box sai)"}

        try:
            emb_objs = DeepFace.represent(img_path=face, model_name=CNN_MODEL_NAME, enforce_detection=False)
            checkin_vector = emb_objs[0]["embedding"]
        except Exception as e:
            return {"success": False, "message": "Lỗi khi tạo embedding từ ảnh check-in", "error": str(e)}

        # ----- SỬA LỖI DEEPFACE (DÙNG NUMPY) -----
        try:
            a = np.asarray(checkin_vector)
            b = np.asarray(db_vector)
            
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            similarity = dot_product / (norm_a * norm_b)
            distance = 1 - similarity
            
        except Exception as e:
            return {"success": False, "message": "Lỗi khi so sánh 2 embedding (numpy)", "error": str(e)}
        # ----- KẾT THÚC SỬA LỖI DEEPFACE -----
        
        distance = float(distance) 

        # ----- ĐÂY LÀ PHẦN BẠN CẦN SỬA -----
        if distance < DIST_THRESHOLD:
            return {
                "success": True, 
                "message": "Bạn đã điểm danh thành công", # <-- ĐÃ SỬA
                "mssv": student_id_to_check, 
                "distance": distance
            }
        else:
            return {
                "success": False, 
                "message": "Khuôn mặt không trùng khớp, bạn hãy chụp xác nhận lại", # <-- ĐÃ SỬA
                "mssv": student_id_to_check, 
                "distance": distance
            }
        # ----- KẾT THÚC PHẦN SỬA -----

    except Exception as e:
        return {"success": False, "message": "Lỗi nội bộ Python", "error": str(e)}
