import re

file_path = "desktop_ui/mainwindow/handlers.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_content = content.replace("self._software_worker.finished.connect(on_finished)", "self._software_worker.finished.connect(on_finished)\n        self._software_worker.progress.connect(on_progress)")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
