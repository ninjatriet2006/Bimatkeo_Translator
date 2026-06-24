import os

output_file = '/home/bimatkeo/.gemini/antigravity-ide/skills/python-ai/SKILL.md'

content = """---
name: python-ai
description: Cẩm nang toàn tập (Master Guide) về kiến trúc chuyên sâu, lập trình UI (PySide6) và tích hợp AI cho các dự án Python Desktop.
user-invocable: false
---

# 🧠 Master Python AI Skill: Core Architecture & Evolution Patterns (Extended Edition)

> **AUTO-UPDATE PROTOCOL:** Tệp này được hệ thống Antigravity duy trì tự động. Bất kỳ bài học, sửa lỗi, hay thiết kế mới nào liên quan đến Python/AI Desktop UI bắt buộc phải được cập nhật trực tiếp vào tệp này theo [Self-Evolution Protocol](file:///home/bimatkeo/.gemini/antigravity-ide/skills/self-evolution/SKILL.md).

Tài liệu này là bản **COMPACT ĐẠI HOÀN THIỆN**, chứa các pattern (thiết kế mẫu), kỹ thuật tối ưu hóa mã nguồn, xử lý đa luồng, và tích hợp AI. Nó được chắt lọc để trở thành chân lý thiết kế tuyệt đối cho các ứng dụng Python Desktop hiện đại. Mọi dòng code viết ra trong tương lai đều phải đối chiếu với cẩm nang này.

---

## 1. 🏗️ The Anti-Monolith Rule: Modularity via Mixins (Mở rộng)

### 1.1. Vấn Đề Của Kiến Trúc Cổ Điển
Trong PyQt6/PySide6, `QMainWindow` là trung tâm của mọi sự chú ý. Lập trình viên mới thường nhồi nhét:
- Khởi tạo UI (`setCentralWidget`, `QGridLayout`)
- Đọc/Ghi dữ liệu (`json.load()`, `yaml.safe_load()`)
- Bắt sự kiện (`button.clicked.connect()`)
- Gọi API (`requests.post()`)
vào cùng một file `main_window.py`. Điều này dẫn đến hiện tượng **Spaghetti Code** khi file chạm mốc hàng nghìn dòng.

### 1.2. Giải Pháp: Domain-Driven Mixins
Chia ứng dụng thành các domain tách biệt. Dưới đây là kiến trúc chuẩn:

```python
# --- File: core/registry.py ---
class RegistryMixin:
    \"\"\"Quản lý Single Source of Truth (SSOT) cho cấu hình.\"\"\"
    def __init__(self):
        # Không gọi super().__init__() ở đây vì nó là Mixin
        self.app_settings = self._load_settings()
        self.api_profiles = self._load_profiles()

    def _load_settings(self) -> dict:
        # Cố gắng đọc từ đĩa, nếu lỗi thì dùng seed mặc định
        pass

# --- File: ui/builders.py ---
class WidgetBuildersMixin:
    \"\"\"Nhà máy sản xuất UI (Factory). Tuyệt đối không chứa logic lưu data.\"\"\"
    def _create_api_selector(self) -> QWidget:
        # Chỉ tạo ra QComboBox và gán CSS class/ToolTip
        return QComboBox()

# --- File: ui/handlers.py ---
class HandlersMixin:
    \"\"\"Điều phối viên (Coordinator). Kết nối Builder với Registry.\"\"\"
    def _bind_signals(self):
        # Kết nối tín hiệu của UI từ Builder để cập nhật dữ liệu vào Registry
        pass

# --- File: main.py ---
class AppMainWindow(QMainWindow, WidgetBuildersMixin, HandlersMixin, RegistryMixin):
    def __init__(self):
        super().__init__() # Khởi tạo QMainWindow
        RegistryMixin.__init__(self) # Nạp dữ liệu
        
        self.setup_ui() # Từ WidgetBuildersMixin
        self._bind_signals() # Từ HandlersMixin
```

### 1.3. Lợi Ích Của Thiết Kế Này
- **Phẳng hóa không gian tên (Flat Namespace):** Gọi `self._load_settings()` trực tiếp thay vì `self.registry._load_settings()`.
- **Dễ Unit Test:** Có thể test `RegistryMixin` độc lập bằng cách tạo một class giả (Mock Class) kế thừa nó.

---

## 2. ⚙️ Data-Driven UI (Config-First Architecture)

Giao diện không bao giờ được hardcode trong Python. Đây là cốt lõi của tính linh hoạt.

### 2.1. YAML Schema Tiêu Chuẩn
Một file `studio_config.yaml` định nghĩa hoàn toàn cấu trúc các Form cài đặt:

```yaml
Audio_Transcription:
  audio_model:
    widget: ai_model_selector
    service: Audio
    label: "Mô Hình AI Nhận Diện:"
    order: 1
    default: "whisper-1"
  use_gpu:
    widget: checkbox
    label: "Tăng tốc GPU (CUDA):"
    order: 2
    default: true
```

### 2.2. Thuật Toán Render UI Động
Thuật toán phân tích file YAML, sinh UI và tự động gán giá trị mặc định từ Local Settings:

```python
def render_dynamic_form(self, group_data: dict, current_settings: dict) -> QWidget:
    container = QWidget()
    layout = QFormLayout(container)
    
    # Sort items theo thuộc tính 'order'
    sorted_items = sorted(group_data.items(), key=lambda item: item[1].get('order', 99))
    
    for key, attrs in sorted_items:
        widget_type = attrs.get('widget')
        builder_method = getattr(self, f"_create_{widget_type}_widget", None)
        
        if builder_method:
            widget = builder_method(attrs)
            
            # Gán giá trị khởi tạo từ current_settings hoặc default của YAML
            saved_value = current_settings.get(key, attrs.get('default'))
            self._set_widget_value_safely(widget, saved_value)
            
            # Kết nối tín hiệu thay đổi về hệ thống chung
            self._connect_generic_signal(key, widget)
            
            layout.addRow(attrs.get('label', key), widget)
            
    return container
```

---

## 3. 🔌 Dynamic Event Routing & State Synchronization

Bắt từng tín hiệu thủ công (e.g., `btn_save.clicked.connect(...)`) là cách làm tồi tệ nhất khi mở rộng.

### 3.1. Kỹ Thuật Lambda Injection
Khi tạo hàng loạt widget tự động, ta tiêm (inject) tham số `key` vào hàm bắt sự kiện bằng closure (cần lưu ý hiện tượng "late binding" trong Python):

```python
# CÁCH LÀM SAI (LATE BINDING BUG):
# for key in keys:
#     widget.textChanged.connect(lambda text: self.update(key, text))
# => Tất cả các widget sẽ trỏ về `key` cuối cùng của vòng lặp!

# CÁCH LÀM ĐÚNG (EARLY BINDING):
for key, widget in widgets.items():
    widget.textChanged.connect(lambda text, k=key: self.update_setting(k, text))
```

### 3.2. Cập Nhật Visibility Dựa Trên State
Trạng thái UI (hiện ô nhập API, giấu ô Offline Model) phải hoàn toàn vô hướng (stateless) và dựa vào giá trị đang lưu.

```python
def _update_audio_visibility(self):
    mode = self.current_settings.get('audio_mode', 'Offline')
    
    # Sử dụng dictionary comprehension để ẩn/hiện hàng loạt widget nhanh chóng
    visibility_map = {
        'api_key': mode == 'Online',
        'endpoint_url': mode == 'Online',
        'offline_model_path': mode == 'Offline',
        'cuda_cores': mode == 'Offline'
    }
    
    for widget_key, is_visible in visibility_map.items():
        if widget_key in self.ui_widgets:
            self.ui_widgets[widget_key].setVisible(is_visible)
```

---

## 4. 🛡️ Cấu Trúc Dữ Liệu Bền Vững (Registry & Auto-Healing)

File cấu hình của người dùng nằm trên ổ cứng có thể bị mất quyền truy cập, bị xóa nhầm, hoặc bị ghi đè lỗi. Hệ thống phải MIỄN NHIỄM với các tai nạn này.

### 4.1. Khởi Tạo Seed Tự Động (Auto-Seeding)
```python
def _load_or_seed_config(self, filepath: str, seed_generator_func) -> dict:
    if not os.path.exists(filepath):
        print(f"[INFO] File {filepath} bị mất. Tiến hành tạo Seed...")
        seed_data = seed_generator_func()
        self._write_yaml(filepath, seed_data)
        return seed_data
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            # Kiểm tra tính vẹn toàn (Sanity Check)
            if not isinstance(data, dict):
                raise ValueError("Cấu trúc file bị hỏng (Không phải Dict).")
            return data
    except Exception as e:
        print(f"[ERROR] Hỏng file {filepath}: {e}. Đang reset về Seed...")
        return seed_generator_func()
```

### 4.2. Graceful Fallback Khi Thiếu Mô Hình
Nếu hệ thống gọi `gemini-1.5-pro` nhưng API báo lỗi hoặc Model không khả dụng, hệ thống phải tự lùi về `gemini-1.5-flash` và báo cho người dùng bằng UI tĩnh (không throw Exception văng app).

```python
def resolve_model_fallback(self, requested_model: str, task_type: str) -> str:
    available_models = self.get_available_models(task_type)
    if requested_model in available_models:
        return requested_model
        
    # Mạng lưới dự phòng
    fallback_chain = {
        'Translation': ['gemini-1.5-flash', 'gpt-3.5-turbo', 'llama3'],
        'OCR': ['gemini-1.5-flash', 'gpt-4o-mini']
    }
    
    for fallback in fallback_chain.get(task_type, []):
        if fallback in available_models:
            self.show_toast_notification(f"Model {requested_model} bị thiếu. Đã lùi về {fallback}.")
            return fallback
            
    raise CriticalModelMissingError("Không có bất kỳ model dự phòng nào khả dụng!")
```

---

## 5. ⚡ Job Runner & Concurrency (Bất Đồng Bộ Trong PySide6)

Tuyệt đối cấm sử dụng `time.sleep()`, vòng lặp vô tận `while True`, hoặc gọi API trực tiếp trên GUI Thread. Nó sẽ chặn Event Loop và làm cửa sổ treo (Not Responding).

### 5.1. Sử Dụng QRunnable Và QThreadPool Chuẩn Mực
Khác với `QThread`, `QRunnable` nhẹ hơn và được quản lý bằng Pool. Cần sử dụng kết hợp với một lớp Signals (kế thừa `QObject`) vì `QRunnable` không thể phát tín hiệu PyQt natively.

```python
from PySide6.QtCore import QRunnable, QObject, Signal, Slot, QThreadPool

class WorkerSignals(QObject):
    finished = Signal()
    error = Signal(str, str) # title, detail
    progress = Signal(int, str)
    result = Signal(object)

class APIWorker(QRunnable):
    def __init__(self, api_func, *args, **kwargs):
        super().__init__()
        self.api_func = api_func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
    @Slot()
    def run(self):
        try:
            self.signals.progress.emit(10, "Đang khởi tạo kết nối...")
            response = self.api_func(*self.args, **self.kwargs)
            self.signals.progress.emit(100, "Hoàn tất.")
            self.signals.result.emit(response)
        except Exception as e:
            import traceback
            self.signals.error.emit("API Error", traceback.format_exc())
        finally:
            self.signals.finished.emit()
```

### 5.2. Quản Lý Trạng Thái UI Trong Khi Chạy (State Locking)
Trước khi đưa Job vào ThreadPool, phải khóa các nút bấm để ngăn người dùng click liên tục.

```python
def execute_translation_job(self, text: str):
    # 1. Khóa giao diện
    self.ui.btn_translate.setEnabled(False)
    self.ui.loading_spinner.start()
    
    # 2. Tạo worker
    worker = APIWorker(self.api_client.translate, text)
    
    # 3. Ràng buộc tín hiệu
    worker.signals.result.connect(self._on_translation_success)
    worker.signals.error.connect(self._on_translation_failed)
    
    # 4. Luôn mở khóa UI trong finally (khi có finished)
    worker.signals.finished.connect(lambda: self.ui.btn_translate.setEnabled(True))
    worker.signals.finished.connect(self.ui.loading_spinner.stop)
    
    # 5. Khởi chạy
    QThreadPool.globalInstance().start(worker)
```

---

## 6. 🤖 Abstraction Layer Trừu Tượng Hóa Đa Mô Hình AI (Multi-Vendor Abstraction)

Khi làm việc với nhiều LLM (Gemini, OpenAI, Anthropic, DeepSeek, Local Ollama), phần lõi xử lý phải được cô lập với phần API.

### 6.1. System Message & Context Window Management
Mọi API đều có giới hạn Tokens. Bắt buộc phải có thuật toán ước lượng hoặc cắt tỉa độ dài (Pruning) trước khi gửi đi.

```python
def prepare_payload(self, system_prompt: str, user_text: str, max_tokens: int) -> dict:
    # Kỹ thuật xấp xỉ token: 1 token ~ 4 ký tự tiếng Anh, 1 ký tự tiếng Trung/Nhật
    approx_length = len(user_text) // 3 
    
    if approx_length > max_tokens:
        # Cắt bớt phần đuôi hoặc chia đoạn (Chunking)
        user_text = user_text[:max_tokens * 3] + "...[TRUNCATED]"
        
    return {
        "model": self.model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0.3
    }
```

### 6.2. Abstract Translator Provider Pattern
```python
class BaseAIProvider(ABC):
    @abstractmethod
    def translate(self, text: str, source: str, target: str) -> str:
        pass

class OpenAITranslator(BaseAIProvider):
    def translate(self, text, source, target):
        # Implement call to api.openai.com
        pass

class GeminiTranslator(BaseAIProvider):
    def translate(self, text, source, target):
        # Implement call to Google SDK
        pass

class TranslatorFactory:
    @staticmethod
    def get_provider(endpoint_url: str, api_key: str) -> BaseAIProvider:
        url = endpoint_url.lower()
        if "googleapis" in url or "gemini" in url:
            return GeminiTranslator(api_key)
        elif "openai.com" in url or "proxy" in url:
            return OpenAITranslator(api_key)
        else:
            raise ValueError(f"Không thể nhận diện chuẩn API cho endpoint: {endpoint_url}")
```

---

## 7. 📁 Quản Lý Hệ Thống Tệp (File System & Path Safety)

Mọi thao tác đọc/ghi file trong Python Desktop đều phải an toàn trên mọi hệ điều hành (Windows, macOS, Linux).

### 7.1. Cấm Dùng Đường Dẫn Tuyệt Đối Khép Kín (Hardcoded Absolute Paths)
Không bao giờ dùng: `config_path = "C:/Users/Bimatkeo/Config/app.json"`

### 7.2. Chuẩn Hóa Qua Project Base Directory
```python
import os
import sys

class PathManager:
    @staticmethod
    def get_base_dir() -> str:
        # Xử lý tương thích khi đóng gói thành file .exe bằng PyInstaller
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    @staticmethod
    def get_config_dir() -> str:
        target = os.path.join(PathManager.get_base_dir(), ".config")
        os.makedirs(target, exist_ok=True)
        return target
```

---

## 8. 🐛 Logging Hệ Thống Trong Suốt (Transparent Logging UI)

Giao diện ứng dụng cần có một màn hình hoặc hộp thoại hiển thị trực tiếp Console Output thay vì bắt người dùng mở Terminal.

### 8.1. Custom Logging Handler Cho PySide6
Tạo một Custom Handler để dẫn (pipe) luồng log gốc của Python (module `logging`) vào một `QTextEdit`.

```python
import logging
from PySide6.QtCore import Signal, QObject

class QtLogSignals(QObject):
    log_emitted = Signal(str)

class QtLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.signals = QtLogSignals()

    def emit(self, record):
        msg = self.format(record)
        # Bắn signal an toàn về UI Thread
        self.signals.log_emitted.emit(msg)

# Ở phần khởi tạo UI:
# logger_handler = QtLogHandler()
# logger_handler.signals.log_emitted.connect(self.ui.text_edit_console.append)
# logging.getLogger().addHandler(logger_handler)
```

---

## 9. 🎨 Nguyên Lý Tối Ưu UX (User Experience)

### 9.1. Quản Lý Chuỗi Hoạt Họa (Micro-Animations)
UI Python thường có cảm giác bị "cứng". Hãy thêm `QPropertyAnimation` cho các thẻ (tabs) hoặc hiệu ứng mờ (fade in) khi hiện các thông báo lỗi.
- Đổi màu viền input thành Đỏ khi gặp lỗi, Kèm hiệu ứng rung (Shake).
- Dùng `QGraphicsOpacityEffect` để tạo hiệu ứng mờ dần (fade out) cho các tin nhắn Toast.

### 9.2. Phân Tách Ngôn Ngữ Bằng Tệp Tin Rời (Internationalization)
Dù bạn đang thiết kế UI bằng code hay YAML, mọi dòng chuỗi hiển thị lên giao diện (ví dụ: "Chế Độ Dịch", "Cài Đặt") phải được bao bọc bởi một hàm dịch thuật `_()`.

```python
def _(key: str) -> str:
    # Hàm load bản dịch từ i18n_vi.json hoặc i18n_en.json
    return translation_registry.get(key, key)
    
# Gán nhãn cho nút
self.btn_save.setText(_("ui.button.save"))
```

---

# 🛑 TỔNG KẾT & QUY CHUẨN KẾT THÚC
Đây là **Bản Di Chúc Lập Trình (The Ultimate Manifesto)** cho mọi tương tác về Python AI Desktop. Antigravity IDE và mọi AI nội bộ khi truy xuất tệp này phải đọc và áp dụng triệt để. Nếu bạn sửa lỗi một chức năng, hãy đối chiếu xem mình đã tuân thủ Mixins chưa? Đã dùng QRunnable chưa? Đã tự động tạo Seed File chưa? Nếu rồi, bạn đã đáp ứng được Tiêu Chuẩn Vàng của hệ thống tiến hóa này.

(END OF DEEP COMPACTION)
"""

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Massive SKILL.md generated successfully at {output_file}. Length: {len(content.splitlines())} lines.")
