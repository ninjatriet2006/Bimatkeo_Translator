import re

file_path = "desktop_ui/mainwindow/handlers.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_connection = """        from PySide6.QtWidgets import QProgressDialog
        progress_dlg = QProgressDialog(f"Đang kiểm tra cập nhật cho {translator_name}...", "Hủy", 0, 100, self)
        progress_dlg.setWindowTitle("Cập nhật Mô hình Dịch")
        from PySide6.QtCore import Qt
        progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dlg.setMinimumDuration(0)
        progress_dlg.show()

        self._software_worker = TranslatorSoftwareUpdateWorker()
        progress_dlg.canceled.connect(self._software_worker.terminate)
        
        def on_progress(val, text):
            progress_dlg.setValue(val)
            progress_dlg.setLabelText(text)
            
        def on_finished(success, message):
            progress_dlg.setValue(100)
            progress_dlg.close()
            for k in ['offline_translator', 'ai_translator']:"""

old_connection_pattern = re.compile(
    r"        self\._software_worker = TranslatorSoftwareUpdateWorker\(\)\n"
    r"\s+def on_finished\(success, message\):\n"
    r"            for k in \['offline_translator', 'ai_translator'\]:",
    re.MULTILINE
)

if not old_connection_pattern.search(content):
    print("Could not find connection pattern.")
else:
    new_content = old_connection_pattern.sub(new_connection, content)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Replaced connection successfully.")
