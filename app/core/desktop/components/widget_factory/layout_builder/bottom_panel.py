"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.widget_factory.layout_builder.bottom_panel
- RESPONSIBILITY: Build the bottom UI panel (progress bar, start/stop buttons).
- CALLED BY: app.core.desktop.components.widget_factory.layout_builder.__init__ (as Mixin)
- CALLS TO: PySide6.QtWidgets
- IN = OUT: Returns QWidget containing bottom panel controls and stores references in self.mw.
=============================================================================
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QFrame, QLabel, QProgressBar, QPushButton

class BottomPanelBuilderMixin:
    def create_bottom_panel(self) -> QWidget:
        bottom_frame = QFrame()
        bottom_frame.setFrameShape(QFrame.Shape.NoFrame)
        layout = QHBoxLayout(bottom_frame)
        layout.setContentsMargins(0, 0, 0, 0)

        progress_widget = QWidget()
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setSpacing(10)
        progress_layout.setContentsMargins(5, 5, 5, 5)

        self.mw.progress_label = QLabel(self.mw.get_string("ui_status_ready") if self.mw.get_string("ui_status_ready") != "ui_status_ready" else "Ready")
        self.mw.progress_label.setProperty("lang_id", "ui_status_ready")
        self.mw.progress_label.setProperty("lang_type", "ui")
        self.mw.progress_label.setMinimumWidth(200)

        self.mw.progress_bar = QProgressBar()
        self.mw.progress_bar.setValue(0)
        self.mw.progress_bar.setTextVisible(False)
        self.mw.progress_bar.setFormat("%p% - %v/%m pages")

        progress_layout.addWidget(self.mw.progress_label)
        progress_layout.addWidget(self.mw.progress_bar, stretch=1)

        self.mw.start_button = QPushButton(self.mw.get_string("ui_btn_start") if self.mw.get_string("ui_btn_start") != "ui_btn_start" else "▶️ START")
        self.mw.start_button.setProperty("lang_id", "ui_btn_start")
        self.mw.start_button.setProperty("lang_type", "ui")
        self.mw.start_button.clicked.connect(self.mw._start_pipeline_thread)
        self.mw.start_button.setFixedHeight(40)
        font = self.mw.start_button.font()
        font.setBold(True)
        self.mw.start_button.setFont(font)

        self.mw.stop_button = QPushButton(self.mw.get_string("ui_btn_stop") if self.mw.get_string("ui_btn_stop") != "ui_btn_stop" else "⏹️ STOP")
        self.mw.stop_button.setProperty("lang_id", "ui_btn_stop")
        self.mw.stop_button.setProperty("lang_type", "ui")
        self.mw.stop_button.clicked.connect(self.mw._stop_pipeline)
        self.mw.stop_button.setEnabled(False)
        self.mw.stop_button.setFixedHeight(40)
        stop_font = self.mw.stop_button.font()
        stop_font.setBold(True)
        self.mw.stop_button.setFont(stop_font)

        layout.addWidget(progress_widget, stretch=1)
        layout.addWidget(self.mw.start_button)
        layout.addWidget(self.mw.stop_button)

        return bottom_frame
