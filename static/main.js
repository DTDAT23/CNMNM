// static/main.js

document.addEventListener("DOMContentLoaded", () => {
    // Lấy các phần tử DOM
    const video = document.getElementById("camera-feed");
    const canvas = document.getElementById("capture-canvas");
    const form = document.getElementById("checkin-form");
    const mssvInput = document.getElementById("mssv");
    const resultDiv = document.getElementById("ket-qua");
    const submitBtn = document.getElementById("submit-btn");

    let stream = null;

    // 1. Hàm khởi động camera
    async function startCamera() {
        try {
            // Xin quyền truy cập camera
            stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 }, // Yêu cầu kích thước
                audio: false
            });
            // Gán stream video vào thẻ <video>
            video.srcObject = stream;
            video.onloadedmetadata = () => {
                // Đặt kích thước canvas bằng kích thước thật của video
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
            };
        } catch (err) {
            console.error("Lỗi bật camera:", err);
            resultDiv.textContent = `Lỗi bật camera: ${err.message}. Bạn cần cho phép trình duyệt sử dụng camera.`;
        }
    }

    // 2. Hàm xử lý khi nhấn nút "Gửi"
    form.addEventListener("submit", async (e) => {
        e.preventDefault(); // Ngăn form gửi theo cách truyền thống

        const mssv = mssvInput.value;
        if (!mssv) {
            alert("Vui lòng nhập MSSV");
            return;
        }

        if (!stream) {
            alert("Không tìm thấy camera");
            return;
        }

        // Đổi chữ trên nút để báo đang xử lý
        submitBtn.disabled = true;
        submitBtn.textContent = "Đang xử lý...";

        // 3. Chụp ảnh từ video
        const context = canvas.getContext("2d");
        // Vẽ khung hình hiện tại của video lên canvas
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // 4. Chuyển ảnh trên canvas thành file (Blob)
        canvas.toBlob(async (blob) => {
            // 5. Tạo FormData để gửi đi
            const formData = new FormData();
            formData.append("mssv", mssv);
            // Gửi blob đi với tên file là "capture.jpg"
            // Đây là mấu chốt: server sẽ nhận y hệt như 1 file upload!
            formData.append("image", blob, "capture.jpg");

            // 6. Gửi API
            try {
                const response = await fetch("/api/checkin", {
                    method: "POST",
                    body: formData
                });

                const result = await response.json();
                
                // Hiển thị kết quả
                resultDiv.textContent = JSON.stringify(result, null, 2);

            } catch (err) {
                console.error("Lỗi khi gọi API:", err);
                resultDiv.textContent = `Lỗi kết nối: ${err.message}`;
            } finally {
                // Kích hoạt lại nút
                submitBtn.disabled = false;
                submitBtn.textContent = "Chụp và Gửi điểm danh";
            }

        }, "image/jpeg", 0.9); // Chất lượng ảnh JPEG 90%
    });

    // 7. Bật camera ngay khi tải trang
    startCamera();
});