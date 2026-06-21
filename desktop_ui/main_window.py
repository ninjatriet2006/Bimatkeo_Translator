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

# Core non-UI imports
from .pipeline_client import Pipeline
from .config_loader import ConfigLoader

# Import modularized components
from .mainwindow import (
    get_provider_credentials,
    DynamicHeightListWidget,
    SearchableComboPopup,
    SearchableFontInstallDialog,
    SearchableComboBox,
    NoScrollComboBox,
    WidgetBuildersMixin,
    JobRunnerMixin,
    ConsoleMixin,
    HandlersMixin
)

# Dynamic configuration mapping placeholders (shared globally)
LANGUAGES = {}
TRANSLATOR_GROUPS = {}
TRANSLATOR_CAPABILITIES = {}
LOG_COLORS = {}


class TranslatorStudioApp(QMainWindow, WidgetBuildersMixin, JobRunnerMixin, ConsoleMixin, HandlersMixin):

    log_signal = Signal(str, str)
    pipeline_finished_signal = Signal()
    models_fetched_signal = Signal(list, object)
    fetch_finished_signal = Signal(object)

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

        global TRANSLATOR_GROUPS, TRANSLATOR_CAPABILITIES, LOG_COLORS
        TRANSLATOR_GROUPS.clear()
        
        offline_list = offline_info.get('values', []) if offline_info else []
        api_list = ai_info.get('values', []) if ai_info else []
        other_list = ["original", "none"]

        TRANSLATOR_GROUPS["--- OFFLINE MODELS (No API Key) ---"] = offline_list
        TRANSLATOR_GROUPS["--- API-BASED (Requires Setup) ---"] = api_list
        TRANSLATOR_GROUPS["--- OTHER ACTIONS ---"] = other_list

        # Update TRANSLATOR_CAPABILITIES dynamically from the dynamic YAML config loader
        if hasattr(self.config_loader, 'translator_capabilities'):
            TRANSLATOR_CAPABILITIES.clear()
            TRANSLATOR_CAPABILITIES.update(self.config_loader.translator_capabilities)

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
        self.task_settings = {}
        self.widget_references = {}
        self.current_settings = self.config_loader.get_factory_defaults()
        if hasattr(self.config_loader, 'oldsession_config'):
            saved_settings = self.config_loader.oldsession_config.get("current_settings", {})
            self.current_settings.update(saved_settings)
        if hasattr(self.config_loader, 'app_language'):
            self.current_settings['app_language'] = self.config_loader.app_language
        self.job_queue = []
        self.history_queue = []
        self.selected_job_id = None
        self.is_running_pipeline = False
        self._stopped_by_user = False
        self.pipeline_process = None
        self.available_themes = {}

        # --- Variables for the Visual Compare Tab ---
        self.test_image_path = None
        self.original_pixmap_item = None
        self.translated_pixmap_item = None
        self.is_panning = False
        self.last_pan_pos = None
        self.temp_dir = os.path.join(self.project_base_dir, "temp")
        self.detected_vram_gb = 0
        try:
            python_exe = getattr(self, 'config_loader', None) and getattr(self.config_loader, 'python_executable', None) or sys.executable
            cmd = [python_exe, "-c", "import torch; print(torch.cuda.get_device_properties(0).total_memory if torch.cuda.is_available() else 0)"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                val = result.stdout.strip()
                if val.isdigit():
                    mem_bytes = int(val)
                    self.detected_vram_gb = mem_bytes / (1024**3)
                    if self.detected_vram_gb > 0:
                        print(f"[INFO] Detected {self.detected_vram_gb:.2f} GB of VRAM via subprocess.")
        except Exception as e:
            print(f"[WARNING] Could not detect VRAM. Automatic mode will default to Safe. Error: {e}")

        # --- Pipeline for backend processing ---
        temp_dir = os.path.join(self.project_base_dir, "temp")
        self.pipeline = Pipeline(self, self.config_loader.python_executable, temp_dir)

        self._initialize_app()
        # Connect custom signals to their slots
        self.log_signal.connect(self._insert_log_text)
        self.pipeline_finished_signal.connect(self._on_pipeline_finished)
        self.models_fetched_signal.connect(self._on_models_fetched)
        self.fetch_finished_signal.connect(self._on_fetch_finished)
        # Apply saved theme if exists
        saved_theme = self.config_loader.oldsession_config.get("theme", "Default Qt")
        self._apply_theme(saved_theme)
        self._on_translator_category_changed()

    def _initialize_app(self):
        """
        Sets up the main window, its properties, and creates the main layout.
        """
        print("[UI] Initializing PySide6 application window...")
        self.setWindowTitle("🎌 Bimatkeo Translator - PySide")
        self.resize(1280, 720)
        self.setMinimumSize(QSize(960, 540))
        self._create_main_layout()
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
        queue_layout.addWidget(self.queue_list_widget)

        # --- Job Control Buttons for the Queue ---
        job_controls_container = QWidget()
        job_controls_layout = QHBoxLayout(job_controls_container)
        job_controls_layout.setContentsMargins(0, 0, 0, 0)

        add_btn = QPushButton("➕ Add Job")
        add_btn.clicked.connect(self._add_job)

        remove_btn = QPushButton("🗑️ Remove Selected")
        remove_btn.clicked.connect(self._remove_selected_jobs_from_queue)

        clear_btn = QPushButton("🧹 Clear Queue")
        clear_btn.clicked.connect(self._clear_queue)

        job_controls_layout.addWidget(add_btn)
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

        # --- Add both sections to the main panel layout ---
        left_panel_layout.addWidget(queue_frame, stretch=3)
        left_panel_layout.addWidget(history_frame, stretch=2)

        self.left_panel_widget = left_panel_container
        return left_panel_container

    def _create_right_panel(self) -> QWidget:
        """Creates the right panel widget containing the main tabs."""
        self.main_tabs = QTabWidget()

        tab_config = self._create_settings_tab_container()
        tab_compare = self._create_visual_compare_tab()
        tab_log = self._create_log_tab()

        self.main_tabs.addTab(tab_config, "Configuration ⚙️")
        self.main_tabs.addTab(tab_log, "Live Log 📊")

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

        config_data = self.config_loader.full_config_data
        tab_order = self.config_loader.get_tab_order()
        grouped_settings = {tab_name: [] for tab_name in tab_order}
        for key, info in config_data.items():
            group = info.get("group", "Other")
            if group in grouped_settings:
                grouped_settings[group].append(info)

        for tab_name in tab_order:
            settings_list = sorted(grouped_settings.get(tab_name, []), key=lambda x: x.get('order', 999))
            tab_content_widget = self._build_dynamic_tab_content(tab_name, settings_list)
            self.settings_tab_view.addTab(tab_content_widget, tab_name)

        tasks_tab_content = self._build_tasks_tab_content()
        self.settings_tab_view.addTab(tasks_tab_content, "Tasks 🛠️")

        return container_widget

    def _create_visual_compare_tab(self) -> QWidget:
        """Creates the entire UI for the Visual Compare tab and connects its signals."""
        container = QWidget()
        layout = QVBoxLayout(container)

        # 1. Top Controls Panel
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)

        load_button = QPushButton("Load Test Image...")
        load_button.clicked.connect(self._load_test_image)

        self.fast_preview_check = QCheckBox("Fast Preview")
        self.fast_preview_check.setChecked(True)

        self.run_test_button = QPushButton("Run Test")
        self.run_test_button.setEnabled(False)
        self.run_test_button.clicked.connect(self._run_visual_test_thread)

        reset_button = QPushButton("Reset View")
        reset_button.clicked.connect(self._fit_image_to_view)

        self.zoom_label = QLabel("Zoom: 100%")

        self.limit_zoom_check = QCheckBox("Limit Zoom")
        self.limit_zoom_check.setChecked(True)
        self.limit_zoom_check.setToolTip("When checked, zoom is limited between 5% and 800%.")

        controls_layout.addWidget(load_button)
        controls_layout.addWidget(self.fast_preview_check)
        controls_layout.addStretch()
        controls_layout.addWidget(self.zoom_label)
        controls_layout.addWidget(reset_button)
        controls_layout.addWidget(self.run_test_button)

        # 2. Image Display Area
        image_area_frame = QFrame()
        image_area_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.image_area_layout = QHBoxLayout(image_area_frame)

        self.original_view = QGraphicsView()
        self.original_scene = QGraphicsScene()
        self.original_view.setScene(self.original_scene)
        self.original_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.original_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.translated_view = QGraphicsView()
        self.translated_scene = QGraphicsScene()
        self.translated_view.setScene(self.translated_scene)
        self.translated_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.translated_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # Connect events for zooming and synchronized panning
        self.original_view.wheelEvent = self._wheel_event_zoom
        self.translated_view.wheelEvent = self._wheel_event_zoom
        self.original_view.horizontalScrollBar().valueChanged.connect(self.translated_view.horizontalScrollBar().setValue)
        self.original_view.verticalScrollBar().valueChanged.connect(self.translated_view.verticalScrollBar().setValue)
        self.translated_view.horizontalScrollBar().valueChanged.connect(self.original_view.horizontalScrollBar().setValue)
        self.translated_view.verticalScrollBar().valueChanged.connect(self.original_view.verticalScrollBar().setValue)

        original_container = QWidget()
        original_layout = QVBoxLayout(original_container)
        original_layout.addWidget(QLabel("Original (Ctrl+Scroll=Zoom, Drag=Pan)"))
        original_layout.addWidget(self.original_view)

        translated_container = QWidget()
        translated_layout = QVBoxLayout(translated_container)
        translated_layout.addWidget(QLabel("Output"))
        translated_layout.addWidget(self.translated_view)

        self.image_area_layout.addWidget(original_container)
        self.image_area_layout.addWidget(translated_container)

        layout.addWidget(controls_frame)
        layout.addWidget(image_area_frame, stretch=1)

        return container
