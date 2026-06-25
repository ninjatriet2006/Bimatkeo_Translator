# Báo cáo Bổ sung: Các Hardcode Còn Sót Lại (Lần 2)

Theo yêu cầu quét toàn bộ file `.py` từng dòng để tìm kiếm các dạng hardcode phụ trợ (URL, thông tin cá nhân, điều kiện if/else/case tĩnh), dưới đây là danh sách các hardcode còn sót lại trong hệ thống:

### 1. Hardcode URL và Đường dẫn Mạng (Mảng Tài nguyên)
- **`desktop_ui/constants.py` và `desktop_ui/mainwindow/handlers.py`**:
  - Tồn tại các URL cứng như: `https://cdn.jsdelivr.net/npm/google-font-metadata/...` và `https://fonts.googleapis.com/...` để tải meta-data của Google Fonts.
- **`app/plugins/recognizer/paddle_onnx_rec_impl.py`**:
  - Nhúng trực tiếp một liên kết Github Raw để tải từ điển tiếng Anh: `url = "https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/en_dict.txt"`.

*👉 Đề xuất:* Di dời toàn bộ các URL tài nguyên tĩnh này vào một tệp cấu hình (ví dụ: `resources.yaml` hoặc một phần trong `global_settings`), giúp người dùng có thể đổi mirror download nếu mạng bị chặn.

### 2. Hardcode Tên Model (Dạng Placeholder)
- Các file Plugin xử lý Ảnh/OCR như:
  - `app/plugins/recognizer/pixel_32px_impl.py` (`self.model = "32px_Loaded_Model"`)
  - `app/plugins/detector/craft_impl.py` (`self.model = "CRAFT_Loaded_Model"`)
  - `app/plugins/detector/ctd_impl.py` (`self.model = "CTD_Loaded_Model_Placeholder"`)
  - `app/plugins/detector/dbconvnext_impl.py` (`self.model = "DBConvNeXt_Loaded_Model"`)

*👉 Đề xuất:* Các biến `self.model` này đang bị gán tĩnh để đánh lừa luồng code thay vì nhận tham số thực tế từ bộ cấu hình Registry. Cần đồng bộ hóa để plugin nhận tên model từ bên ngoài.

### 3. Hardcode Logic Phân Nhánh IF / ELIF / CASE
- **`app/core/api_utils.py` (Dòng 90)**:
  - `elif ai_provider == 'felo': return ['felo-search']`
  - *Vấn đề:* Backend đang chặn một trường hợp rẽ nhánh tĩnh cho mạng lưới Felo. Nên đưa chuỗi `"felo-search"` vào trường `static_models: ["felo-search"]` bên trong block của provider Felo trong `model_registry.yaml` để tự động hóa.
- **`desktop_ui/mainwindow/handlers.py` (Hàng chục vị trí)**:
  - Khắp nơi trong UI code đang phân luồng dữ liệu bằng chuỗi cứng: `elif key == "offline_translator":` hay `elif key == "ai_translator":`.
  - *Vấn đề:* Nếu tương lai cần bổ sung nhóm API mới (như Voice-to-Text hay TTS), chúng ta sẽ phải đục khoét và thêm if/else trên khắp các file giao diện.
  - *Đề xuất V2:* Chuyển đổi kiến trúc này thành Action Map hoặc Dictionary-based Hook.

---
**Tóm lại:** Quá trình quét đã tìm thấy các hardcode phụ nằm ngoài nhóm cốt lõi (Registry V2). Chúng tôi có thể tiếp tục thực thi dọn dẹp các mục này theo cùng phương pháp "hướng file cấu hình" như đã làm với Registry nếu bạn đồng ý.
