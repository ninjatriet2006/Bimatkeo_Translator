"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.preview_panel
- RESPONSIBILITY: preview_panel.py module logic.
- CALLED BY: Various
- CALLS TO: Various
- IN = OUT: Defines logic for app.core.desktop.components.preview_panel.
=============================================================================
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                               QPushButton, QCheckBox, QLabel, QSplitter)
from PySide6.QtCore import Qt
from app.core.desktop.components.preview_widgets.interactive_canvas import InteractivePreviewCanvas
from app.core.desktop.components.preview_widgets.inspector_panel import InspectorPanel

class PreviewPanel(QWidget):
    """UI Component for the Preview Tester tab."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 1. Top Controls Panel
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)

        self.load_button = QPushButton("Load Test Image...")
        
        self.fast_preview_check = QCheckBox("Fast Preview")
        self.fast_preview_check.setChecked(True)

        self.run_test_button = QPushButton("Run Test")
        self.run_test_button.setEnabled(False)

        self.reset_button = QPushButton("Reset View")
        
        self.zoom_label = QLabel("Zoom: 100%")

        self.limit_zoom_check = QCheckBox("Limit Zoom")
        self.limit_zoom_check.setChecked(True)
        self.limit_zoom_check.setToolTip("When checked, zoom is limited between 5% and 800%.")

        controls_layout.addWidget(self.load_button)
        controls_layout.addWidget(self.fast_preview_check)
        controls_layout.addStretch()
        controls_layout.addWidget(self.zoom_label)
        controls_layout.addWidget(self.reset_button)
        controls_layout.addWidget(self.run_test_button)

        layout.addWidget(controls_frame)

        # 2. Unified Canvas and Inspector
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.canvas = InteractivePreviewCanvas()
        self.inspector = InspectorPanel()
        
        self.splitter.addWidget(self.canvas)
        self.splitter.addWidget(self.inspector)
        
        # Set stretch factor so canvas takes most space
        self.splitter.setStretchFactor(0, 4)
        self.splitter.setStretchFactor(1, 1)

        layout.addWidget(self.splitter, stretch=1)
