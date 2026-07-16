import sys
import threading
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

app = QApplication(sys.argv)

def fail():
    print("fail called")
    app.quit()

def _load():
    try:
        QTimer.singleShot(0, fail)
    except Exception as e:
        print("Exception:", e)

threading.Thread(target=_load).start()
app.exec()
