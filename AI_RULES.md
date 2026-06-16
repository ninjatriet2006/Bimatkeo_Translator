# Bimatkeo Translator - AI Assistant Mandatory Rules

Tất cả các AI Assistant (Agent) khi làm việc trong dự án này **BẮT BUỘC** phải tuân thủ nghiêm ngặt các quy tắc dưới đây trước khi thực hiện bất kỳ thay đổi nào lên mã nguồn:

## 1. QUY TẮC LẬP KẾ HOẠCH TRƯỚC (PLANNING FIRST)
- **Cấm tự ý sửa code:** AI tuyệt đối KHÔNG ĐƯỢC tự ý sửa đổi code, chạy các lệnh làm thay đổi file (`write_to_file`, `replace_file_content`, `run_command` với các lệnh `rm`, `sed`...) khi chưa có kế hoạch (Plan) cụ thể.
- **Quy trình bắt buộc:**
  1. Phân tích nguyên nhân gốc rễ bằng các lệnh đọc/tìm kiếm (`view_file`, `grep_search`).
  2. Tạo bản Kế hoạch (Ví dụ: `implementation_plan.md`) giải thích rõ sẽ sửa ở đâu, như thế nào.
  3. Bật tùy chọn Yêu cầu phản hồi (`request_feedback = true`).
  4. **Dừng lại (Stop/Wait) và chờ User (Người dùng) đọc xong và xác nhận "Đồng ý" hoặc "Approve" rồi mới được bắt đầu gõ code/sửa file.**

## 2. QUY TẮC PHÂN TÍCH LỖI
- Không bao giờ được "đoán mò" nguyên nhân lỗi mà không có bằng chứng (Ví dụ: Không tự ý kết luận lỗi do format chuỗi, lỗi do thiếu file... nếu chưa tự mình dùng lệnh đọc dòng code đó hoặc check lịch sử Git).
- Phải tìm ra **chính xác** dòng code gây ra lỗi trước khi đưa ra Plan.

## 3. QUY TẮC XỬ LÝ ĐƯỜNG DẪN (PATH RESOLUTION)
- Hệ thống đang hoạt động tốt với cấu trúc dùng `self.project_base_dir` cho đường dẫn tương đối (ví dụ trong `config_loader.py` hay `handlers.py`).
- Tuyệt đối không được "chữa cháy" lỗi đường dẫn bằng cách hard-code (gắn cứng) đường dẫn tuyệt đối (Absolute Path) như `/home/user/...` vào trong mã nguồn. Điều này sẽ làm phá vỡ tính tương thích đa nền tảng của phần mềm.

## 4. GHI NHỚ LỊCH SỬ GIAO DIỆN VÀ TÍNH NĂNG
- Trước khi thêm, xóa hay sửa một phần của giao diện (ví dụ: các Dropdown cập nhật phần mềm, Preset Manager, Target Language), phải chú ý đến các cơ chế **Tự động làm mới (Auto-Refresh/Filter)**.
- Khi thêm một tùy chọn mới vào Dropdown, phải nhớ thêm nó vào cả hàm tạo ban đầu (`_create_combobox`) LẪN các hàm tự làm mới (`_refresh_combobox_values` và `_filter_translator_dropdowns`).

---

## 5. QUY TẮC ĐỘC LẬP DỰ ÁN (PROJECT INDEPENDENCE)
- Dự án `Bimatkeo_Translator` được thiết kế hoạt động hoàn toàn **ĐỘC LẬP** với dự án gốc `manga-image-translator` ở cấp độ lưu trữ và cấu trúc thư mục.
- Tuyệt đối KHÔNG ĐƯỢC ép buộc hoặc sửa đổi các đường dẫn lưu trữ model/file của `Bimatkeo_Translator` (ví dụ: `models/Offline Translator/...`) về lại cấu trúc cũ của backend `manga-image-translator` (như `models/translators/...`). Việc tải và lưu trữ model phải tuân thủ nghiêm ngặt hệ sinh thái riêng của dự án này.

*(Bất cứ AI nào đọc được file này, hãy tự ý thức việc tuân thủ để tránh làm sai lệch cấu trúc dự án và gây mất thời gian cho lập trình viên!)*
