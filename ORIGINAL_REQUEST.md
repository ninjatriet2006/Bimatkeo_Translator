# Original User Request

## Initial Request — 2026-07-27T01:35:44+07:00

Sửa chữa lỗi UI/nút bấm, tái cấu trúc mô-đun hóa độc lập và xây dựng bộ kiểm thử pytest tự động cho ứng dụng dịch thuật Bimatkeo_Translator.

Working directory: /home/bimatkeo/Documents/Translator/Bimatkeo_Translator
Integrity mode: development

## Requirements

### R1. Sửa toàn bộ lỗi nút bấm UI & Đa ngôn ngữ (Localization by ID)
- Kiểm tra và khắc phục tất cả các nút bấm, menu và tính năng bị hỏng hoặc phản hồi sai trên UI.
- Loại bỏ toàn bộ văn bản hardcode trên UI. Bắt buộc áp dụng cơ chế ID Linking (`lang_id`, `lang_type`) và cập nhật qua hàm `update_language_ui`.

### R2. Tái cấu trúc theo hướng Mô-đun hóa (Decoupling)
- Chia nhỏ các thành phần monolithic thành các mô-đun độc lập, giảm thiểu sự phụ thuộc lẫn nhau giữa các thành phần để tránh lỗi dây chuyền và giảm tải cho hệ thống.

### R3. Xây dựng và thực thi bộ kiểm thử tự động (Test Suite)
- Viết bộ kiểm thử (dùng pytest) covering logic tính năng, các nút bấm UI, và liên kết ngôn ngữ tự động.

## Acceptance Criteria

### UI & Functional Correctness
- [ ] 100% các nút bấm và thành phần giao diện thực thi đúng chức năng mong đợi không phát sinh lỗi ngoại lệ (exception).
- [ ] Tất cả UI widget được gán thuộc tính `lang_id` và không chứa text hiển thị hardcode.

### Architecture & Isolation
- [ ] Các mô-đun quản lý logic chính được tách biệt, giao tiếp qua interface rõ ràng, hạn chế tối đa phụ thuộc trực tiếp (decoupled).

### Verification & Testing
- [ ] Chạy câu lệnh kiểm thử `pytest` đạt kết quả pass 100% không có lỗi hỏng (0 failures).
