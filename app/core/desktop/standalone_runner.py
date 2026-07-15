"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.standalone_runner
- RESPONSIBILITY: Bootstraps the Standalone UI for specific tools (OCR, Translator).
- CALLED BY: MainWindow via subprocess, or CLI.
- CALLS TO: app.core.desktop.components.standalone.*
- IN = OUT: Spawns a QApplication.
=============================================================================
"""
import sys
import argparse
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
import os

# Add workspace root to sys.path
workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

class StandaloneWindow(QMainWindow):
    def __init__(self, tool_name: str):
        super().__init__()
        self.setWindowTitle(f"Standalone {tool_name.capitalize()}")
        self.resize(800, 600)
        
        self.tool_name = tool_name
        self._load_tool()

    def _load_tool(self):
        if self.tool_name.lower() == "translator":
            from app.core.desktop.components.standalone.translator_widget import TranslatorStandaloneWidget
            widget = TranslatorStandaloneWidget(self)
            self.setCentralWidget(widget)
        elif self.tool_name.lower() == "ocr":
            from app.core.desktop.components.standalone.ocr_widget import OCRStandaloneWidget
            widget = OCRStandaloneWidget(self)
            self.setCentralWidget(widget)
        else:
            QMessageBox.critical(self, "Error", f"Unknown standalone tool: {self.tool_name}")
            self.close()

def main():
    parser = argparse.ArgumentParser(description="Standalone Tool Runner")
    parser.add_argument("--tool", type=str, required=True, help="Tool to launch (e.g. translator, ocr)")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    
    # Simple style
    app.setStyle("Fusion")
    
    window = StandaloneWindow(args.tool)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
