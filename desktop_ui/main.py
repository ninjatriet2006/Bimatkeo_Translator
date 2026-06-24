import os
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon

# Configure path: Add the parent directory of 'desktop_ui' (the project root) to sys.path
# so we can import app and other packages if needed.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

try:
    from desktop_ui.main_window import TranslatorStudioApp
except ImportError as e:
    error_app = QApplication(sys.argv)
    QMessageBox.critical(
        None,
        "Fatal Import Error",
        "Could not import the main application window.\n\n"
        f"Error: {e}"
    )
    sys.exit(1)


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setWindowIcon(QIcon(os.path.join(BASE_DIR, "assets", "app_icon.png")))
        main_window = TranslatorStudioApp()
        main_window.show()
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        error_title = "Critical Application Error"
        error_message = (
            "The application encountered a critical error and had to shut down.\n\n"
            f"Error Type: {type(e).__name__}\n"
            f"Error Details: {e}\n\n"
            "Please check the console output for the full traceback."
        )
        print(f"---! {error_title.upper()} !---")
        traceback.print_exc()
        print("---------------------------------")
        error_app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, error_title, error_message)
        sys.exit(1)
