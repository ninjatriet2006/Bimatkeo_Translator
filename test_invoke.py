import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QMetaObject, Qt, QObject

app = QApplication(sys.argv)
class Test(QObject):
    pass
t = Test()
try:
    QMetaObject.invokeMethod(t, lambda: print("hi"), Qt.QueuedConnection)
    print("Success")
except Exception as e:
    print("Fail:", e)
