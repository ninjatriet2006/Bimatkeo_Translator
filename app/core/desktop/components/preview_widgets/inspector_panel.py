"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.preview_widgets.inspector_panel
- RESPONSIBILITY: Provide a side panel to edit and view details of a selected BBox.
- CALLED BY: app.core.desktop.components.preview_panel
- CALLS TO: None
- IN = OUT: Defines the inspector widget.
=============================================================================
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QGroupBox, QFormLayout
from PySide6.QtCore import Qt

class InspectorPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self._setup_ui()
        self.clear_inspector()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.lbl_title = QLabel("<b>Box Inspector</b>")
        layout.addWidget(self.lbl_title)

        # Geometry Group
        geom_group = QGroupBox("Geometry")
        geom_layout = QFormLayout(geom_group)
        self.le_x = QLineEdit()
        self.le_y = QLineEdit()
        self.le_w = QLineEdit()
        self.le_h = QLineEdit()
        geom_layout.addRow("X:", self.le_x)
        geom_layout.addRow("Y:", self.le_y)
        geom_layout.addRow("W:", self.le_w)
        geom_layout.addRow("H:", self.le_h)
        layout.addWidget(geom_group)

        # Text Group
        text_group = QGroupBox("Text Data")
        text_layout = QVBoxLayout(text_group)
        text_layout.addWidget(QLabel("OCR Text:"))
        self.te_ocr = QTextEdit()
        self.te_ocr.setMaximumHeight(80)
        text_layout.addWidget(self.te_ocr)
        
        text_layout.addWidget(QLabel("Translated Text:"))
        self.te_translated = QTextEdit()
        self.te_translated.setMaximumHeight(80)
        text_layout.addWidget(self.te_translated)
        layout.addWidget(text_group)

        # Actions Group
        action_group = QGroupBox("Live Actions")
        action_layout = QVBoxLayout(action_group)
        self.btn_rerun_ocr = QPushButton("Rerun OCR")
        self.btn_rerun_trans = QPushButton("Rerun Translation")
        self.btn_render_box = QPushButton("Live Render Box")
        action_layout.addWidget(self.btn_rerun_ocr)
        action_layout.addWidget(self.btn_rerun_trans)
        action_layout.addWidget(self.btn_render_box)
        layout.addWidget(action_group)

        layout.addStretch()

    def clear_inspector(self):
        self.le_x.clear()
        self.le_y.clear()
        self.le_w.clear()
        self.le_h.clear()
        self.te_ocr.clear()
        self.te_translated.clear()
        self.setEnabled(False)

    def load_box_data(self, box_data: dict):
        self.setEnabled(True)
        bbox = box_data.get("bbox", [0, 0, 0, 0])
        self.le_x.setText(str(bbox[0]))
        self.le_y.setText(str(bbox[1]))
        self.le_w.setText(str(bbox[2]))
        self.le_h.setText(str(bbox[3]))
        
        self.te_ocr.setText(box_data.get("original_text", ""))
        self.te_translated.setText(box_data.get("translated_text", ""))
