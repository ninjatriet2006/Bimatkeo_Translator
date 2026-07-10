# type: ignore
# ===============================================================
# Main Application Window (PySide6 Version) - Entry Point
#
# Author: User & Gemini Collaboration
# ===============================================================

import os
import sys
import copy
import subprocess
import threading

# Ensure project root is in sys.path to allow running this script directly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.desktop.constants import *


# PySide6 imports
from PySide6.QtWidgets import (
    QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QProgressBar, QTabWidget, QScrollArea,
    QComboBox, QCheckBox, QButtonGroup, QSlider, QLineEdit, QGridLayout,
    QColorDialog, QMessageBox, QListWidget, QListWidgetItem, QFileDialog,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QTextEdit,
    QApplication, QMenu, QSizePolicy, QDialog
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QByteArray, QEvent, QPoint
from PySide6.QtGui import QFont, QCursor, QStandardItemModel, QFontDatabase, QPixmap, QPainter, QColor, QPalette

from app.core.desktop.config_loader import ConfigLoader

from app.core.desktop.components.widgets_helper import (
    DynamicHeightListWidget,
    SearchableComboPopup,
    SearchableFontInstallDialog,
    SearchableComboBox,
    NoScrollComboBox
)

from app.core.desktop.logic.job_runner import JobRunnerMixin
from app.core.desktop.logic.core_handlers import HandlersMixin
from app.core.desktop.components.settings_panel import WidgetBuildersMixin

# Note: ConsoleMixin was removed.
from app.core.desktop.components.console_widget import ConsoleWidget
from app.core.desktop.logic.logger import AppLogger

from app.core.desktop.components.ui_utils import build_grouped_settings_tabs

# Dynamic configuration mapping placeholders (shared globally)
LANGUAGES = {}
TRANSLATOR_GROUPS = {}

LOG_COLORS = {}


class TranslatorStudioApp(WidgetBuildersMixin, JobRunnerMixin, ConsoleMixin, HandlersMixin, QMainWindow):

    log_signal = Signal(str, str)
    pipeline_finished_signal = Signal()
    pipeline_progress_signal = Signal(int, int, str)
    models_fetched_signal = Signal(list, object)
    fetch_finished_signal = Signal(object)
    test_finished_signal = Signal(bool, str, object)
    visual_test_finished_signal = Signal()
    visual_test_result_signal = Signal(str)

    GOOGLE_FONTS = [
        "Comic Neue",
        "Bangers",
        "Patrick Hand",
        "Architects Daughter",
        "Kaushan Script",
        "Kalam",
        "Chewy",
        "Fredoka One",
        "Schoolbell",
        "Noto Sans JP",
        "Noto Sans SC",
        "Noto Sans KR",
        "ZCOOL KuaiLe"
    ]

    def __init__(self):
        super().__init__()
        self.project_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.config_loader = ConfigLoader(self.project_base_dir)
        
        # Update LANGUAGES dynamically from the backend if loaded
        if hasattr(self.config_loader, 'languages') and self.config_loader.languages:
            global LANGUAGES
            LANGUAGES.clear()
            LANGUAGES.update(self.config_loader.languages)

        # Update TRANSLATOR_GROUPS dynamically from the custom values of offline_translator and ai_translator
        offline_info = self.config_loader.full_config_data.get('offline_translator')
        ai_info = self.config_loader.full_config_data.get('ai_translator')

        global TRANSLATOR_GROUPS, LOG_COLORS
        TRANSLATOR_GROUPS.clear()
        
        offline_list = offline_info.get('values', []) if offline_info else []
        api_list = ai_info.get('values', []) if ai_info else []
        other_list = ["original", "none"]

        TRANSLATOR_GROUPS[CAT_OFFLINE_MODELS] = offline_list
        TRANSLATOR_GROUPS[CAT_API_BASED] = api_list
        TRANSLATOR_GROUPS[CAT_OTHER_ACTIONS] = other_list


        # Update LOG_COLORS dynamically from the dynamic YAML config loader
        if hasattr(self.config_loader, 'log_colors'):
            LOG_COLORS.clear()
            LOG_COLORS.update(self.config_loader.log_colors)

        self.original_offline_translators = list(offline_list)
        self.original_ai_translators = list(api_list)

        self._load_app_state()
        self._build_font_map()
        self.setting_widgets = {}
        self.setting_rows = {}
        self.task_widgets = {}
        
        oldsession = getattr(self.config_loader, 'oldsession_config', {})
        self.task_settings = oldsession.get("task_settings", {})
        self.job_queue = oldsession.get("job_queue", [])
        self.history_queue = oldsession.get("history_queue", [])
        
        self.widget_references = {}
        self.current_settings = self.config_loader.get_factory_defaults()
        if hasattr(self.config_loader, 'oldsession_config'):
            saved_settings = self.config_loader.oldsession_config.get("current_settings", {})
            self.current_settings.update(saved_settings)
        if hasattr(self.config_loader, 'app_language'):
            self.current_settings['app_language'] = self.config_loader.app_language
        self.selected_job_id = None
        self.is_running_pipeline = False
        self._stopped_by_user = False
        self.pipeline_process = None
        self.available_themes = {}

        self.last_pan_pos = None
        self.temp_dir = os.path.join(self.project_base_dir, "temp")
        self.detected_vram_gb = 0
        def check_vram_background():
            try:
                python_exe = getattr(self, 'config_loader', None) and getattr(self.config_loader, 'python_executable', None) or sys.executable
                cmd = [python_exe, "-c", "import torch; print(torch.cuda.get_device_properties(0).total_memory if torch.cuda.is_available() else 0)"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    val = result.stdout.strip()
                    if val.isdigit():
                        mem_bytes = int(val)
                        self.detected_vram_gb = mem_bytes / (1024**3)
                        if self.detected_vram_gb > 0:
                            print(f"[INFO] Detected {self.detected_vram_gb:.2f} GB of VRAM via subprocess.")
            except Exception as e:
                print(f"[WARNING] Could not detect VRAM. Automatic mode will default to Safe. Error: {e}")
        
        threading.Thread(target=check_vram_background, daemon=True).start()

        # --- Pipeline for backend processing ---
        self.temp_dir = os.path.join(self.project_base_dir, "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        # Pipeline is instantiated lazily inside background workers to save 15s of startup time.


        self._initialize_app()
        # Connect custom signals to their slots
        self.log_signal.connect(self._insert_log_text)
        self.pipeline_finished_signal.connect(self._on_pipeline_finished)
        self.pipeline_progress_signal.connect(self._update_progress_bar)
        self.models_fetched_signal.connect(self._on_models_fetched)
        self.fetch_finished_signal.connect(self._on_fetch_finished)
        self.test_finished_signal.connect(self._on_test_finished)
        self.visual_test_finished_signal.connect(self._on_visual_test_finished)
        self.visual_test_result_signal.connect(self._display_test_result)
        # Apply saved theme if exists
        saved_theme = self.config_loader.oldsession_config.get("theme", "Default Qt")
        self._apply_theme(saved_theme)
        self._on_translator_category_changed()
        self._on_ocr_category_changed()
        self._update_inpainter_visibility()

    def _initialize_app(self):
        """
        Sets up the main window, its properties, and creates the main layout.
        """
        print("[UI] Initializing PySide6 application window...")
        self.setWindowTitle("🎌 Bimatkeo Translator - PySide")
        self.resize(1280, 720)
        self.setMinimumSize(QSize(960, 540))
        self._create_main_layout()
        
        self._update_job_list_ui()
        self._update_history_list_ui()
        print("[UI] Main layout and dynamic widgets created successfully.")

    def _create_main_layout(self):
        """Creates the main QWidget and layouts to structure the window."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        top_area_widget = QWidget()
        top_layout = QHBoxLayout(top_area_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()

        top_layout.addWidget(left_panel, stretch=1)
        top_layout.addWidget(right_panel, stretch=3)

        bottom_panel = self._create_bottom_panel()

        main_layout.addWidget(top_area_widget)
        main_layout.addWidget(bottom_panel)

    def _create_left_panel(self) -> QWidget:
        """Creates the main left panel, divided into a 'Queue' and 'History' section."""
        left_panel_container = QFrame()
        left_panel_container.setObjectName("LeftPanel")
        left_panel_layout = QVBoxLayout(left_panel_container)

        # --- 1. Top Section: Queue ---
        queue_frame = QWidget()
        queue_layout = QVBoxLayout(queue_frame)
        queue_layout.setContentsMargins(0, 0, 0, 0)

        queue_title = QLabel("Queue (Next Up)")
        font = queue_title.font()
        font.setPointSize(12)
        font.setBold(True)
        queue_title.setFont(font)
        queue_layout.addWidget(queue_title)

        self.queue_list_widget = QListWidget()
        self.queue_list_widget.setToolTip("Add folders by clicking 'Add Job' or by dragging and dropping them here.")
        self.queue_list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.queue_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.queue_list_widget.itemSelectionChanged.connect(self._on_job_selection_changed)

        self.queue_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.queue_list_widget.customContextMenuRequested.connect(self._show_queue_context_menu)
        self.queue_list_widget.itemChanged.connect(self._on_queue_item_changed)
        queue_layout.addWidget(self.queue_list_widget)

        # --- Job Control Buttons for the Queue ---
        job_controls_container = QWidget()
        job_controls_layout = QHBoxLayout(job_controls_container)
        job_controls_layout.setContentsMargins(0, 0, 0, 0)

        add_folder_btn = QPushButton("➕ Add Folder")
        add_folder_btn.clicked.connect(self._add_job)

        add_file_btn = QPushButton("📄 Add File(s)")
        add_file_btn.clicked.connect(self._add_file_job)

        remove_btn = QPushButton("🗑️ Remove Selected")
        remove_btn.clicked.connect(self._remove_selected_jobs_from_queue)

        clear_btn = QPushButton("🧹 Clear Queue")
        clear_btn.clicked.connect(self._clear_queue)

        job_controls_layout.addWidget(add_folder_btn)
        job_controls_layout.addWidget(add_file_btn)
        job_controls_layout.addWidget(remove_btn)
        job_controls_layout.addWidget(clear_btn)

        queue_layout.addWidget(job_controls_container)

        # --- 2. Bottom Section: History ---
        history_frame = QWidget()
        history_layout = QVBoxLayout(history_frame)
        history_layout.setContentsMargins(0, 0, 0, 0)

        history_title = QLabel("History (Completed Jobs)")
        history_title.setFont(font)
        history_layout.addWidget(history_title)

        self.history_list_widget = QListWidget()
        self.history_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        self.history_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_list_widget.customContextMenuRequested.connect(self._show_history_context_menu)

        history_layout.addWidget(self.history_list_widget)

        # --- History Control Buttons ---
        history_controls_container = QWidget()
        history_controls_layout = QHBoxLayout(history_controls_container)
        history_controls_layout.setContentsMargins(0, 0, 0, 0)
        history_controls_layout.addStretch()

        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.clicked.connect(self._clear_history)
        history_controls_layout.addWidget(clear_history_btn)
        history_layout.addWidget(history_controls_container)

        # --- Add all sections to the main panel layout (3 equal parts) ---
        left_panel_layout.addWidget(queue_frame, stretch=1)
        
        # --- Middle Section: Live Log ---
        log_frame = self._create_log_tab()
        # Thay đổi tiêu đề Log nếu cần (hoặc giữ nguyên widget từ hàm cũ)
        left_panel_layout.addWidget(log_frame, stretch=1)

        # --- Bottom Section: History ---
        left_panel_layout.addWidget(history_frame, stretch=1)

        self.left_panel_widget = left_panel_container
        return left_panel_container

    def _create_right_panel(self) -> QWidget:
        """Creates the right panel widget containing the main tabs."""
        self.main_tabs = QTabWidget()
        tab_config = self._create_settings_tab_container()
        tab_preview_tester = self._create_preview_tester_tab()

        self.main_tabs.addTab(tab_config, "Configuration ⚙️")
        self.main_tabs.addTab(tab_preview_tester, "Preview Tester 🔍")

        return self.main_tabs

    def _create_settings_tab_container(self) -> QWidget:
        """
        Creates the content for the 'Configuration' tab, which itself is another
        set of tabs read dynamically from the config loader.
        """
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(10)

        self.settings_tab_view = QTabWidget()
        container_layout.addWidget(self.settings_tab_view)

        self._populate_all_tabs()

        return container_widget

        # Remove old visual compare UI methods

    def _update_progress_bar(self, current: int, total: int, text: str):
        """Updates the progress bar and status label from background threads."""
        if hasattr(self, 'progress_bar') and hasattr(self, 'progress_label'):
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            self.progress_label.setText(text)

        # Removed _on_hitl_requested and _on_mtpe_approved
