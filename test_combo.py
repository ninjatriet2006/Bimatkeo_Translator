import sys
from PySide6.QtWidgets import QApplication, QComboBox

app = QApplication(sys.argv)
combo = QComboBox()
combo.addItems(["A", "B", "C"])

def on_change(idx):
    print("Changed to:", idx)

combo.currentIndexChanged.connect(on_change)
combo.setCurrentIndex(1)
combo.setCurrentIndex(2)
