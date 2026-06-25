import sys
import os
from PySide6.QtWidgets import QApplication
from desktop_ui.main_window import TranslatorStudioApp
from PySide6.QtCore import QTimer
import cv2
import numpy as np

# Create dummy image
dummy_img = np.ones((500, 500, 3), dtype=np.uint8) * 255
dummy_path = os.path.abspath("temp/dummy_test.png")
os.makedirs("temp", exist_ok=True)
cv2.imwrite(dummy_path, dummy_img)

app = QApplication(sys.argv)
window = TranslatorStudioApp()
window.test_image_path = dummy_path

# Mute message boxes
import PySide6.QtWidgets
PySide6.QtWidgets.QMessageBox.warning = lambda *args: None
PySide6.QtWidgets.QMessageBox.critical = lambda *args: None

print("Starting visual test...")
window._run_visual_test_thread()

def check_result():
    if window.run_test_button.isEnabled():
        print("Test finished!")
        out_dir = os.path.abspath("temp/dummy_test_translated_test")
        print("Checking output dir:", out_dir)
        if os.path.exists(out_dir):
            print("Files in output dir:", os.listdir(out_dir))
        else:
            print("Output dir not found.")
        app.quit()

timer = QTimer()
timer.timeout.connect(check_result)
timer.start(1000)

QTimer.singleShot(20000, app.quit) # timeout
app.exec()
