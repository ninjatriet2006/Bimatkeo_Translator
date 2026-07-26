# UI & Localization Audit Handoff Report

## 1. Observation

Direct observations from surveying the `Bimatkeo_Translator` codebase and test suite execution:

### A. Original Request & Requirements Mapping (`ORIGINAL_REQUEST.md`)
- **R1. Sửa toàn bộ lỗi nút bấm UI & Đa ngôn ngữ (Localization by ID)**:
  - Fix all broken/unresponsive buttons, menus, and features.
  - Remove all hardcoded UI strings. Require ID Linking (`lang_id`, `lang_type`) updated via `update_language_ui()`.
- **R2. Tái cấu trúc theo hướng Mô-đun hóa (Decoupling)**:
  - Decouple monolithic components into independent modules.
- **R3. Xây dựng và thực thi bộ kiểm thử tự động (Test Suite)**:
  - Write pytest suite covering feature logic, UI buttons, and automatic language linking.
  - Command `pytest` must pass 100% (0 failures / 0 collection errors).

### B. Verification & Test Suite Failure Output
Running `./.venv/bin/pytest` produced 6 collection errors (0 passed):
```
=========================== short test summary info ============================
ERROR test_check.py - ImportError: cannot import name 'BimatkeoTranslator' from 'app.core.desktop.main_window'
ERROR test_invoke.py - RuntimeError: libshiboken: Please destroy the QApplication singleton before creating a new QApplication instance.
ERROR test_merge.py - KeyError: 'General & Translator'
ERROR test_qtimer_thread.py - RuntimeError: libshiboken: Please destroy the QApplication singleton before creating a new QApplication instance.
ERROR test_real_loader.py - TypeError: RegistryLoader.__init__() missing 1 required positional argument: 'registry_mixin'
ERROR test_timer.py - RuntimeError: libshiboken: Please destroy the QApplication singleton before creating a new QApplication instance.
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
```

### C. Hardcoded UI Strings & Lacking ID Linking (`lang_id`, `lang_type`)
1. **Main Window Top Toolbar (`app/core/desktop/main_window.py`, lines 379–388)**:
   - `btn_queue = QPushButton("📋 Job Queue")`
   - `btn_log = QPushButton("📜 Console Log")`
   - `btn_history = QPushButton("🕒 History")`
   - `btn_preview = QPushButton("🔍 Preview Tester")`
   - `btn_standalone_trans = QPushButton("🌐 Translator Tool")`
   - `btn_standalone_ocr = QPushButton("📝 OCR Tool")`
   - `btn_standalone_inpaint = QPushButton("🖌️ Inpaint Tool")`
   - `btn_standalone_diffusion = QPushButton("✨ Diffusion Tool")`
   - `btn_standalone_render = QPushButton("🎨 Render Tool")`
   - `btn_close_all_standalone = QPushButton("❌ Close Standalones")`
   *Observation*: None of these 10 toolbar buttons have `lang_id` or `lang_type` properties assigned. They remain permanently in English.
2. **Preview Tester Toolbar Controls (`app/core/desktop/components/widget_factory/layout_builder/preview_tester.py`, lines 49–61)**:
   - `self.mw.zoom_label = QLabel("Zoom: 100%")` (missing `lang_id`)
   - `self.mw.limit_zoom_check = QCheckBox("Limit Zoom")` (missing `lang_id`)
   - `self.mw.btn_mode_select = QRadioButton("Select")` (missing `lang_id`)
   - `self.mw.btn_mode_draw = QRadioButton("Draw Box")` (missing `lang_id`)
3. **File Explorer Panel (`app/core/desktop/components/preview_widgets/file_explorer_panel.py`, line 35)**:
   - `btn_select_folder = QPushButton("Select Folder", self)` (missing `lang_id`)
4. **Inspector Panel (`app/core/desktop/components/preview_widgets/inspector_panel.py`, lines 30–60)**:
   - Labels ("Inspector", "Box Coordinates", "Original Text", "Translated Text") & Buttons ("Rerun OCR", "Rerun Translation", "Live Render Box") lack `lang_id` properties.
5. **Font Install Dialog (`app/core/desktop/components/custom_widgets/font_install_dialog.py`, lines 53, 58)**:
   - `btn_install = QPushButton("Cài đặt", self)` & `btn_cancel = QPushButton("Hủy bỏ", self)` (Hardcoded Vietnamese text, missing `lang_id`).
6. **All 5 Standalone Tools (`app/core/desktop/components/standalone/*.py`)**:
   - `translator_widget.py`, `ocr_widget.py`, `inpaint_widget.py`, `diffusion_widget.py`, `render_widget.py`:
     Titles, labels, buttons ("Load Model", "Translate", "Run OCR", "Select Image", "Run Inpaint", "Run Diffusion", "Fetch", "Test") are hardcoded text without `lang_id` property assignments or integration with `update_language_ui()`.
7. **Standalone Window Titles in Main Window (`app/core/desktop/main_window.py`, line 580)**:
   - `self.log_window = StandaloneToolWindow(self, "Console Log", ...)` lacks `lang_id` property on the dialog container.

### D. Identified Code Bugs & Broken Components
1. **Class Name Mismatch in Root Test Script (`test_check.py:4`)**:
   - `from app.core.desktop.main_window import BimatkeoTranslator` raises `ImportError` because main window class is `TranslatorStudioApp`.
2. **Key Error in `test_merge.py:17`**:
   - Attempts to index `UI_TAB_LAYOUT['General & Translator']`, raising `KeyError` because tab dictionary structure was refactored under `config_loader`.
3. **Language Code vs Language Name Mismatch in `tabs.py:85`**:
   - `self.mw.config_loader.apply_language(self.mw.current_settings.get('app_language', 'English'))`: passes language name (e.g. `'English'` or `'Tiếng Việt'`) instead of language code (`'en'` or `'vi'`) when rebuilding tabs, leading to inconsistent lookup in `LanguageManager`.

---

## 2. Logic Chain

1. **Observation**: `update_language_ui()` in `app/core/desktop/main_window.py:266` relies on walking all child widgets recursively and reading `w.property("lang_id")` and `w.property("lang_type")`.
   - **Reasoning**: Any UI widget created without `.setProperty("lang_id", "...")` is invisible to `update_language_ui()`. When the user switches application language between English and Vietnamese, these widgets remain stuck on their original hardcoded text.
   - **Direct Evidence**: The 10 main toolbar buttons (`btn_queue`, `btn_log`, `btn_history`, `btn_preview`, standalone buttons) in `main_window.py:379-388` have no `lang_id` properties.

2. **Observation**: Executing `./.venv/bin/pytest` fails during test collection with 6 errors.
   - **Reasoning**: Prototype/utility scripts in the repository root (`test_check.py`, `test_invoke.py`, `test_qtimer_thread.py`, `test_timer.py`) instantiate `QApplication(sys.argv)` at top-level during file import. PySide6/libshiboken prohibits creating multiple `QApplication` instances in the same process, causing immediate collection crashes.
   - **Direct Evidence**: `RuntimeError: libshiboken: Please destroy the QApplication singleton before creating a new QApplication instance.`

3. **Observation**: `tabs.py:85` executes `apply_language(self.mw.current_settings.get('app_language', 'English'))`.
   - **Reasoning**: `LanguageManager.get_string(lang_id, ...)` expects `lang_id` to be `'en'` or `'vi'`, but `app_language` stores `'English'` or `'Tiếng Việt'` unless mapped. Passing `'English'` causes fallback lookup failure.

---

## 3. Caveats

- **Read-Only Scope**: In accordance with Explorer 1 role constraints, no source code or test files were modified during this investigation.
- **Model Execution Environment**: Hardware VRAM check reported GPU status dynamically. Backend AI model weights (Lama, PaddleOCR, etc.) require proper setup or mock fixtures for unit testing.

---

## 4. Conclusion

1. **UI & Localization**:
   - To achieve 100% compliance with R1, all hardcoded strings in `main_window.py`, `preview_tester.py`, `file_explorer_panel.py`, `inspector_panel.py`, `font_install_dialog.py`, and `standalone/*.py` must be registered with `.setProperty("lang_id", "...")` and corresponding keys added to `en.yaml` and `vi.yaml`.
   - `tabs.py:85` must be updated to pass valid language IDs (`'en'` / `'vi'`).
2. **Automated Testing Suite (Pytest)**:
   - Root-level test scripts need refactoring into a structured `tests/` directory with a shared `pytest-qt` or custom `qapp` fixture in `conftest.py`.
   - Fix class name references (`BimatkeoTranslator` -> `TranslatorStudioApp`) and dictionary keys in test files.

---

## 5. Verification Method

To verify findings independently:

1. **Verify Localization Linkage**:
   ```bash
   python3 -c "
   import os, re
   desktop_dir = 'app/core/desktop'
   for root, _, files in os.walk(desktop_dir):
       for f in files:
           if f.endswith('.py'):
               path = os.path.join(root, f)
               content = open(path).read()
               if 'QPushButton(' in content and 'setProperty(\"lang_id\"' not in content:
                   print('Hardcoded buttons found in:', path)
   "
   ```
2. **Verify Test Suite Collection State**:
   ```bash
   ./.venv/bin/pytest
   ```
   (Expect 6 collection errors currently until refactored by Implementer agent).
