import time
import os
import sys
from PySide6.QtWidgets import QApplication

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

app = QApplication(sys.argv)

print("Starting import...")
t0 = time.time()
from desktop_ui.main_window import TranslatorStudioApp
t1 = time.time()
print(f"Import took {t1 - t0:.3f} seconds")

print("Instantiating app...")
t2 = time.time()
main_window = TranslatorStudioApp()
t3 = time.time()
print(f"Instantiation took {t3 - t2:.3f} seconds")

print("Done profiling startup.")
sys.exit(0)
