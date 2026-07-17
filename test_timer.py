import sys
from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtCore import QTimer
import threading
import time

app = QApplication(sys.argv)
btn = QPushButton("Wait")
btn.show()

def bg_thread():
    time.sleep(1)
    print("Calling QTimer.singleShot...")
    QTimer.singleShot(0, lambda: btn.setText("Done"))
    print("Called!")
    time.sleep(1)
    app.quit()

threading.Thread(target=bg_thread, daemon=True).start()
sys.exit(app.exec())
