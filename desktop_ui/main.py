import os
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon

# Configure path: Add the parent directory of 'desktop_ui' (the project root) to sys.path
# so we can import app and other packages if needed.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Set HF_HOME so all huggingface cache goes to the app's models folder
os.environ["HF_HOME"] = os.path.join(BASE_DIR, "models", "huggingface_cache")

# Load network configurations for HF Mirror
network_cfg_path = os.path.join(BASE_DIR, ".config", "configs", "network.yaml")
if os.path.exists(network_cfg_path):
    try:
        from ruamel.yaml import YAML
        yaml = YAML()
        with open(network_cfg_path, "r", encoding="utf-8") as f:
            net_cfg = yaml.load(f)
            if net_cfg and net_cfg.get("enable_hf_mirror"):
                hf_endpoint = net_cfg.get("hf_endpoint")
                if hf_endpoint:
                    os.environ["HF_ENDPOINT"] = hf_endpoint
    except Exception as e:
        print(f"Warning: Failed to load network config: {e}")

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
