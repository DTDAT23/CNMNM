# tao_database.py
import os
import pickle
from deepface import DeepFace
import warnings

warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database_sinh_vien")
EMBEDDINGS_SAVE_PATH = os.path.join(BASE_DIR, "database_embeddings.pkl")
CNN_MODEL_NAME = "ArcFace"


def create_database_embeddings():
    result = {
        "success": False,
        "total_created": 0,
        "failed_files": []
    }

    if not os.path.exists(DB_PATH):
        result["message"] = "Không tìm thấy thư mục database_sinh_vien"
        return result

    images = [f for f in os.listdir(DB_PATH) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not images:
        result["message"] = "Không có ảnh trong thư mục database_sinh_vien"
        return result

    db = {}
    failed = []

    for fn in images:
        path = os.path.join(DB_PATH, fn)
        mssv = os.path.splitext(fn)[0]
        try:
            emb_objs = DeepFace.represent(img_path=path, model_name=CNN_MODEL_NAME)
            db[mssv] = emb_objs[0]["embedding"]
            print(f"[OK] {mssv}")
        except Exception as e:
            failed.append(fn)
            print(f"[ERR] {fn} -> {str(e)}")

    with open(EMBEDDINGS_SAVE_PATH, "wb") as f:
        pickle.dump(db, f)

    result["success"] = True
    result["total_created"] = len(db)
    result["failed_files"] = failed
    result["message"] = "Hoàn tất tạo database_embeddings.pkl"
    return result


if __name__ == "__main__":
    out = create_database_embeddings()
    import json
    print(json.dumps(out, ensure_ascii=False, indent=2))
