# app.py
import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from diem_danh import run_attendance_pipeline
from tao_database import create_database_embeddings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/api/checkin", methods=["POST"])
def api_checkin():
    try:
        mssv = request.form.get("mssv")
        file = request.files.get("image")

        if not mssv or not file:
            return jsonify({"success": False, "message": "Thiếu MSSV hoặc file ảnh"}), 400

        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_DIR, filename)
        file.save(save_path)

        result = run_attendance_pipeline(save_path, mssv)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": "Lỗi server", "error": str(e)}), 500


@app.route("/api/create-database", methods=["POST"])
def api_create_db():
    try:
        result = create_database_embeddings()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": "Lỗi tạo database", "error": str(e)}), 500


# serve uploaded images (debug)
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


if __name__ == "__main__":
    # debug True cho dev; set False khi deploy
    app.run(host="0.0.0.0", port=5000, debug=True)