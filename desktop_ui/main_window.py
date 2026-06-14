# type: ignore
# ===============================================================
# Main Application Window (PySide6 Version)
#
# Author: User & Gemini Collaboration
#
# Description: This module contains the main application class,
#              which is being rebuilt using PySide6 to create the UI.
# ===============================================================

import os
import sys
import shutil
import threading
import copy
import time
import json
import subprocess

# PySide6 imports for the main window structure and new widgets
from PySide6.QtWidgets import (
    QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QProgressBar, QTabWidget, QScrollArea,
    QComboBox, QCheckBox, QButtonGroup, QSlider, QLineEdit, QGridLayout,
    QColorDialog, QMessageBox, QListWidget, QListWidgetItem, QFileDialog,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QTextEdit,
    QApplication, QMenu, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QByteArray, QEvent, QPoint
from PySide6.QtGui import QFont, QCursor, QStandardItemModel, QFontDatabase, QPixmap, QPainter, QColor

from PIL import Image

# Helper to read credentials from environment / keys.yaml
def get_provider_credentials(provider: str) -> dict:
    import os
    import yaml
    
    # Try to load from keys.yaml first
    keys_vars = {}
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    keys_path = os.path.join(base_dir, ".config", "keys.yaml")
    if os.path.exists(keys_path):
        try:
            with open(keys_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
            if isinstance(content, dict):
                for k, v in content.items():
                    if k:
                        keys_vars[str(k)] = str(v) if v is not None else ""
        except Exception:
            pass

    def get_val(env_name, default=""):
        return keys_vars.get(env_name) or os.getenv(env_name, default)

    if provider == 'gemini':
        return {
            "endpoint": get_val("GEMINI_API_ENDPOINT", "https://generativelanguage.googleapis.com"),
            "model": get_val("GEMINI_API_MODEL", "Auto"),
            "key": get_val("GEMINI_API_KEY", "")
        }
    elif provider == 'openai':
        return {
            "endpoint": get_val("OPENAI_API_ENDPOINT", "https://api.openai.com/v1"),
            "model": get_val("OPENAI_API_MODEL", "Auto"),
            "key": get_val("OPENAI_API_KEY", "")
        }
    return {
        "endpoint": get_val(f"{provider.upper()}_API_ENDPOINT", ""),
        "model": get_val(f"{provider.upper()}_API_MODEL", "Auto"),
        "key": get_val(f"{provider.upper()}_API_KEY", "")
    }


# Core non-UI imports remain the same
from .pipeline_client import Pipeline
from .config_loader import ConfigLoader
from .constants import (
    LANGUAGES, TRANSLATOR_GROUPS, TRANSLATOR_CAPABILITIES, LOG_COLORS
)


class DynamicHeightListWidget(QListWidget):
    """
    A custom QListWidget that:
    1. Overrides its size hints to always match its content's height.
    2. Disables its own vertical scrollbar, forcing the parent to scroll.
    3. Ignores mouse wheel events to prevent accidental scrolling inside parent.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def minimumSizeHint(self) -> QSize:
        """Override to report the content's height as the minimum possible height."""
        height = self._get_content_height()
        return QSize(super().minimumSizeHint().width(), height)

    def sizeHint(self) -> QSize:
        """Override to report the content's height as the preferred height."""
        height = self._get_content_height()
        return QSize(super().sizeHint().width(), height)

    def wheelEvent(self, event: QEvent):
        """Pass the wheel event to the parent to allow scrolling the main area."""
        event.ignore()

    def _get_content_height(self) -> int:
        """Calculates the total height required to display all items without scrolling."""
        if self.count() == 0:
            return 35  # Return a default small height when empty

        # Sum of the height of each item in the list
        content_height = 0
        for i in range(self.count()):
            content_height += self.sizeHintForRow(i)

        # Add the height of the frame around the content
        content_height += self.frameWidth() * 2

        return content_height


class SearchableComboPopup(QWidget):
    def __init__(self, combo, parent=None):
        super().__init__(None, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.combo = combo
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Search Line Edit
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Search...")
        self.search_edit.textChanged.connect(self._filter_items)
        layout.addWidget(self.search_edit)
        
        # List Widget
        self.list_widget = QListWidget(self)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)
        
        self.installEventFilter(self)
        self.search_edit.installEventFilter(self)
        self.list_widget.installEventFilter(self)
        
        self._apply_popup_theme()

    def _apply_popup_theme(self):
        app = QApplication.instance()
        main_win = None
        for widget in app.topLevelWidgets():
            if isinstance(widget, QMainWindow):
                main_win = widget
                break
        
        if main_win and getattr(main_win, 'theme_colors', None):
            colors = main_win.theme_colors
            bg = colors.get("background_frame", "#2c2c2c")
            bg_input = colors.get("background_main", "#1e1e1e")
            txt = colors.get("text_main", "#dce4ee")
            border = colors.get("border", "#555555")
            accent = colors.get("accent", "#3a7ebf")
            hover = colors.get("primary_button_hover", "#444444")
        else:
            bg = "#2c2c2c"
            bg_input = "#1e1e1e"
            txt = "#dce4ee"
            border = "#555555"
            accent = "#3a7ebf"
            hover = "#444444"
            
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg};
                color: {txt};
                border: 1px solid {border};
                border-radius: 4px;
            }}
            QLineEdit {{
                background-color: {bg_input};
                color: {txt};
                border: 1px solid {border};
                padding: 4px;
                border-radius: 3px;
            }}
            QListWidget {{
                background-color: {bg};
                border: none;
            }}
            QListWidget::item {{
                padding: 5px;
                border-radius: 2px;
                background-color: transparent;
                color: {txt};
                border: none;
            }}
            QListWidget::item:hover {{
                background-color: {hover};
            }}
            QListWidget::item:selected {{
                background-color: {accent};
                color: white;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #555555;
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #888888;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)

    def populate(self):
        self._apply_popup_theme()
        self.list_widget.clear()
        self.items_data = []
        for i in range(self.combo.count()):
            text = self.combo.itemText(i)
            item_model = self.combo.model().index(i, 0)
            is_enabled = bool(self.combo.model().flags(item_model) & Qt.ItemFlag.ItemIsEnabled)
            user_data = self.combo.itemData(i)
            self.items_data.append((text, is_enabled, i, user_data))
            
        self.search_edit.blockSignals(True)
        self.search_edit.setText("")
        self.search_edit.blockSignals(False)
        self._filter_items()
        self.search_edit.setFocus()

    def _filter_items(self):
        search_text = self.search_edit.text().lower()
        self.list_widget.clear()
        
        self.current_visible_mappings = []
        selected_row = -1
        
        for text, is_enabled, orig_index, user_data in self.items_data:
            if search_text in text.lower():
                item = QListWidgetItem(text)
                if not is_enabled:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                    item.setForeground(QColor("#888888"))
                elif "(Not Setup)" in text:
                    item.setForeground(QColor("#a8a8a8"))
                    item.setToolTip("Model weights not found. Check model configs.")
                self.list_widget.addItem(item)
                self.current_visible_mappings.append(orig_index)
                
                if orig_index == self.combo.currentIndex():
                    selected_row = self.list_widget.count() - 1
                    self.list_widget.setCurrentItem(item)

        if selected_row != -1:
            self.list_widget.setCurrentRow(selected_row)
            
        self.adjust_size()

    def adjust_size(self):
        row_height = 28
        item_count = min(7, self.list_widget.count())
        if item_count == 0:
            item_count = 1
        
        list_height = item_count * row_height + 4
        total_height = 26 + 16 + list_height
        
        self.setFixedWidth(max(self.combo.width(), 200))
        self.setFixedHeight(total_height)

    def _on_item_clicked(self, item):
        row = self.list_widget.row(item)
        if 0 <= row < len(self.current_visible_mappings):
            orig_index = self.current_visible_mappings[row]
            self.combo.setCurrentIndex(orig_index)
            self.combo.activated.emit(orig_index)
            self.combo.currentIndexChanged.emit(orig_index)
            self.combo.currentTextChanged.emit(self.combo.itemText(orig_index))
            if self.combo.isEditable() and self.combo.lineEdit():
                self.combo.lineEdit().setText(self.combo.itemText(orig_index))
        self.close()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.close()
                return True
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                current_item = self.list_widget.currentItem()
                if current_item and (current_item.flags() & Qt.ItemFlag.ItemIsEnabled):
                    self._on_item_clicked(current_item)
                else:
                    self.close()
                return True
            elif event.key() == Qt.Key.Key_Down:
                if obj == self.search_edit:
                    self.list_widget.setFocus()
                    if self.list_widget.count() > 0 and self.list_widget.currentRow() == -1:
                        self.list_widget.setCurrentRow(0)
                    return True
                elif obj == self.list_widget:
                    curr_row = self.list_widget.currentRow()
                    if curr_row < self.list_widget.count() - 1:
                        self.list_widget.setCurrentRow(curr_row + 1)
                    return True
            elif event.key() == Qt.Key.Key_Up:
                if obj == self.list_widget:
                    curr_row = self.list_widget.currentRow()
                    if curr_row > 0:
                        self.list_widget.setCurrentRow(curr_row - 1)
                    else:
                        self.search_edit.setFocus()
                    return True
        elif event.type() == QEvent.Type.MouseButtonPress:
            if not self.geometry().contains(QCursor.pos()):
                self.close()
                return True
        return super().eventFilter(obj, event)


class SearchableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.popup_widget = None

    def showPopup(self):
        if not self.popup_widget:
            self.popup_widget = SearchableComboPopup(self)
        
        self.popup_widget.populate()
        
        # Position the popup
        pos = self.mapToGlobal(QPoint(0, self.height()))
        
        # Prevent going off screen
        screen = QApplication.screenAt(pos)
        if not screen:
            screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.availableGeometry()
            popup_height = self.popup_widget.height()
            if pos.y() + popup_height > screen_geom.bottom():
                # Show above
                pos = self.mapToGlobal(QPoint(0, -popup_height))
                
        self.popup_widget.move(pos)
        self.popup_widget.show()

    def hidePopup(self):
        if self.popup_widget:
            self.popup_widget.close()
        super().hidePopup()


class NoScrollComboBox(SearchableComboBox):
    """A custom QComboBox that ignores wheel events to prevent accidental scrolling."""

    def wheelEvent(self, event: QEvent):
        # Ignore the event completely, passing it to the parent widget (the scroll area)
        event.ignore()


class TranslatorStudioApp(QMainWindow):

    log_signal = Signal(str, str)
    pipeline_finished_signal = Signal()
    models_fetched_signal = Signal(list, object)
    fetch_finished_signal = Signal(object)

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

        global TRANSLATOR_GROUPS
        TRANSLATOR_GROUPS.clear()
        
        offline_list = offline_info.get('values', []) if offline_info else []
        api_list = ai_info.get('values', []) if ai_info else []
        other_list = ["original", "none"]

        TRANSLATOR_GROUPS["--- OFFLINE MODELS (No API Key) ---"] = offline_list
        TRANSLATOR_GROUPS["--- API-BASED (Requires Setup) ---"] = api_list
        TRANSLATOR_GROUPS["--- OTHER ACTIONS ---"] = other_list

        self._load_app_state()
        self._build_font_map()
        self.setting_widgets = {}
        self.setting_rows = {}
        self.task_widgets = {}
        self.task_settings = {}
        self.widget_references = {}
        self.current_settings = self.config_loader.get_factory_defaults()
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
        self.temp_dir = os.path.join(self.project_base_dir, "MangaStudio_Data", "temp")
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

        # --- Pipeline for backend processing (CORRECTED LINE) ---
        temp_dir = os.path.join(self.project_base_dir, "MangaStudio_Data", "temp")
        self.pipeline = Pipeline(self, self.config_loader.python_executable, temp_dir)

        self._initialize_app()
        # Connect custom signals to their slots
        self.log_signal.connect(self._insert_log_text)
        self.pipeline_finished_signal.connect(self._on_pipeline_finished)
        self.models_fetched_signal.connect(self._on_models_fetched)
        self.fetch_finished_signal.connect(self._on_fetch_finished)
        self._apply_theme("Default Qt")
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
        top_layout.addWidget(right_panel, stretch=3)  # Give right panel more space

        bottom_panel = self._create_bottom_panel()

        main_layout.addWidget(top_area_widget)
        main_layout.addWidget(bottom_panel)

    def _create_left_panel(self) -> QWidget:
        """Creates the main left panel, divided into a 'Queue' and 'History' section."""
        # Main container for the entire left side
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
        self.queue_list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)  # Enable drag-drop reordering
        self.queue_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)  # Allow multi-select with Ctrl/Shift
        self.queue_list_widget.itemSelectionChanged.connect(self._on_job_selection_changed)

        self.queue_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.queue_list_widget.customContextMenuRequested.connect(self._show_queue_context_menu)
        queue_layout.addWidget(self.queue_list_widget)

        # --- Job Control Buttons for the Queue ---
        job_controls_container = QWidget()
        job_controls_layout = QHBoxLayout(job_controls_container)
        job_controls_layout.setContentsMargins(0, 0, 0, 0)

        # We will replace this with a dropdown button later
        add_btn = QPushButton("➕ Add Job")
        add_btn.clicked.connect(self._add_job)

        remove_btn = QPushButton("🗑️ Remove Selected")
        # Connect this button to the working function that removes jobs
        remove_btn.clicked.connect(self._remove_selected_jobs_from_queue)

        clear_btn = QPushButton("🧹 Clear Queue")
        clear_btn.clicked.connect(self._clear_queue)

        # Add all buttons to the horizontal layout
        job_controls_layout.addWidget(add_btn)
        job_controls_layout.addWidget(remove_btn)
        job_controls_layout.addWidget(clear_btn)

        # Add the button container to the main vertical layout for the queue
        queue_layout.addWidget(job_controls_container)

        # --- 2. Bottom Section: History ---
        history_frame = QWidget()
        history_layout = QVBoxLayout(history_frame)
        history_layout.setContentsMargins(0, 0, 0, 0)

        history_title = QLabel("History (Completed Jobs)")
        history_title.setFont(font)  # Reuse the same font
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
        history_controls_layout.addStretch()  # Push button to the right

        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.clicked.connect(self._clear_history)
        history_controls_layout.addWidget(clear_history_btn)
        history_layout.addWidget(history_controls_container)

        # --- Add both sections to the main panel layout ---
        left_panel_layout.addWidget(queue_frame, stretch=3)  # Give more space to the queue
        left_panel_layout.addWidget(history_frame, stretch=2)  # Give less space to history

        self.left_panel_widget = left_panel_container
        return left_panel_container

    def _create_right_panel(self) -> QWidget:
        """Creates the right panel widget containing the main tabs."""
        self.main_tabs = QTabWidget()

        # --- CHANGED: The configuration tab is now built dynamically ---
        tab_config = self._create_settings_tab_container()
        tab_compare = self._create_visual_compare_tab()
        tab_log = self._create_log_tab()

        # Add a simple label to the other tabs for now
        compare_layout = QVBoxLayout(tab_compare)
        compare_layout.addWidget(QLabel("Visual comparison tools will be built here."))

        log_layout = QVBoxLayout(tab_log)
        log_layout.addWidget(QLabel("The live log will be displayed here."))

        self.main_tabs.addTab(tab_config, "Configuration ⚙️")
        # --- DISABLED FEATURE: The Visual Compare tab is hidden until its core bug is fixed. ---
        # TODO: The 'translated_view' panel does not correctly display the output image after
        #       the single-image pipeline finishes. The underlying logic in _run_visual_test
        #       and _display_test_result needs to be debugged.
        # self.main_tabs.addTab(tab_compare, "Visual Compare 👁️") 
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

        # --- Build the regular settings tabs from ui_map.json ---
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

        # --- NEW: Build the 'Tasks' tab ---
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
        load_button.clicked.connect(self._load_test_image)  # Connect signal

        self.fast_preview_check = QCheckBox("Fast Preview")
        self.fast_preview_check.setChecked(True)

        self.run_test_button = QPushButton("Run Test")
        self.run_test_button.setEnabled(False)
        self.run_test_button.clicked.connect(self._run_visual_test_thread)

        reset_button = QPushButton("Reset View")
        reset_button.clicked.connect(self._fit_image_to_view)  # Connect signal

        self.zoom_label = QLabel("Zoom: 100%")

        self.limit_zoom_check = QCheckBox("Limit Zoom")
        self.limit_zoom_check.setChecked(True)  # Enabled by default
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
        self.original_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)  # Enable panning!

        self.translated_view = QGraphicsView()
        self.translated_scene = QGraphicsScene()
        self.translated_view.setScene(self.translated_scene)
        self.translated_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.translated_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # --- Connect events for zooming and synchronized panning ---
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

    def _build_dynamic_tab_content(self, tab_name: str, settings_list: list) -> QWidget:
        """
        Creates a scrollable area and populates it with settings widgets,
        now with a dedicated, collapsible section for advanced settings.
        """
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # --- NEW LOGIC: Split settings into standard and advanced groups first ---
        standard_settings = []
        advanced_settings = []
        for info in settings_list:
            if info.get("section") == "advanced":
                advanced_settings.append(info)
            else:
                standard_settings.append(info)

        # --- 1. Render all standard settings ---
        for info in standard_settings:
            widget_row = self._create_setting_row(info)
            layout.addWidget(widget_row)

        # --- 2. Render the 'Advanced Settings' separator and section ---
        # Only add the separator if there are actually advanced settings for this tab
        if advanced_settings:
            # Add some vertical space before the separator
            layout.addSpacing(15)

            # Create the separator widget (Label + Line)
            separator_container = QWidget()
            separator_layout = QVBoxLayout(separator_container)
            separator_layout.setContentsMargins(0, 5, 0, 5)
            separator_layout.setSpacing(5)

            label = QLabel("<b>ADVANCED SETTINGS</b>")

            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)

            separator_layout.addWidget(label)
            separator_layout.addWidget(line)

            layout.addWidget(separator_container)

            # --- 3. Render all advanced settings ---
            for info in advanced_settings:
                widget_row = self._create_setting_row(info)
                layout.addWidget(widget_row)

        # Special handling for Extra Settings tab (Theme manager, etc.)
        if tab_name == "Extra Settings":
            vram_info_label = QLabel()
            vram_info_label.setWordWrap(True)
            vram_info_label.setStyleSheet("font-size: 9pt; color: #999;")

            if self.detected_vram_gb > 0:
                vram_text = f"Detected {self.detected_vram_gb:.2f} GB of VRAM. "
                if self.detected_vram_gb <= 6:
                    vram_text += "<b>Recommendation: 'Low VRAM' mode.</b>"
                else:
                    vram_text += "<b>Recommendation: 'High VRAM' mode.</b>"
            else:
                vram_text = "Could not detect GPU VRAM. 'Low VRAM' mode is recommended for safety."

            vram_info_label.setText(vram_text)
            layout.addWidget(vram_info_label)

            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            layout.addWidget(separator)

            font_scale_widget = self._create_font_scale_widget()
            theme_manager_widget = self._create_theme_manager_widget()
            layout.addWidget(font_scale_widget)
            layout.addWidget(theme_manager_widget)

        layout.addStretch()  # Pushes all widgets to the top
        scroll_area.setWidget(content_widget)
        return scroll_area

    def _build_tasks_tab_content(self) -> QWidget:
        """Creates the content for the 'Tasks' tab with improved layout."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # This widget is created manually and not from ui_map.json
        device_widget_container = QWidget()
        device_layout = QHBoxLayout(device_widget_container)
        device_layout.setContentsMargins(0, 0, 0, 0)
        device_layout.addWidget(QLabel("Task Processing Device:"))

        # We reuse the segmented button logic for consistency
        seg_button_container = QWidget()
        seg_button_layout = QHBoxLayout(seg_button_container)
        seg_button_layout.setContentsMargins(0, 0, 0, 0)
        seg_button_layout.setSpacing(0)

        button_group = QButtonGroup(seg_button_container)
        button_group.setExclusive(True)

        for val in ["CPU", "NVIDIA GPU"]:
            button = QPushButton(val)
            button.setCheckable(True)
            seg_button_layout.addWidget(button)
            button_group.addButton(button)
            if val == "CPU":  # Default to CPU
                button.setChecked(True)

        seg_button_container.setLayout(seg_button_layout)
        device_layout.addWidget(seg_button_container, stretch=1)

        # Store a reference to this new widget so we can read its value later
        self.tasks_processing_device_widget = seg_button_container

        layout.addWidget(device_widget_container)

        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        tasks_config = self.config_loader.tasks_config
        if not tasks_config:
            layout.addWidget(QLabel("Could not load tasks.json or it is empty."))
            content_widget.setLayout(layout)
            scroll_area.setWidget(content_widget)
            return scroll_area

        if not hasattr(self, 'task_settings'):
            self.task_settings = {}
            self.task_widgets = {}

        for task_key, task_info in tasks_config.items():
            task_frame = QFrame()
            task_frame.setObjectName("StyledPanel")
            task_frame.setFrameShape(QFrame.Shape.StyledPanel)
            task_layout = QVBoxLayout(task_frame)

            # --- Top Section: Title and Description ---
            title_label = QLabel(task_info.get("label", "Unnamed Task"))
            font = title_label.font()
            font.setPointSize(12)
            font.setBold(True)
            title_label.setFont(font)
            task_layout.addWidget(title_label)

            description_label = QLabel(task_info.get("description", ""))
            description_label.setWordWrap(True)
            task_layout.addWidget(description_label)

            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            task_layout.addWidget(separator)

            # --- Middle Section: Dynamically created settings ---
            self.task_settings.setdefault(task_key, task_info.get("defaults", {}).copy())
            self.task_widgets.setdefault(task_key, {})

            settings_keys = task_info.get("settings_keys", [])
            for setting_key in settings_keys:
                widget_info = self.config_loader.full_config_data.get(setting_key)
                if widget_info:
                    widget_row = self._create_setting_row(widget_info, task_key)
                    task_layout.addWidget(widget_row)
                else:
                    task_layout.addWidget(QLabel(f"Warning: Definition for '{setting_key}' not found."))

            task_layout.addStretch(1)  # Add stretch to push buttons to the bottom

            # --- Bottom Section: Action Buttons ---
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            button_layout.setContentsMargins(0, 0, 0, 0)

            reset_button = QPushButton("Reset to Defaults")
            reset_button.clicked.connect(lambda checked, tk=task_key: self._reset_task_settings(tk))

            # CORRECT DEFINITION ORDER
            # Define the button first, then set its text and connect the signal.
            run_button = QPushButton()
            run_button.setText(f"Assign {task_info.get('label', 'Task')}")
            run_button.clicked.connect(lambda checked, tk=task_key: self._assign_task_to_selection(tk))

            button_layout.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignLeft)
            button_layout.addStretch()  # Pushes the two buttons apart
            button_layout.addWidget(run_button, alignment=Qt.AlignmentFlag.AlignRight)

            task_layout.addWidget(button_container)
            layout.addWidget(task_frame)

        layout.addStretch(1)  # Pushes all task frames to the top
        content_widget.setLayout(layout)
        scroll_area.setWidget(content_widget)
        return scroll_area

    def _create_setting_row(self, info: dict, context_key: str = None) -> QWidget:
        """
        Creates a single row (Label + Tooltip Icon + Widget) for a setting.
        This function now handles the special 'translator_chain_builder' case separately
        to prevent duplicate labels.
        """
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)

        widget_type = info.get("widget")

        # --- SPECIAL CASE: Non-interactive Label ---
        # This widget type is for display only and doesn't follow the standard flow.
        if widget_type == "label":
            widget = QLabel(info.get("label", ""))
            if "style" in info:
                widget.setStyleSheet(info["style"])
            row_layout.addWidget(widget)
            # Store a reference so we can update it later
            if not context_key:
                self.setting_widgets[info['key']] = widget
                self.setting_rows[info['key']] = row_widget
            return row_widget # Return immediately, do not process further.

        # --- PATH 1: For the special self-contained widget ---
        if widget_type == "translator_chain_builder":
            widget = self._create_translator_chain_builder(info)
            row_layout.addWidget(widget)

            if context_key:
                self.task_widgets[context_key][info['key']] = widget
            else:
                self.setting_widgets[info['key']] = widget
                self.setting_rows[info['key']] = row_widget
                if not hasattr(self, 'widget_references'): self.widget_references = {}
                self.widget_references[info['key']] = widget

            self._connect_widget_signal(info['key'], widget, context_key)

        # --- PATH 2: For all other standard widgets ---
        else:
            label_container = QWidget()
            label_layout = QHBoxLayout(label_container)
            label_layout.setContentsMargins(0, 0, 0, 0)
            label_layout.setSpacing(5)

            label_text = info.get("label", info.get("key", "N/A"))
            main_label = QLabel(label_text)
            label_layout.addWidget(main_label)

            tooltip_text = info.get("tooltip")
            if tooltip_text:
                tooltip_icon = QLabel("(?)")
                tooltip_icon.setStyleSheet("color: #40E0D0;")
                tooltip_icon.setCursor(Qt.CursorShape.PointingHandCursor)
                default_val = info.get('default', 'N/A')
                full_tooltip = f"<b>{label_text}</b><hr>{tooltip_text}<br><i>(Default: {default_val})</i>"
                tooltip_icon.setToolTip(full_tooltip)
                label_layout.addWidget(tooltip_icon)

            label_layout.addStretch()
            row_layout.addWidget(label_container, stretch=1)

            if widget_type == "segmented_button":
                widget = self._create_segmented_button(info)
            elif widget_type in ["optionmenu", "optionmenu_languages", "optionmenu_separators"]:
                widget = self._create_combobox(info)
            elif widget_type == "checkbox":
                widget = self._create_checkbox(info)
            elif widget_type == "slider":
                widget = self._create_slider(info)
            elif widget_type == "entry":
                widget = self._create_entry(info)
            elif widget_type == "language_checkbox_grid":
                widget = self._create_language_checkbox_grid(info)
            elif widget_type == "combobox_fonts":
                widget = self._create_font_combobox(info)
            elif widget_type == "entry_with_button":
                widget = self._create_entry_with_button(info)
            elif widget_type == "api_group_selector":
                widget = self._create_api_group_selector(info)
            elif widget_type == "api_profile_selector":
                widget = self._create_api_profile_selector(info)
            elif widget_type == "ai_model_selector":
                widget = self._create_ai_model_selector(info)
            elif widget_type == "api_key_manager":
                widget = self._create_api_manager_widget(info)
            elif widget_type == "grid_segmented_button":
                widget = self._create_grid_segmented_button(info)
            elif widget_type == "preset_manager":
                widget = self._create_preset_manager(info)
            else:
                widget = QLabel(f"TODO: '{widget_type}'")
                widget.setStyleSheet("color: yellow;")

            row_layout.addWidget(widget, stretch=2)

            if context_key:
                self.task_widgets[context_key][info['key']] = widget
                initial_value = self.task_settings[context_key].get(info['key'])
            else:
                self.setting_widgets[info['key']] = widget
                self.setting_rows[info['key']] = row_widget
                initial_value = self.current_settings.get(info['key'])

            self._set_widget_value(info['key'], initial_value, widget)
            self._connect_widget_signal(info['key'], widget, context_key)

        return row_widget

    def _create_segmented_button(self, info: dict) -> QWidget:
        """Creates a group of toggleable buttons."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        button_group = QButtonGroup(container)
        button_group.setExclusive(True)  # Only one can be checked at a time

        values = info.get("values", [])
        for val in values:
            button = QPushButton(val)
            button.setCheckable(True)
            if val == info.get("default"):
                button.setChecked(True)
            layout.addWidget(button)
            button_group.addButton(button)

        return container

    def _set_combobox_value_by_data(self, combo_box, value):
        index = -1
        for i in range(combo_box.count()):
            if combo_box.itemData(i) == value:
                index = i
                break
        if index != -1:
            combo_box.setCurrentIndex(index)
        else:
            combo_box.setCurrentText(str(value))

    def _create_combobox(self, info: dict) -> QComboBox:
        """Creates a dropdown (ComboBox) widget."""
        combo_box = SearchableComboBox()
        values = info.get("values", [])
        key = info.get("key")

        # Override values for UI-only translators if needed
        if key == "offline_translator":
            values = TRANSLATOR_GROUPS.get("--- OFFLINE MODELS (No API Key) ---", values)
        elif key == "ai_translator":
            values = TRANSLATOR_GROUPS.get("--- API-BASED (Requires Setup) ---", values)

        if info.get("widget") == "optionmenu_separators" or key in ["offline_translator", "ai_translator"]:
            # If it's the main translator selectors or has separators
            if key in ["offline_translator", "ai_translator"]:
                # Simple list of choices for split dropdowns, but check setup
                for val in values:
                    exists = self.config_loader.check_model_existence(val, field=key)
                    display_name = val
                    if not exists:
                        display_name = f"{val} (Not Setup)"
                    combo_box.addItem(display_name, val)
                    if not exists:
                        last_idx = combo_box.count() - 1
                        combo_box.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            else:
                # Optionmenu with separators (e.g. from TRANSLATOR_GROUPS)
                for group_name, translators in TRANSLATOR_GROUPS.items():
                    item_index = combo_box.count()
                    combo_box.addItem(group_name)
                    combo_box.model().item(item_index).setEnabled(False)
                    field_name = "offline_translator" if "OFFLINE" in group_name else ("ai_translator" if "API" in group_name else None)
                    for t in translators:
                        exists = self.config_loader.check_model_existence(t, field=field_name)
                        display_name = t
                        if not exists:
                            display_name = f"{t} (Not Setup)"
                        combo_box.addItem(display_name, t)
                        if not exists:
                            last_idx = combo_box.count() - 1
                            combo_box.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            self._set_combobox_value_by_data(combo_box, str(info.get("default")))
        else:
            for val in values:
                exists = self.config_loader.check_model_existence(val, field=key)
                display_name = val
                if not exists:
                    display_name = f"{val} (Not Setup)"
                combo_box.addItem(display_name, val)
                if not exists:
                    last_idx = combo_box.count() - 1
                    combo_box.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            self._set_combobox_value_by_data(combo_box, str(info.get("default")))

        return combo_box

    def _create_checkbox(self, info: dict) -> QCheckBox:
        """Creates a checkbox widget."""
        # In PySide, the label is part of the checkbox, so we pass an empty string
        check_box = QCheckBox("")
        if info.get("default") is True:
            check_box.setChecked(True)
        return check_box

    def _create_slider(self, info: dict) -> QWidget:
        """Creates a container with a QSlider and a QLabel to display its value."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        slider = QSlider(Qt.Orientation.Horizontal)

        # --- FIX: Prevent focus and wheel events ---
        # This makes the slider only controllable by dragging the handle.
        slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        value_label = QLabel()
        value_label.setMinimumWidth(45)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        options = info.get("options", {})
        from_val = options.get("from_", 0)
        to_val = options.get("to", 100)

        # --- FIX: Ensure integer steps for integer-based sliders ---
        # The 'number_of_steps' key in ui_map.json can be used to control this,
        # but for now, we'll ensure the final value is rounded correctly.

        multiplier = info.get("value_multiplier", 1)
        # Use a high precision for smooth dragging
        internal_precision = 100

        slider.setMinimum(int(from_val * internal_precision))
        slider.setMaximum(int(to_val * internal_precision))

        def update_label(value):
            actual_value = (value / internal_precision) * multiplier
            value_format = info.get("value_format", "{:.0f}")

            if 'f' in value_format:
                display_value = float(actual_value)
            else:
                display_value = int(round(actual_value))

            if value_label:
                value_label.setText(value_format.format(display_value))

        slider.update_label_func = update_label
        slider.valueChanged.connect(update_label)

        default_value = info.get("default")
        initial_slider_value = 0
        if default_value is not None:
            try:
                initial_slider_value = int((float(default_value) / multiplier) * internal_precision)
            except (ValueError, TypeError):
                initial_slider_value = 0

        slider.setValue(initial_slider_value)
        update_label(initial_slider_value)

        layout.addWidget(slider)
        layout.addWidget(value_label)
        return container

    def _create_entry(self, info: dict) -> QLineEdit:
        """Creates a text input (QLineEdit) widget."""
        entry = QLineEdit()
        default_text = info.get("default", "")
        if default_text is not None:
            entry.setText(str(default_text))

        placeholder = info.get("placeholder", "")
        if placeholder:
            entry.setPlaceholderText(placeholder)

        return entry

    def _create_language_checkbox_grid(self, info: dict) -> QWidget:
        """Creates a scrollable grid of checkboxes for language selection."""
        # This widget is more complex, so it gets its own container and layout
        container = QFrame()
        container.setFrameShape(QFrame.Shape.StyledPanel)
        container_layout = QVBoxLayout(container)

        # We don't need a scroll area if the container itself can be a fixed size
        # for simplicity for now. A QScrollArea can be added later if needed.
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(5)

        checkboxes = {}
        lang_items = [lang for lang in LANGUAGES.items() if lang[1] != 'auto']

        # Create a 2-column grid of checkboxes
        for i, (name, code) in enumerate(lang_items):
            row, col = divmod(i, 2)
            check_box = QCheckBox(name)
            grid_layout.addWidget(check_box, row, col)
            checkboxes[code] = check_box

        container_layout.addWidget(grid_widget)

        # We need to store these checkboxes somewhere to get their values later.
        # Let's create a storage for them if it doesn't exist.
        if not hasattr(self, 'widget_references'):
            self.widget_references = {}
        self.widget_references[info['key']] = checkboxes

        return container

    def _create_font_combobox(self, info: dict) -> QComboBox:
        """Creates a combobox populated with system and project fonts."""
        combo_box = SearchableComboBox()
        font_list = self._get_font_list()
        combo_box.addItems(font_list)

        # Make the header items non-selectable for better UX
        for i, item_text in enumerate(font_list):
            if item_text.startswith("---"):
                combo_box.model().item(i).setEnabled(False)

        default_font = info.get("default", "Sans-serif")
        combo_box.setCurrentText(default_font)
        return combo_box

    def _create_entry_with_button(self, info: dict) -> QWidget:
        """Creates a QLineEdit with a QPushButton next to it."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        entry = QLineEdit()
        entry.setText(str(info.get("default", "")))
        layout.addWidget(entry)

        button = QPushButton(info.get("button_text", "..."))
        button.setFixedWidth(40)
        # Pass both the widget key and the associated entry field to the handler
        button.clicked.connect(lambda: self._handle_widget_button_click(info['key'], entry))
        layout.addWidget(button)

        return container

    def _create_translator_chain_builder(self, info: dict) -> QWidget:
        """
        Creates a self-contained component for the translator chain,
        including its own header with a label and control buttons.
        """
        # Main container for the whole builder
        container = QFrame()
        container.setObjectName("ChainBuilderFrame")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)

        # --- Header Row ---
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # The label is now created INSIDE the component
        label = QLabel(info.get("label", "Translation Steps:"))
        header_layout.addWidget(label)
        header_layout.addStretch()  # This pushes the buttons to the right

        # Control buttons for the list
        add_btn = QPushButton("➕ Add Step")
        remove_btn = QPushButton("➖ Remove Selected")
        header_layout.addWidget(add_btn)
        header_layout.addWidget(remove_btn)

        # Add the completed header to the main vertical layout
        container_layout.addWidget(header_widget)

        # --- List Widget ---
        self.chain_list_widget = DynamicHeightListWidget()
        self.chain_list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        container_layout.addWidget(self.chain_list_widget)

        # --- Connect signals ---
        add_btn.clicked.connect(self._add_chain_step)
        remove_btn.clicked.connect(self._remove_chain_step)

        # Store a reference for enabling/disabling the whole container
        self.widget_references[info['key']] = container

        # Initialize UI state
        QTimer.singleShot(0, self._update_chain_ui_state)

        return container

    def _create_chain_step_widget(self) -> QWidget:
        """Creates the widget for a single row/step in the translator chain."""
        step_widget = QWidget()
        layout = QHBoxLayout(step_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        translator_combo = NoScrollComboBox()
        # Populate with translators from TRANSLATOR_GROUPS constant
        for group_name, translators in TRANSLATOR_GROUPS.items():
            item_index = translator_combo.count()
            translator_combo.addItem(group_name)
            translator_combo.model().item(item_index).setEnabled(False)
            field_name = "offline_translator" if "OFFLINE" in group_name else ("ai_translator" if "API" in group_name else None)
            for t in translators:
                exists = self.config_loader.check_model_existence(t, field=field_name)
                display_name = t
                if not exists:
                    display_name = f"{t} (Not Setup)"
                translator_combo.addItem(display_name, t)
                if not exists:
                    last_idx = translator_combo.count() - 1
                    translator_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)

        lang_combo = NoScrollComboBox()
        # Populate with languages from LANGUAGES constant
        lang_combo.addItems(list(LANGUAGES.keys()))

        layout.addWidget(QLabel("Translate with:"))
        layout.addWidget(translator_combo)
        layout.addWidget(QLabel("to"))
        layout.addWidget(lang_combo)

        # Store combo boxes in the widget's properties for later access
        step_widget.translator_combo = translator_combo
        step_widget.lang_combo = lang_combo

        translator_combo.currentTextChanged.connect(
            lambda text, lc=lang_combo: self._filter_language_dropdown(text, lc)
        )
        # Trigger it once to set the initial state
        self._filter_language_dropdown(translator_combo.currentText(), lang_combo)

        handler = lambda: self._on_setting_changed('translator_chain')
        translator_combo.currentTextChanged.connect(handler)
        lang_combo.currentTextChanged.connect(handler)

        return step_widget

    def _add_chain_step(self):
        """Adds a new, empty step to the translator chain list."""
        step_widget = self._create_chain_step_widget()

        list_item = QListWidgetItem(self.chain_list_widget)
        list_item.setSizeHint(step_widget.sizeHint())

        self.chain_list_widget.addItem(list_item)
        self.chain_list_widget.setItemWidget(list_item, step_widget)
        self._on_setting_changed('translator_chain')  # Notify that settings have changed
        self.chain_list_widget.updateGeometry()

    def _remove_chain_step(self):
        """Removes the currently selected step from the chain list."""
        selected_items = self.chain_list_widget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            row = self.chain_list_widget.row(item)
            self.chain_list_widget.takeItem(row)
        self._on_setting_changed('translator_chain')
        self.chain_list_widget.updateGeometry()

    def _get_translator_chain_string(self) -> str:
        """
        Reads all steps from the chain_list_widget and builds the
        backend-compatible string (e.g., 'sugoi:ENG;deepl:TRK').
        """
        if not hasattr(self, 'chain_list_widget'):
            return ""

        steps = []
        for i in range(self.chain_list_widget.count()):
            item = self.chain_list_widget.item(i)
            widget = self.chain_list_widget.itemWidget(item)

            if widget and hasattr(widget, 'translator_combo') and hasattr(widget, 'lang_combo'):
                translator_name = widget.translator_combo.currentData()
                if not translator_name:
                    translator_name = widget.translator_combo.currentText()
                lang_name = widget.lang_combo.currentText()

                # Make sure the selected item is not a separator/header
                if translator_name not in TRANSLATOR_GROUPS:
                    lang_code = LANGUAGES.get(lang_name, '')
                    if lang_code:
                        steps.append(f"{translator_name}:{lang_code}")

        return ";".join(steps)

    def _rebuild_chain_from_string(self, chain_string: str):
        """Clears and rebuilds the translator chain UI from a saved string."""
        self.chain_list_widget.clear()
        if not chain_string:
            return

        steps = chain_string.split(';')
        code_to_lang_name = {v: k for k, v in LANGUAGES.items()}

        for step in steps:
            parts = step.split(':')
            if len(parts) == 2:
                translator_name, lang_code = parts

                # Add a new visual step to the list
                step_widget = self._create_chain_step_widget()
                list_item = QListWidgetItem(self.chain_list_widget)
                list_item.setSizeHint(step_widget.sizeHint())
                self.chain_list_widget.addItem(list_item)
                self.chain_list_widget.setItemWidget(list_item, step_widget)

                # Set the combobox values based on the loaded data
                self._set_combobox_value_by_data(step_widget.translator_combo, translator_name)
                lang_name = code_to_lang_name.get(lang_code, "")
                if lang_name:
                    step_widget.lang_combo.setCurrentText(lang_name)

        self.chain_list_widget.updateGeometry()

    def _create_grid_segmented_button(self, info: dict) -> QWidget:
        """Creates a grid of toggleable buttons that can wrap to multiple lines."""
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        button_group = QButtonGroup(container)
        button_group.setExclusive(True)

        values = info.get("values", [])
        columns = info.get("options", {}).get("columns", 4)  # Default to 4 columns

        row, col = 0, 0
        for val in values:
            button = QPushButton(val)
            button.setCheckable(True)
            if val == info.get("default"):
                button.setChecked(True)

            layout.addWidget(button, row, col)
            button_group.addButton(button)

            col += 1
            if col >= columns:
                col = 0
                row += 1

        return container

    def _create_preset_manager(self, info: dict) -> QWidget:
        """Creates the preset management compound widget."""
        preset_frame = QFrame()
        preset_frame.setObjectName("StyledPanel")
        preset_frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(preset_frame)

        self.profile_combobox = SearchableComboBox()
        layout.addWidget(self.profile_combobox)

        self.profile_name_entry = QLineEdit()
        self.profile_name_entry.setPlaceholderText("Enter new preset name")
        layout.addWidget(self.profile_name_entry)

        # When a profile is selected from the dropdown, copy its name to the entry field
        self.profile_combobox.currentTextChanged.connect(self.profile_name_entry.setText)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)

        save_btn = QPushButton("Save")
        load_btn = QPushButton("Load")
        delete_btn = QPushButton("Delete")

        button_layout.addWidget(save_btn)
        button_layout.addWidget(load_btn)
        button_layout.addWidget(delete_btn)
        layout.addWidget(button_container)

        # Connect buttons to their handler methods
        save_btn.clicked.connect(self._save_profile)
        load_btn.clicked.connect(self._load_profile)
        delete_btn.clicked.connect(self._delete_profile)

        self._refresh_profile_list()  # Initial population of the combobox
        return preset_frame

    def _get_font_list(self) -> list:
        """Gets a combined list of project and system fonts."""
        project_fonts = []
        fonts_dir = os.path.join(self.project_base_dir, "fonts")
        if os.path.isdir(fonts_dir):
            project_fonts = sorted([f for f in os.listdir(fonts_dir) if f.lower().endswith(('.ttf', '.otf'))])

        # Use QFontDatabase for a reliable way to get system fonts
        system_fonts = sorted(QFontDatabase().families())

        final_list = []
        if project_fonts:
            final_list.extend(project_fonts)
        final_list.extend(system_fonts)
        return final_list

    def _update_chain_ui_state(self):
        """
        Enables or disables the translator chain builder and the main translator dropdowns
        based on the 'Enable Translator Chain' checkbox.
        """
        enable_checkbox = self.setting_widgets.get('enable_translator_chain')
        chain_container = self.widget_references.get('translator_chain')
        category_widget = self.setting_widgets.get('translator_category')
        offline_combo = self.setting_widgets.get('offline_translator')
        ai_combo = self.setting_widgets.get('ai_translator')
        ai_endpoint = self.setting_widgets.get('ai_endpoint')
        ai_model_widget = self.setting_widgets.get('ai_model')
        ai_key = self.setting_widgets.get('ai_key')
        main_language_combo = self.setting_widgets.get('target_lang')

        if not all([enable_checkbox, chain_container, main_language_combo]):
            return

        is_chain_enabled = enable_checkbox.isChecked()

        # Enable/disable the builder and its contents
        chain_container.setEnabled(is_chain_enabled)

        # Enable/disable the main dropdowns (opposite logic)
        main_language_combo.setEnabled(not is_chain_enabled)
        
        for w in [category_widget, offline_combo, ai_combo, ai_endpoint, ai_model_widget, ai_key]:
            if w:
                w.setEnabled(not is_chain_enabled)

        # If disabled is False (meaning main settings are active), update visibility based on category
        if not is_chain_enabled:
            self._update_translator_visibility()

        # If the chain is disabled, clear its contents
        if not is_chain_enabled:
            self.chain_list_widget.clear()
            self.chain_list_widget.updateGeometry()

        self._on_setting_changed('translator_chain')

    def _update_chain_list_height(self):
        """Calculates and sets the minimum height of the chain list widget to fit all its items."""
        if not hasattr(self, 'chain_list_widget'):
            return

        # Calculate the total height of all item widgets
        content_height = 0
        for i in range(self.chain_list_widget.count()):
            # Using sizeHintForRow is more accurate than getting the widget's hint directly
            content_height += self.chain_list_widget.sizeHintForRow(i)

        # Add spacing between items to the calculation
        if self.chain_list_widget.count() > 1:
            content_height += self.chain_list_widget.spacing() * (self.chain_list_widget.count() - 1)

        # Ensure the widget doesn't collapse completely when empty
        if content_height == 0:
            content_height = 40  # A sensible default height for an empty list

        # Force the layout to give the list at least this much vertical space
        self.chain_list_widget.setMinimumHeight(content_height)

    def _update_translator_tooltip(self, translator_name: str):
        """Updates the tooltip of the translator combobox to show its capabilities."""
        category = self._get_active_translator_category()
        key = 'offline_translator' if category == 'Offline' else 'ai_translator'
        translator_combo = self.setting_widgets.get(key)
        if not translator_combo:
            return

        capabilities = TRANSLATOR_CAPABILITIES.get(translator_name, {})

        # Reverse the LANGUAGES dict for easy code-to-name lookup
        code_to_name = {v: k for k, v in LANGUAGES.items()}

        tooltip_html = f"<b>{translator_name} Capabilities:</b><hr>"

        if not capabilities:
            tooltip_html += "No translation is performed."
        elif capabilities.get('__any__') == '__all__':
            tooltip_html += "Supports translation between most languages."
        else:
            lines = []
            for source_code, target_codes in capabilities.items():
                source_name = code_to_name.get(source_code, source_code)
                target_names = [code_to_name.get(tc, tc) for tc in target_codes]
                lines.append(f"<b>From {source_name}:</b><br>  → {', '.join(target_names)}")
            tooltip_html += "<br>".join(lines)

        translator_combo.setToolTip(tooltip_html)

    def _handle_widget_button_click(self, key: str, associated_widget: QWidget):
        """Handles clicks for buttons that are part of a widget row."""
        if key == "font_color":
            current_color = associated_widget.text()
            if not current_color: current_color = "000000"
            color = QColorDialog.getColor(initial=f"#{current_color}", title="Choose Font Color")
            if color.isValid():
                new_color_hex = color.name()[1:]
                associated_widget.setText(new_color_hex)
                self._on_setting_changed(key)
        
        elif key == "gpt_config":
            configs_dir = os.path.join(self.project_base_dir, "MangaStudio_Data", "gpt_configs")
            os.makedirs(configs_dir, exist_ok=True)
            config_path, _ = QFileDialog.getOpenFileName(self, "Select GPT Config File", configs_dir, "YAML Files (*.yaml *.yml);;All Files (*)")
            if config_path:
                file_name = os.path.basename(config_path)
                associated_widget.setText(file_name)
                self._on_setting_changed(key)
        
        elif key in ["pre_dict_path", "post_dict_path"]:
            # --- NEW DICTIONARY LOGIC ---
            dicts_dir = os.path.join(self.project_base_dir, "MangaStudio_Data", "dicts")
            os.makedirs(dicts_dir, exist_ok=True)
            
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Select Dictionary File", 
                dicts_dir, 
                "Text Files (*.txt);;All Files (*)"
            )
            
            if file_path:
                # We only want the relative path from the project base directory
                relative_path = os.path.relpath(file_path, self.project_base_dir)
                associated_widget.setText(relative_path.replace("\\", "/")) # Use forward slashes for consistency
                self._on_setting_changed(key)

        elif key == "ai_model":
            button = associated_widget.parent().findChild(QPushButton)
            if button:
                self._fetch_ai_models(button)

    def _get_active_translator_category(self) -> str:
        """Returns 'Offline' or 'AI / Online'."""
        widget = self.setting_widgets.get('translator_category')
        if not widget:
            return 'Offline'
        val = self._get_value_from_widget('translator_category', widget)
        return val or 'Offline'

    def _get_active_translator_name(self) -> str:
        """Returns the active translator name (e.g. sugoi, gemini, etc.)"""
        category = self._get_active_translator_category()
        key = 'offline_translator' if category == 'Offline' else 'ai_translator'
        widget = self.setting_widgets.get(key)
        if not widget:
            return 'none'
        return self._get_value_from_widget(key, widget) or 'none'

    def _update_translator_visibility(self):
        """Toggles the visibility of translator settings based on Offline vs AI category with cascade hierarchy."""
        selected_category = self._get_active_translator_category()
        
        show_offline = (selected_category == "Offline")
        show_ai = (selected_category == "AI / Online")

        # Toggle rows visibility
        if 'offline_translator' in self.setting_rows:
            self.setting_rows['offline_translator'].setVisible(show_offline)
        
        # Determine visibility in AI / Online mode based on cascade dependency
        group_val = ""
        group_widget = self.setting_widgets.get('api_group')
        if group_widget:
            group_combo = group_widget.findChild(QComboBox)
            if group_combo:
                group_val = group_combo.currentText().strip()
                
        is_group_selected = show_ai and group_val != "" and group_val.lower() != "none"
        
        name_val = ""
        name_widget = self.setting_widgets.get('api_name')
        if name_widget:
            name_combo = name_widget.findChild(QComboBox)
            if name_combo:
                name_val = name_combo.currentText().strip()
                
        is_name_selected = is_group_selected and name_val != "" and name_val.lower() != "none"

        # Apply cascade visibility
        if 'api_group' in self.setting_rows:
            self.setting_rows['api_group'].setVisible(show_ai)
            
        if 'api_name' in self.setting_rows:
            self.setting_rows['api_name'].setVisible(is_group_selected)
            
        for ai_key in ['ai_translator', 'ai_endpoint', 'ai_model', 'ai_key']:
            if ai_key in self.setting_rows:
                self.setting_rows[ai_key].setVisible(is_name_selected)

    def _on_translator_category_changed(self):
        """Handles changes in translator category (Offline vs AI)."""
        self._update_translator_visibility()
        # Trigger updates for the newly active translator
        active_name = self._get_active_translator_name()
        self._on_translator_changed(active_name)

    def _sync_ai_credentials(self, ai_provider: str):
        """Auto-populates Endpoint, Model, and Key fields when changing AI provider."""
        if getattr(self, '_loading_api_profile', False):
            return
        import os
        from dotenv import load_dotenv
        # Reload .env in case the user edited it
        load_dotenv(os.path.join(self.project_base_dir, ".env"))

        info = get_provider_credentials(ai_provider)

        # Set values to the widgets
        for field, key in [('endpoint', 'ai_endpoint'), ('model', 'ai_model'), ('key', 'ai_key')]:
            widget = self.setting_widgets.get(key)
            if widget:
                self.current_settings[key] = info[field]
                self._set_widget_value(key, info[field], widget)

    def _fetch_ai_models(self, button):
        """Fetches models from the configured endpoint in a background thread."""
        endpoint = self._get_value_from_widget('ai_endpoint', self.setting_widgets.get('ai_endpoint'))
        key = self._get_value_from_widget('ai_key', self.setting_widgets.get('ai_key'))
        ai_provider = self._get_active_translator_name()

        # Fallback default endpoints if the user cleared the text box
        if not endpoint:
            provider_endpoints = {
                'openai': 'https://api.openai.com/v1',
                'deepseek': 'https://api.deepseek.com',
                'groq': 'https://api.groq.com/openai/v1',
                'custom_openai': 'http://localhost:11434/v1',
                'sakura': 'http://127.0.0.1:8080/v1'
            }
            endpoint = provider_endpoints.get(ai_provider, '')

        if not endpoint and ai_provider != 'gemini':
            self.log("WARNING", f"No API Endpoint URL provided for provider '{ai_provider}'. Please enter a valid URL.")
            return

        button.setEnabled(False)
        button.setText("...")

        def thread_target():
            import urllib.request
            import urllib.error
            import json
            import ssl

            models = []
            
            # Helper to check if a model name should be filtered out
            def is_blacklisted(model_name):
                name_lower = model_name.lower()
                blacklist_keywords = [
                    "embedding", "tts", "whisper", "dall-e", "moderation", 
                    "classifier", "aqa", "sib", "babbage", "davinci", "ada"
                ]
                for kw in blacklist_keywords:
                    if kw in name_lower:
                        return True
                return False

            try:
                # Bypass SSL verification if needed (for local self-signed dev certs)
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                if ai_provider == 'gemini':
                    base_url = endpoint.rstrip('/') if endpoint else "https://generativelanguage.googleapis.com/v1beta"
                    url = f"{base_url}/models?key={key}"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                        res_data = json.loads(response.read().decode('utf-8'))
                        gemini_models = []
                        for m in res_data.get('models', []):
                            m_name = m.get('name', '')
                            if m_name.startswith('models/'):
                                m_name = m_name.replace('models/', '')
                            if is_blacklisted(m_name):
                                continue
                            input_limit = m.get('inputTokenLimit', 0)
                            gemini_models.append((m_name, input_limit))
                        
                        # Sort by inputTokenLimit descending, then by name ascending
                        gemini_models.sort(key=lambda x: (-x[1], x[0]))
                        models = [x[0] for x in gemini_models]
                else:
                    base_url = endpoint.rstrip('/')
                    url = base_url + '/models'
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0',
                        'Content-Type': 'application/json'
                    }
                    if key:
                        headers['Authorization'] = f"Bearer {key}"
                    
                    req = urllib.request.Request(url, headers=headers)
                    raw_models = []
                    try:
                        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                            res_data = json.loads(response.read().decode('utf-8'))
                            # Check standard OpenAI response format: {"data": [{"id": "model-id"}]}
                            if 'data' in res_data and isinstance(res_data['data'], list):
                                for item in res_data['data']:
                                    if 'id' in item:
                                        raw_models.append(item['id'])
                            # Ollama /api/tags fallback (if the user gave the Ollama base port 11434 directly)
                            elif 'models' in res_data and isinstance(res_data['models'], list):
                                for item in res_data['models']:
                                    if 'name' in item:
                                        raw_models.append(item['name'])
                    except urllib.error.HTTPError as e:
                        # Fallback for Ollama /api/tags if /v1/models fails
                        if '11434' in base_url or 'ollama' in base_url.lower():
                            ollama_url = base_url.replace('/v1', '') + '/api/tags'
                            req = urllib.request.Request(ollama_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                                res_data = json.loads(response.read().decode('utf-8'))
                                for item in res_data.get('models', []):
                                    if 'name' in item:
                                        raw_models.append(item['name'])
                        else:
                            raise e

                    # Filter blacklist
                    filtered_models = [m for m in raw_models if not is_blacklisted(m)]
                    
                    # Sort heuristics for OpenAI/groq/deepseek models: prioritize newer models
                    def priority_sort_key(m_name):
                        m_lower = m_name.lower()
                        # Prioritize gpt-4o, o1, o3, deepseek-chat, mixtral, llama3
                        if any(x in m_lower for x in ["gpt-4o", "o1", "o3", "deepseek-chat", "mixtral", "llama3"]):
                            priority = -10
                        elif any(x in m_lower for x in ["gpt-4", "deepseek", "llama"]):
                            priority = -5
                        elif "gpt-3.5" in m_lower:
                            priority = 0
                        else:
                            priority = 5
                        return (priority, m_lower)

                    filtered_models = sorted(list(set(filtered_models)), key=priority_sort_key)
                    models = filtered_models

                if not models:
                    raise Exception("No suitable model IDs found in response.")

                self.models_fetched_signal.emit(models, button)
            except Exception as e:
                err_msg = str(e)
                print(f"[ERROR] Failed to fetch models: {err_msg}")
                self.log("ERROR", f"Failed to fetch models: {err_msg}")
            finally:
                self.fetch_finished_signal.emit(button)

        import threading
        threading.Thread(target=thread_target, daemon=True).start()

    def _show_fetched_models(self, models, button):
        if not models:
            return
            
        model_widget = self.setting_widgets.get('ai_model')
        if model_widget:
            combo = model_widget.findChild(QComboBox)
            if combo:
                current_text = combo.currentText()
                combo.blockSignals(True)
                combo.clear()
                
                # Prepend "Auto"
                combo.addItem("Auto")
                combo.addItems(models)
                
                # Restore current selection, defaulting to "Auto"
                if current_text and (current_text in models or current_text == "Auto"):
                    combo.setCurrentText(current_text)
                else:
                    combo.setCurrentText("Auto")
                    self.current_settings['ai_model'] = "Auto"
                    
                combo.blockSignals(False)
                self._on_setting_changed('ai_model')
                combo.showPopup()

    def _select_fetched_model(self, model_name, entry_widget):
        entry_widget.setText(model_name)
        self._on_setting_changed('ai_model')

    def _on_models_fetched(self, models, button):
        self._show_fetched_models(models, button)

    def _on_fetch_finished(self, button):
        button.setEnabled(True)
        button.setText("Fetch")

    def _get_api_profiles_file_path(self) -> str:
        base_dir = os.path.join(self.project_base_dir, '.config')
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, 'api_profiles.json')

    def _load_api_profiles(self) -> dict:
        path = self._get_api_profiles_file_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load API profiles: {e}")
        
        from dotenv import load_dotenv
        load_dotenv(os.path.join(self.project_base_dir, ".env"))

        gemini_creds = get_provider_credentials('gemini')
        openai_creds = get_provider_credentials('openai')

        return {
            "Default (Gemini)": {
                "group": "Default",
                "provider": "gemini",
                **gemini_creds
            },
            "Default (OpenAI)": {
                "group": "Default",
                "provider": "openai",
                **openai_creds
            }
        }

    def _save_api_profiles(self, profiles: dict):
        path = self._get_api_profiles_file_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=4)
        except Exception as e:
            print(f"[ERROR] Failed to save API profiles: {e}")

    def _create_api_group_selector(self, info: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        combo = SearchableComboBox()
        combo.setEditable(True)
        
        profiles = self._load_api_profiles()
        groups = sorted(list(set(p.get("group", "") for p in profiles.values())))
        groups = [g for g in groups if g]
        
        combo.addItem("")
        combo.addItems(groups)
        default_val = self.current_settings.get('api_group', info.get("default", ""))
        combo.setCurrentText(str(default_val))
        layout.addWidget(combo, stretch=1)
        
        # Delete button
        del_btn = QPushButton("Del")
        del_btn.setFixedWidth(40)
        del_btn.setToolTip("Delete this group and all its profiles")
        del_btn.clicked.connect(self._delete_current_api_group)
        layout.addWidget(del_btn)
        
        self.widget_references[info['key']] = combo
        return container

    def _create_api_profile_selector(self, info: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        combo = SearchableComboBox()
        combo.setEditable(True)
        profiles = self._load_api_profiles()
        current_group = self.current_settings.get('api_group', '')
        filtered_profiles = []
        if current_group and current_group.strip():
            filtered_profiles = [name for name, p in profiles.items() if p.get("group", "") == current_group]
            
        combo.addItem("")
        combo.addItems(filtered_profiles)
        
        # Set default value
        default_val = self.current_settings.get('api_name', info.get("default", ""))
        combo.setCurrentText(str(default_val))
            
        layout.addWidget(combo, stretch=1)
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.setFixedWidth(50)
        save_btn.setToolTip("Save this profile to local config")
        save_btn.clicked.connect(self._save_current_api_profile)
        layout.addWidget(save_btn)
        
        # Delete button
        del_btn = QPushButton("Del")
        del_btn.setFixedWidth(40)
        del_btn.setToolTip("Delete this profile from local config")
        del_btn.clicked.connect(self._delete_current_api_profile)
        layout.addWidget(del_btn)
        
        self.widget_references[info['key']] = combo
        return container

    def _create_ai_model_selector(self, info: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        combo = SearchableComboBox()
        combo.setEditable(True)
        
        combo.addItem("Auto")
        
        default_val = info.get("default", "")
        if default_val and default_val != "Auto":
            combo.addItem(str(default_val))
            combo.setCurrentText(str(default_val))
        else:
            combo.setCurrentText("Auto")
            
        layout.addWidget(combo, stretch=1)
        
        fetch_btn = QPushButton(info.get("button_text", "Fetch"))
        fetch_btn.setFixedWidth(50)
        fetch_btn.clicked.connect(lambda: self._fetch_ai_models(fetch_btn))
        layout.addWidget(fetch_btn)
        
        self.widget_references[info['key']] = combo
        return container

    def _save_current_api_profile(self):
        name_widget = self.setting_widgets.get('api_name')
        if not name_widget:
            return
        combo = name_widget.findChild(QComboBox)
        if not combo:
            return
        profile_name = combo.currentText().strip()
        if not profile_name:
            self.log("WARNING", "Please enter an API Profile Name before saving.")
            return

        group = self._get_value_from_widget('api_group', self.setting_widgets.get('api_group')) or 'Default'
        provider = self._get_value_from_widget('ai_translator', self.setting_widgets.get('ai_translator')) or 'gemini'
        endpoint = self._get_value_from_widget('ai_endpoint', self.setting_widgets.get('ai_endpoint')) or ''
        model = self._get_value_from_widget('ai_model', self.setting_widgets.get('ai_model')) or ''
        key = self._get_value_from_widget('ai_key', self.setting_widgets.get('ai_key')) or ''

        profiles = self._load_api_profiles()
        profiles[profile_name] = {
            "group": group,
            "provider": provider,
            "endpoint": endpoint,
            "model": model,
            "key": key
        }
        self._save_api_profiles(profiles)

        # Refresh group combobox items
        group_widget = self.setting_widgets.get('api_group')
        if group_widget:
            group_combo = group_widget.findChild(QComboBox)
            if group_combo:
                all_groups = sorted(list(set(p.get("group", "Default") for p in profiles.values())))
                if not all_groups:
                    all_groups = ["Default"]
                group_combo.blockSignals(True)
                group_combo.clear()
                group_combo.addItems(all_groups)
                group_combo.setCurrentText(group)
                group_combo.blockSignals(False)

        # Refresh name combobox items filtered by current group
        filtered_profiles = [name for name, p in profiles.items() if p.get("group", "Default") == group]
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(filtered_profiles)
        combo.setCurrentText(profile_name)
        combo.blockSignals(False)

        self.log("SUCCESS", f"API Profile '{profile_name}' saved to local config.")

    def _delete_current_api_group(self):
        group_widget = self.setting_widgets.get('api_group')
        if not group_widget:
            return
        group_combo = group_widget.findChild(QComboBox)
        if not group_combo:
            return
        group_name = group_combo.currentText().strip()
        if not group_name:
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận xóa nhóm API",
            f"Bạn có chắc chắn muốn xóa nhóm API '{group_name}'?\nHành động này cũng sẽ xóa toàn bộ các hồ sơ API nằm trong nhóm này!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        profiles = self._load_api_profiles()
        to_delete = [name for name, profile in profiles.items() if profile.get("group") == group_name]
        for name in to_delete:
            del profiles[name]
        
        self._save_api_profiles(profiles)
        self.log("SUCCESS", f"Đã xóa nhóm API '{group_name}' và {len(to_delete)} hồ sơ liên quan.")

        # Re-populate groups list
        all_groups = sorted(list(set(p.get("group", "Default") for p in profiles.values())))
        if not all_groups:
            all_groups = ["Default"]
        fallback_group = all_groups[0]

        group_combo.blockSignals(True)
        group_combo.clear()
        group_combo.addItems(all_groups)
        group_combo.setCurrentText(fallback_group)
        group_combo.blockSignals(False)

        self._on_api_group_changed(fallback_group)

    def _delete_current_api_profile(self):
        name_widget = self.setting_widgets.get('api_name')
        if not name_widget:
            return
        combo = name_widget.findChild(QComboBox)
        if not combo:
            return
        profile_name = combo.currentText().strip()
        if not profile_name:
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận xóa hồ sơ API",
            f"Bạn có chắc chắn muốn xóa hồ sơ API '{profile_name}' không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        profiles = self._load_api_profiles()
        if profile_name in profiles:
            del profiles[profile_name]
            self._save_api_profiles(profiles)
            self.log("SUCCESS", f"Đã xóa hồ sơ API '{profile_name}'.")

            # Get current group to filter profiles
            group = self._get_value_from_widget('api_group', self.setting_widgets.get('api_group')) or 'Default'
            filtered_profiles = [name for name, p in profiles.items() if p.get("group", "Default") == group]

            combo.blockSignals(True)
            combo.clear()
            if filtered_profiles:
                combo.addItems(filtered_profiles)
                fallback_name = filtered_profiles[0]
                combo.setCurrentText(fallback_name)
                combo.blockSignals(False)
                self._on_api_profile_changed(fallback_name)
            else:
                combo.setCurrentText("")
                combo.blockSignals(False)
                self.current_settings['api_name'] = ""
                for field, key in [('provider', 'ai_translator'), ('endpoint', 'ai_endpoint'), ('model', 'ai_model'), ('key', 'ai_key')]:
                    widget = self.setting_widgets.get(key)
                    if widget:
                        self.current_settings[key] = ""
                        self._set_widget_value(key, "", widget)
        else:
            self.log("WARNING", f"Không tìm thấy hồ sơ '{profile_name}' trong cấu hình.")

    def _on_api_group_changed(self, group_name: str):
        group_name = (group_name or "").strip()
        
        name_widget = self.setting_widgets.get('api_name')
        if not name_widget:
            return
        combo = name_widget.findChild(QComboBox)
        if not combo:
            return
            
        if not group_name or group_name.lower() == "none":
            combo.blockSignals(True)
            combo.clear()
            combo.setCurrentText("")
            combo.blockSignals(False)
            
            self.current_settings['api_name'] = ""
            for field, key in [('provider', 'ai_translator'), ('endpoint', 'ai_endpoint'), ('model', 'ai_model'), ('key', 'ai_key')]:
                widget = self.setting_widgets.get(key)
                if widget:
                    self.current_settings[key] = ""
                    self._set_widget_value(key, "", widget)
            self._update_translator_visibility()
            return
        
        profiles = self._load_api_profiles()
        filtered_profiles = [name for name, profile in profiles.items() if profile.get("group") == group_name]
        
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("")
        if filtered_profiles:
            combo.addItems(filtered_profiles)
        combo.setCurrentText("")
        combo.blockSignals(False)
        
        self.current_settings['api_name'] = ""
        for field, key in [('provider', 'ai_translator'), ('endpoint', 'ai_endpoint'), ('model', 'ai_model'), ('key', 'ai_key')]:
            widget = self.setting_widgets.get(key)
            if widget:
                self.current_settings[key] = ""
                self._set_widget_value(key, "", widget)
                
        self._update_translator_visibility()

    def _on_api_profile_changed(self, profile_name: str):
        profile_name = (profile_name or "").strip()
        
        if not profile_name or profile_name.lower() == "none":
            self.current_settings['api_name'] = ""
            for field, key in [('provider', 'ai_translator'), ('endpoint', 'ai_endpoint'), ('model', 'ai_model'), ('key', 'ai_key')]:
                widget = self.setting_widgets.get(key)
                if widget:
                    self.current_settings[key] = ""
                    self._set_widget_value(key, "", widget)
            self._update_translator_visibility()
            return
            
        profiles = self._load_api_profiles()
        if profile_name in profiles:
            profile = profiles[profile_name]
            
            self._loading_api_profile = True
            try:
                # Populate widgets
                for field, key in [('group', 'api_group'), ('provider', 'ai_translator'), ('endpoint', 'ai_endpoint'), ('model', 'ai_model'), ('key', 'ai_key')]:
                    widget = self.setting_widgets.get(key)
                    if widget:
                        val = profile.get(field, '')
                        self.current_settings[key] = val
                        self._set_widget_value(key, val, widget)
            finally:
                self._loading_api_profile = False
        else:
            # New typed name - clear details for manual entry
            self.current_settings['api_name'] = profile_name
            for field, key in [('provider', 'ai_translator'), ('endpoint', 'ai_endpoint'), ('model', 'ai_model'), ('key', 'ai_key')]:
                widget = self.setting_widgets.get(key)
                if widget:
                    self.current_settings[key] = ""
                    self._set_widget_value(key, "", widget)
            
        # Make sure we update the translator category visibility
        self._update_translator_visibility()

    def _refresh_profile_list(self):
        """Reloads the list of profiles from the directory and updates the combobox."""
        profiles_dir = os.path.join(self.project_base_dir, "MangaStudio_Data", "profiles")
        os.makedirs(profiles_dir, exist_ok=True)
        try:
            profiles = sorted([f.replace(".json", "") for f in os.listdir(profiles_dir) if f.endswith(".json")])
            self.profile_combobox.clear()
            if profiles:
                self.profile_combobox.addItems(profiles)
            else:
                self.profile_combobox.addItem("No profiles found")
        except Exception as e:
            print(f"[ERROR] Failed to refresh profiles: {e}")

    def _save_profile(self):
        """Saves the current settings dictionary as a profile."""
        name = self.profile_name_entry.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Please enter a profile name.")
            return

        profiles_dir = os.path.join(self.project_base_dir, "MangaStudio_Data", "profiles")
        path = os.path.join(profiles_dir, f"{name}.json")

        if os.path.exists(path):
            reply = QMessageBox.question(self, "Confirm Overwrite", f"Profile '{name}' already exists. Overwrite it?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                # Save the current_settings dictionary to the JSON file
                import json
                json.dump(self.current_settings, f, indent=4)

            self._refresh_profile_list()
            self.profile_combobox.setCurrentText(name)
            print(f"Profile '{name}' saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save profile: {e}")

    def _load_profile(self):
        """Loads a profile and applies its settings, ensuring the UI remains enabled."""
        name = self.profile_combobox.currentText()
        if not name or name == "No profiles found":
            return

        path = os.path.join(self.project_base_dir, "MangaStudio_Data", "profiles", f"{name}.json")
        if not os.path.exists(path):
            QMessageBox.critical(self, "Error", f"Profile file not found: {name}.json")
            self._refresh_profile_list()
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                import json
                loaded_settings = json.load(f)

            # Update the settings for the currently selected job (if any)
            job_index = self._get_selected_job_index()
            if job_index is not None:
                self.job_queue[job_index]['settings'].update(loaded_settings)
            else:
                # If no job is selected, update the global defaults instead
                self.current_settings.update(loaded_settings)

            # Repopulate the panel with the new settings
            self._populate_settings_panel()

            if 'translator_chain' in loaded_settings:
                self._rebuild_chain_from_string(loaded_settings['translator_chain'])

            # Manually trigger the UI state update for the chain builder
            self._update_chain_ui_state()

            # --- CRITICAL FIX ---
            # After populating, explicitly ensure the settings panel is enabled,
            # as long as a job is selected. This prevents it from getting stuck in a disabled state.
            self._set_settings_panel_enabled(job_index is not None)

            self.log("SUCCESS", f"Profile '{name}' loaded and applied.")
            print(f"Profile '{name}' loaded successfully.")

        except Exception as e:
            error_message = f"An unexpected error occurred while loading profile '{name}'.\n\nDetails: {e}"
            print(f"[ERROR] {error_message}")
            QMessageBox.critical(self, "Profile Load Error", error_message)
        self._set_settings_panel_enabled(True)

    def _delete_profile(self):
        """Deletes the selected profile."""
        name = self.profile_combobox.currentText()
        if not name or name == "No profiles found":
            return

        reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete profile '{name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        profiles_dir = os.path.join(self.project_base_dir, "MangaStudio_Data", "profiles")
        path = os.path.join(profiles_dir, f"{name}.json")
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"Profile '{name}' deleted.")
                self._refresh_profile_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete profile: {e}")
            print(f"[ERROR] Failed to delete profile '{name}': {e}")

    def _create_bottom_panel(self) -> QWidget:
        """Creates the bottom panel with progress bar and control buttons."""
        bottom_frame = QFrame()
        bottom_frame.setFrameShape(QFrame.Shape.NoFrame)
        layout = QHBoxLayout(bottom_frame)
        layout.setContentsMargins(0, 0, 0, 0)

        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setSpacing(2)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)

        self.start_button = QPushButton("▶️ START PIPELINE")
        self.start_button.clicked.connect(self._start_pipeline_thread)
        self.start_button.setFixedHeight(40)
        font = self.start_button.font()
        font.setBold(True)
        self.start_button.setFont(font)

        self.stop_button = QPushButton("⏹️ STOP")
        self.stop_button.clicked.connect(self._stop_pipeline)
        self.stop_button.setEnabled(False)
        self.stop_button.setFixedHeight(40)

        layout.addWidget(progress_widget, stretch=1)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        return bottom_frame

    def _create_font_scale_widget(self) -> QWidget:
        """Creates a special row for the UI font scaling option."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)

        label = QLabel("UI Font Scale:")
        label.setToolTip("Changes the font size for the entire application UI.")
        row_layout.addWidget(label, stretch=1)

        self.font_scale_combobox = SearchableComboBox()
        self.font_scale_combobox.addItems(["75%", "85%", "100% (Default)", "115%", "125%", "150%"])
        self.font_scale_combobox.setCurrentText("100% (Default)")

        # Connect the combobox signal to the handler function
        self.font_scale_combobox.currentTextChanged.connect(self._on_font_scale_changed)

        row_layout.addWidget(self.font_scale_combobox, stretch=2)
        return row_widget

    def _on_font_scale_changed(self, text: str):
        """
        Applies a global font size by RE-APPLYING the currently selected theme,
        which will automatically use the new font scale.
        """
        # Get the name of the currently selected theme from the combobox
        current_theme_name = self.theme_combobox.currentText()
        
        # Re-apply the theme. This function is smart enough to read the new font
        # scale from the combobox and include it in the full stylesheet.
        self._apply_theme(current_theme_name)

    def _connect_widget_signal(self, key: str, widget: QWidget, context_key: str = None):
        """
        Connects the appropriate signal of a widget to the setting change handler.
        This version correctly passes the context_key to the handler.
        """
        info = self.config_loader.full_config_data.get(key, {})
        widget_type = info.get("widget")

        # Create a handler function that "captures" the current key and context_key.
        # The lambda function is perfect for this.
        handler = lambda *args, k=key, ctx=context_key: self._on_setting_changed(k, ctx)

        if isinstance(widget, QComboBox):
            # For QComboBox, currentIndexChanged sends an integer index, which we can ignore with *args
            widget.currentIndexChanged.connect(handler)
            if key in ['offline_translator', 'ai_translator']:
                widget.currentTextChanged.connect(self._on_translator_changed)
                if key == 'ai_translator':
                    widget.currentTextChanged.connect(self._sync_ai_credentials)
        elif isinstance(widget, QCheckBox):
            # For QCheckBox, stateChanged sends the state, which we can ignore with *args
            widget.stateChanged.connect(handler)
            if key == 'enable_translator_chain':
                widget.stateChanged.connect(self._update_chain_ui_state)
            if key == 'restore_size_after_colorize':
                widget.stateChanged.connect(self._update_colorize_restore_ui_state)
        elif isinstance(widget, QLineEdit):
            # editingFinished has no arguments, so it works perfectly.
            widget.editingFinished.connect(handler)
        elif widget_type in ["segmented_button", "grid_segmented_button"]:
            button_group = widget.findChild(QButtonGroup)
            if button_group:
                button_group.buttonClicked.connect(handler)
                if key == 'translator_category':
                    button_group.buttonClicked.connect(lambda *args: self._on_translator_category_changed())
        elif widget_type == "api_profile_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                combo.currentTextChanged.connect(handler)
                combo.currentTextChanged.connect(self._on_api_profile_changed)
                if combo.lineEdit():
                    combo.lineEdit().returnPressed.connect(combo.showPopup)
        elif widget_type == "ai_model_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                combo.currentTextChanged.connect(handler)
                combo.activated.connect(lambda index: self._on_setting_changed('ai_model'))
        elif widget_type == "api_group_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                combo.currentTextChanged.connect(handler)
                combo.currentTextChanged.connect(self._on_api_group_changed)
                if combo.lineEdit():
                    combo.lineEdit().returnPressed.connect(combo.showPopup)
        elif widget_type == "language_checkbox_grid":
            checkbox_dict = self.widget_references.get(key, {})
            if checkbox_dict:
                for checkbox in checkbox_dict.values():
                    # stateChanged sends the state, which we can ignore with *args
                    checkbox.stateChanged.connect(handler)
        elif widget_type == "slider":
            slider = widget.findChild(QSlider)
            if slider:
                # valueChanged sends the new value, which we can ignore with *args
                slider.valueChanged.connect(handler)
        elif widget_type == "entry_with_button":
            entry = widget.findChild(QLineEdit)
            if entry:
                # editingFinished has no arguments.
                entry.editingFinished.connect(handler)

    def _on_setting_changed(self, key: str, context_key: str = None):
        """
        A generic handler called whenever a setting widget's value changes.
        """
        if context_key:  # It's a setting for a special task
            widget = self.task_widgets[context_key].get(key)
            new_value = self._get_value_from_widget(key, widget)  # Pass widget directly
            self.task_settings[context_key][key] = new_value
            print(f"[Task Settings] Updated '{context_key}.{key}' to: {new_value}")
        else:  # It's a global setting for the main pipeline
            widget = self.setting_widgets.get(key)
            if key == 'translator_chain':
                new_value = self._get_translator_chain_string()
            else:
                new_value = self._get_value_from_widget(key, widget)
            self.current_settings[key] = new_value
            print(f"[Settings] Updated '{key}' to: {new_value}")

    def _on_translator_changed(self, translator_name: str):
        """Handles changes in the main translator selection."""
        if translator_name and " (Not Setup)" in translator_name:
            translator_name = translator_name.split(" (Not Setup)")[0]
        # Filter the main target language dropdown
        lang_combo = self.setting_widgets.get('target_lang')
        self._filter_language_dropdown(translator_name, lang_combo)

        # Update the tooltip
        self._update_translator_tooltip(translator_name)

    def _filter_language_dropdown(self, translator_name: str, lang_combo: QComboBox):
        """
        A centralized function to filter a given language QComboBox based on
        the capabilities of the selected translator.
        """
        if not lang_combo:
            return

        if translator_name and " (Not Setup)" in translator_name:
            translator_name = translator_name.split(" (Not Setup)")[0]

        # Default to allowing all languages if capabilities are unknown for this translator
        capabilities = TRANSLATOR_CAPABILITIES.get(translator_name, {'__any__': '__all__'})
        supported_codes = set()

        if capabilities.get('__any__') == '__all__':
            all_langs = list(LANGUAGES.values())
            if "auto" in all_langs:
                all_langs.remove("auto")
            supported_codes = set(all_langs)
        else:
            for source_lang, target_langs in capabilities.items():
                supported_codes.update(target_langs)

        supported_display_names = [name for name, code in LANGUAGES.items() if code in supported_codes]

        current_selection = lang_combo.currentText()

        lang_combo.blockSignals(True)
        lang_combo.clear()
        if not supported_display_names:
            lang_combo.addItem("No Supported Targets")
            lang_combo.setEnabled(False)
        else:
            lang_combo.addItems(sorted(supported_display_names))
            lang_combo.setEnabled(True)
        lang_combo.blockSignals(False)

        if current_selection in supported_display_names:
            lang_combo.setCurrentText(current_selection)
        elif "English" in supported_display_names:
            lang_combo.setCurrentText("English")

    def _get_value_from_widget(self, key: str, widget: QWidget) -> any:
        """Retrieves the current value from a given widget by its key."""
        # The widget is now passed directly, no need for lookup
        if not widget:
            return None

        info = self.config_loader.full_config_data.get(key, {})
        widget_type = info.get("widget")

        if isinstance(widget, QComboBox):
            if widget_type == "optionmenu_languages":
                return LANGUAGES.get(widget.currentText(), "auto")
            val = widget.currentData()
            if val is not None:
                return val
            return widget.currentText()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        elif widget_type in ["segmented_button", "grid_segmented_button"]:
            button_group = widget.findChild(QButtonGroup)
            if button_group and button_group.checkedButton():
                value = button_group.checkedButton().text()
                if key == "upscale_ratio":
                    if value == "Disabled":
                        return None  # Return None instead of the string "Disabled"
                    else:
                        return int(value.replace("x", ""))
                return value
            return None  # Return None if no button is checked
        elif widget_type in ["api_profile_selector", "api_group_selector", "ai_model_selector"]:
            combo = widget.findChild(QComboBox)
            return combo.currentText() if combo else None
        elif key == "language_checkbox_grid":
            checkbox_dict = self.widget_references.get(key, {})
            selected = [code for code, cb in checkbox_dict.items() if cb.isChecked()]
            return ",".join(sorted(selected))
        elif widget_type == "slider":
            slider = widget.findChild(QSlider)
            if slider:
                precision = 100
                multiplier = info.get("value_multiplier", 1)
                actual_value = (slider.value() / precision) * multiplier

                # Get the format string to decide if we need an int or a float
                value_format = info.get("value_format", "{:.0f}")

                # If the format string specifies an integer (like "{:.0f}")
                if value_format.endswith("0f}"):
                    return int(round(actual_value))
                else:
                    # Otherwise, it's a float. Return it rounded for cleanliness.
                    return round(actual_value, 4)
            return None
        elif widget_type == "entry_with_button":
            entry = widget.findChild(QLineEdit)
            if entry:
                return entry.text()
            return None

        return None

    def _set_widget_value(self, key: str, value: any, widget: QWidget):
        """Sets the value of a given widget by its key."""
        if not widget or value is None:
            return

        info = self.config_loader.full_config_data.get(key, {})
        widget_type = info.get("widget")

        if isinstance(widget, QComboBox):
            if widget_type == "optionmenu_languages":
                display_name = next((k for k, v in LANGUAGES.items() if v == value), None)
                if display_name:
                    widget.setCurrentText(display_name)
            else:
                index = -1
                for i in range(widget.count()):
                    if widget.itemData(i) == value:
                        index = i
                        break
                if index != -1:
                    widget.setCurrentIndex(index)
                else:
                    widget.setCurrentText(str(value))
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value))
        elif widget_type == "segmented_button":
            button_group = widget.findChild(QButtonGroup)
            if button_group:
                value_to_check = str(value)
                if key == "upscale_ratio":
                    if value is None:
                        value_to_check = "Disabled"
                    else:
                        value_to_check = f"{value}x"

                for button in button_group.buttons():
                    if button.text() == value_to_check:
                        button.setChecked(True)
                        break
        elif widget_type == "grid_segmented_button":
            button_group = widget.findChild(QButtonGroup)
            if button_group:
                value_to_check = str(value)
                for button in button_group.buttons():
                    if button.text() == value_to_check:
                        button.setChecked(True)
                        break
        elif key == "language_checkbox_grid":
            checkbox_dict = self.widget_references.get(key, {})
            selected_langs = set(str(value).split(','))
            for code, cb in checkbox_dict.items():
                cb.setChecked(code in selected_langs)
        elif widget_type == "slider":
            slider = widget.findChild(QSlider)
            if slider and value is not None:
                precision = 100
                multiplier = info.get("value_multiplier", 1)
                slider_value = int((float(value) / multiplier) * precision) if multiplier != 0 else 0
                slider.setValue(slider_value)

                update_func = getattr(slider, 'update_label_func', None)
                if update_func:
                    update_func(slider_value)
        elif widget_type == "entry_with_button":
            entry = widget.findChild(QLineEdit)
            if entry:
                entry.setText(str(value))
        elif widget_type in ["api_profile_selector", "api_group_selector"]:
            combo = widget.findChild(QComboBox)
            if combo:
                combo.blockSignals(True)
                combo.setCurrentText(str(value))
                combo.blockSignals(False)
        elif widget_type == "ai_model_selector":
            combo = widget.findChild(QComboBox)
            if combo:
                value_str = str(value)
                if value_str and combo.findText(value_str) == -1:
                    combo.addItem(value_str)
                combo.blockSignals(True)
                combo.setCurrentText(value_str)
                combo.blockSignals(False)

    def _add_job(self):
        """Opens a dialog to select a folder and adds it as a job."""
        # Use the last selected directory, or the project base directory as a fallback.
        initial_dir = getattr(self, 'last_selected_directory', self.project_base_dir)

        folder_path = QFileDialog.getExistingDirectory(self, "Select Manga/Image Folder", initial_dir)

        if folder_path:
            # Store the newly selected directory to be saved on exit.
            self.last_selected_directory = folder_path
            self._add_job_from_path(folder_path)

    def _add_job_from_path(self, path):
        """
        Adds a job with a default 'Awaiting Config' status to the queue
        and selects it in the UI.
        """
        import time

        job_id = f"job_{int(time.time() * 1000)}_{len(self.job_queue)}"
        job_data = {
            "id": job_id,
            "source_path": path,
            "name": os.path.basename(path),
            # A new job starts with a fresh copy of factory defaults
            "settings": self.config_loader.get_factory_defaults().copy(),
            # A new job is awaiting configuration by the user
            "status": "Awaiting Config",  # Status: ⚪
            # A new job has no assigned type until a configuration is applied
            "job_type": None
        }
        self.job_queue.append(job_data)

        # Refresh the entire queue UI to show the new job
        self._update_job_list_ui()

        # --- CRITICAL FIX: Select the newly added item in the correct list widget ---
        # Find the item we just added by its unique job_id and set it as the current row.
        for i in range(self.queue_list_widget.count()):
            item = self.queue_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == job_id:
                # Setting the current row will automatically trigger the
                # _on_job_selection_changed signal, which is what we want.
                self.queue_list_widget.setCurrentRow(i)
                break

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isdir(path):
                    self._add_job_from_path(path)
                else:
                    self.log("WARNING", f"Dropped item is not a directory: {path}")
            event.acceptProposedAction()
        else:
            event.ignore()

    def _remove_selected_jobs_from_queue(self):
        """Placeholder for removing selected jobs. To be implemented with context menu."""
        print("Action: Remove Selected Jobs (Not yet implemented)")
        # Future logic will go here
        # selected_items = self.queue_list_widget.selectedItems()
        # ... loop and remove from self.job_queue ...
        # self._update_job_list_ui()

    def _duplicate_selected_jobs(self):
        """
        Creates a new, clean job using the same source path as the selected job(s).
        The new job will have factory default settings and no assigned job type.
        """
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            return

        jobs_to_add = []
        for item in selected_items:
            original_job_id = item.data(Qt.ItemDataRole.UserRole)
            original_job = next((job for job in self.job_queue if job['id'] == original_job_id), None)

            if original_job:
                # Create a completely new job dictionary, only reusing the source path and name.
                # This is similar to adding a brand new job.
                new_job = {
                    "id": f"job_{int(time.time() * 1000)}_{len(self.job_queue) + len(jobs_to_add)}",
                    "source_path": original_job['source_path'],
                    "name": original_job['name'],
                    # The new job gets fresh factory defaults, not copied ones.
                    "settings": self.config_loader.get_factory_defaults().copy(),
                    # The new job starts as a blank slate, awaiting configuration.
                    "status": "Awaiting Config",
                    "job_type": None
                }
                jobs_to_add.append(new_job)

        self.job_queue.extend(jobs_to_add)

        self._update_job_list_ui()
        self.log("INFO", f"Duplicated {len(jobs_to_add)} job(s) as new, unconfigured tasks.")

    def _clear_queue(self):
        """Removes all jobs from the queue after confirmation."""
        if not self.job_queue:
            return

        reply = QMessageBox.question(self, "Confirm Clear Queue",
                                     "Are you sure you want to remove ALL jobs from the queue?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.job_queue.clear()
            self.log("INFO", "All jobs have been cleared from the queue.")
            self._update_job_list_ui()

    def _clear_history(self):
        """Removes all jobs from the history list after confirmation."""
        if not self.history_queue:
            return

        reply = QMessageBox.question(self, "Confirm Clear History",
                                     "Are you sure you want to remove ALL jobs from the history?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.history_queue.clear()
            self.log("INFO", "History has been cleared.")
            self._update_history_list_ui()

    def _move_job(self, direction: str):
        """Moves the selected job up or down in the queue."""
        # This function is now superseded by drag-and-drop, but we keep it for now.
        if not self.selected_job_id or len(self.job_queue) < 2:
            return

        index = self._get_selected_job_index()
        if index is None:
            return

        if direction == "up" and index > 0:
            new_index = index - 1
        elif direction == "down" and index < len(self.job_queue) - 1:
            new_index = index + 1
        else:
            return

        self.job_queue.insert(new_index, self.job_queue.pop(index))
        self._update_job_list_ui()

        # Keep the moved item selected in the new list widget
        self.queue_list_widget.setCurrentRow(new_index)

    def _update_job_list_ui(self):
        """
        Refreshes both the queue and history list widgets based on the current state
        of self.job_queue and self.history_queue.
        """
        # Block signals to prevent selection changes from firing events during redraw
        self.queue_list_widget.blockSignals(True)
        self.queue_list_widget.clear()

        # Populate the queue list
        for i, job in enumerate(self.job_queue, 1):  # Use enumerate to get numbers starting from 1
            status_icon = "⚪"
            if job.get('status') == "Ready":
                status_icon = "🟢"
            elif job.get('status') == "Processing":
                status_icon = "🟡"

            job_type = job.get('job_type')
            job_type_tag = f"[{job_type}]" if job_type else ""

            # Prepend the number to the display text
            display_text = f"{i}. {job_type_tag} {status_icon} {job['name']}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, job['id'])  # Store ID for reference
            self.queue_list_widget.addItem(item)

        self.queue_list_widget.blockSignals(False)

    def _update_history_list_ui(self):
        """Refreshes the history list widget based on the self.history_queue."""
        self.history_list_widget.clear()

        # Populate the history list from the end (most recent first)
        for i, job in enumerate(reversed(self.history_queue), 1):  # Use enumerate here as well
            status = job.get('status', 'Unknown')

            if status == "Completed":
                status_icon = "✅"
            elif status == "Failed":
                status_icon = "❌"
            elif status == "Stopped":
                status_icon = "⏹️"
            else:
                status_icon = "❔"

            job_type = job.get('job_type')
            job_type_tag = f"[{job_type}]" if job_type else ""

            # Prepend the number
            display_text = f"{i}. {job_type_tag} {status_icon} {job['name']}"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, job['id'])

            # Color the item based on status
            if status == "Failed" or status == "Stopped":
                item.setForeground(Qt.GlobalColor.red)
            elif status == "Completed":
                item.setForeground(Qt.GlobalColor.green)

            self.history_list_widget.addItem(item)

    def _on_job_selection_changed(self):
        """
        Handles the logic when a different job is selected in the queue list.
        This now ONLY updates the internal reference to the selected job ID
        and no longer automatically loads its settings into the panel.
        """
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            self.selected_job_id = None
        else:
            # We still need to know which job is selected for context menu actions.
            self.selected_job_id = selected_items[0].data(Qt.ItemDataRole.UserRole)

        print(f"[Jobs] Selection changed to job ID: {self.selected_job_id}. Panel state is not affected.")

    def _populate_settings_panel(self):
        """
        Updates all setting widgets to reflect the settings of the currently selected job
        OR the application's default settings if no job is selected.
        This function is now smart enough to handle special compound widgets.
        """
        # Determine the source of settings
        job_index = self._get_selected_job_index()
        if job_index is not None:
            settings_source = self.job_queue[job_index]['settings']
        else:
            # If no job is selected, show factory defaults
            settings_source = self.config_loader.get_factory_defaults()

        # Update the main settings dictionary to reflect what's being shown
        self.current_settings = copy.deepcopy(settings_source)

        # Block signals on all widgets to prevent infinite loops during programmatic changes
        for widget in self.setting_widgets.values():
            if widget:
                widget.blockSignals(True)
                if isinstance(widget, QWidget) and widget.findChild(QSlider):
                    widget.findChild(QSlider).blockSignals(True)

        # Update all widgets with the new values from the determined source
        for key, value in self.current_settings.items():
            widget = self.setting_widgets.get(key)
            if widget:
                # SPECIAL HANDLING for the translator chain
                if key == 'translator_chain':
                    # The value is a string like 'sugoi:ENG'. Rebuild the UI from it.
                    if hasattr(self, '_rebuild_chain_from_string'):
                        self._rebuild_chain_from_string(value or "")
                    # Also update the 'enable' checkbox state
                    enable_checkbox = self.setting_widgets.get('enable_translator_chain')
                    if enable_checkbox:
                        # If the chain string is not empty, the checkbox should be checked.
                        is_chain_enabled = bool(value)
                        enable_checkbox.setChecked(is_chain_enabled)
                        # Trigger the UI state update to enable/disable the correct panels
                        self._update_chain_ui_state()
                else:
                    # Standard handling for all other widgets
                    self._set_widget_value(key, value, widget)

        # Unblock signals to restore normal user interaction
        for widget in self.setting_widgets.values():
            if widget:
                widget.blockSignals(False)
                if isinstance(widget, QWidget) and widget.findChild(QSlider):
                    widget.findChild(QSlider).blockSignals(False)
                    
        self._update_translator_visibility()

    def _get_selected_job_index(self) -> int | None:
        """Finds the index in job_queue for the currently selected job_id."""
        if not self.selected_job_id:
            return None
        for i, job in enumerate(self.job_queue):
            if job['id'] == self.selected_job_id:
                return i
        return None

    def _load_test_image(self):
        """Opens a file dialog to load a test image and displays it."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a Test Image", "", "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)")
        if not file_path:
            return

        self.test_image_path = file_path
        print(f"[Visual Test] Loaded test image: {os.path.basename(file_path)}")

        try:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                raise ValueError("Pixmap is null. The image file may be corrupt or in an unsupported format.")

            # Clear previous images
            self.original_scene.clear()
            self.translated_scene.clear()

            # Display the new image in the 'Original' view
            self.original_pixmap_item = self.original_scene.addPixmap(pixmap)

            # Also create a placeholder in the 'Translated' view to maintain sync
            self.translated_pixmap_item = self.translated_scene.addPixmap(QPixmap())  # Empty pixmap

            # Fit the image to the view and enable the run button
            self.run_test_button.setEnabled(True)
            QTimer.singleShot(50, self._fit_image_to_view)

        except Exception as e:
            print(f"[ERROR] Failed to load image file: {e}")
            QMessageBox.critical(self, "Error", f"Could not load the image:\n{e}")

    def _fit_image_to_view(self):
        """Resets the view to fit the entire image within the visible area."""
        if not self.original_pixmap_item or self.original_pixmap_item.pixmap().isNull():
            return
        # Use the bounding rectangle of the pixmap item to fit it perfectly
        self.original_view.fitInView(self.original_pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.translated_view.fitInView(self.original_pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)  # Use original's rect for sync
        self._update_zoom_label()

    def _wheel_event_zoom(self, event):
        """Handles zooming with Ctrl+MouseWheel, respecting the zoom limit checkbox."""
        if not self.original_pixmap_item or event.modifiers() != Qt.KeyboardModifier.ControlModifier:
            QGraphicsView.wheelEvent(self.original_view, event)
            QGraphicsView.wheelEvent(self.translated_view, event)
            return

        # Define zoom factors and limits
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        # Get the current zoom level before making changes
        current_zoom = self.original_view.transform().m11()

        # Determine the zoom direction
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        # Check if zoom limiting is enabled
        if self.limit_zoom_check.isChecked():
            # Define standard limits (e.g., 5% to 800%)
            min_zoom, max_zoom = 0.05, 8.0
            # Only apply the zoom if the new level will be within the allowed range
            if (current_zoom * zoom_factor > min_zoom
                    and current_zoom * zoom_factor < max_zoom):
                self.original_view.scale(zoom_factor, zoom_factor)
                self.translated_view.scale(zoom_factor, zoom_factor)
        else:
            # If limiting is off, apply more generous limits to prevent freezing
            min_zoom, max_zoom = 0.01, 100.0
            if (current_zoom * zoom_factor > min_zoom
                    and current_zoom * zoom_factor < max_zoom):
                self.original_view.scale(zoom_factor, zoom_factor)
                self.translated_view.scale(zoom_factor, zoom_factor)

        self._update_zoom_label()

    def _update_zoom_label(self):
        """Updates the zoom level display label."""
        # The zoom level is the square root of the determinant of the view's matrix
        zoom = self.original_view.transform().m11()
        self.zoom_label.setText(f"Zoom: {zoom * 100:.0f}%")

    def _run_visual_test_thread(self):
        """Starts the visual test pipeline in a separate thread to avoid freezing the UI."""
        if not self.test_image_path:
            QMessageBox.warning(self, "No Image", "Please load a test image first.")
            return

        # Disable the button to prevent multiple clicks
        self.run_test_button.setEnabled(False)
        self.run_test_button.setText("Testing...")

        # Run the _run_visual_test method in a new thread
        thread = threading.Thread(target=self._run_visual_test, daemon=True)
        thread.start()

    def _run_visual_test(self):
        """Prepares and runs the pipeline on the single loaded test image."""
        self.log("PIPELINE", "Starting visual test pipeline...")

        # Create a temporary 'job' dictionary to hold the settings for the test.
        # This job is a 'Translate' type job for the purpose of config building.
        test_job = {
            "id": "visual_test_job",
            "job_type": "T",  # Treat it as a standard translate job
            "settings": copy.deepcopy(self.current_settings)
        }

        if self.fast_preview_check.isChecked():
            self.log("INFO", "Fast Preview enabled. Overriding settings for speed.")
            test_job['settings'].update({'detection_size': 1024, 'inpainting_size': 1024})
            if test_job['settings'].get('processing_device') == 'NVIDIA GPU':
                test_job['settings']['inpainting_precision'] = 'bf16'

        # Build the final configuration using our new centralized function
        final_config = self._build_final_config_for_job(test_job)

        # Define temporary and final paths for the output
        source_dir = os.path.dirname(self.test_image_path)
        source_name = os.path.splitext(os.path.basename(self.test_image_path))[0]
        # Use a more descriptive name for the final output
        final_output_dir = os.path.join(source_dir, f"{source_name}_translated_test")

        # Clean up old results before starting
        if os.path.exists(final_output_dir):
            shutil.rmtree(final_output_dir)

        # The pipeline now directly creates the final folder, so we don't need a temp output dir
        is_verbose = test_job['settings'].get("enable_verbose_output", False)

        # Call the updated pipeline function with the ready-made config
        success = self.pipeline.run_single_image_test(
            self.test_image_path,
            final_output_dir,
            final_config,
            self.log,
            is_verbose
        )

        if success:
            self.log("SUCCESS", "Visual test backend process completed.")
            result_files = os.listdir(final_output_dir)
            if result_files:
                # Find the resulting image (it should have the same name as the original)
                original_filename = os.path.basename(self.test_image_path)
                result_path = os.path.join(final_output_dir, original_filename)
                if os.path.exists(result_path):
                    # Use QTimer to ensure UI updates happen on the main thread
                    QTimer.singleShot(0, lambda: self._display_test_result(result_path))
                else:
                    self.log("ERROR", "Could not find the translated image in the output folder.")
        else:
            self.log("ERROR", "Visual test failed or was stopped.")
            # Clean up the potentially empty output folder on failure
            if os.path.exists(final_output_dir) and not os.listdir(final_output_dir):
                shutil.rmtree(final_output_dir)

        # Use QTimer to ensure the button is re-enabled on the main thread
        QTimer.singleShot(0, self._on_visual_test_finished)

    def _display_test_result(self, image_path: str):
        """Loads the result image and displays it in the 'Output' view."""
        print(f"[Visual Test] Displaying result from: {image_path}")
        try:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                raise ValueError("Result pixmap is null.")

            # Clear the old placeholder and display the new result
            self.translated_scene.clear()
            self.translated_pixmap_item = self.translated_scene.addPixmap(pixmap)

            # Ensure the view is still synchronized
            self._fit_image_to_view()

        except Exception as e:
            print(f"[ERROR] Failed to load result image: {e}")
            QMessageBox.critical(self, "Error", f"Could not load the result image:\n{e}")

    def _on_visual_test_finished(self):
        """Resets the 'Run Test' button to its normal state."""
        self.run_test_button.setEnabled(True)
        self.run_test_button.setText("Run Test")

    def _create_log_tab(self) -> QWidget:
        """Creates the content for the 'Live Log' tab."""
        container = QWidget()
        layout = QVBoxLayout(container)

        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        header_layout.addStretch()  # Push button to the right
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self._clear_log)
        header_layout.addWidget(clear_button)

        # The main text widget for logging, set to read-only
        self.log_textbox = QTextEdit()
        self.log_textbox.setReadOnly(True)
        self.log_textbox.setFont(QFont("Consolas", 10))  # Use a monospaced font

        layout.addWidget(header_frame)
        layout.addWidget(self.log_textbox, stretch=1)
        return container

    def log(self, level: str, message: str):
        """
        Thread-safe method to log messages, with intelligent parsing for RAW backend output.
        It emits a signal that the main UI thread will catch.
        """
        # This logic mimics the original application's behavior for cleaner logs.
        if level.upper() == "RAW":
            # For RAW messages from the backend, we don't add our own prefix.
            # We pass the message through directly.
            raw_message = message.strip()
            msg_lower = raw_message.lower()

            # We can still re-classify the message type based on content for coloring.
            log_level_for_color = "INFO"  # Default for raw messages
            if msg_lower.startswith(('error:', 'validationerror:', 'exception:', 'traceback')):
                log_level_for_color = "ERROR"
            elif "out of memory" in msg_lower or "allocation failed" in msg_lower:
                log_level_for_color = "ERROR"

            color = LOG_COLORS.get(log_level_for_color, "white")
            # We emit the RAW message without any extra prefixes.
            self.log_signal.emit(color, raw_message)
        else:
            # For our own UI-generated logs (PIPELINE, SUCCESS, etc.), we add a prefix.
            color = LOG_COLORS.get(level.upper(), "white")
            self.log_signal.emit(color, f"[{level.upper()}] {message.strip()}")

    def _insert_log_text(self, color: str, message: str):
        """
        This is the slot that receives the log signal. It safely updates the
        QTextEdit widget from the main UI thread.
        """
        # Use simple HTML to color the text
        self.log_textbox.append(f'<span style="color:{color};">{message}</span>')

    def _clear_log(self):
        """Clears all text from the log box."""
        self.log_textbox.clear()

    def _start_pipeline_thread(self):
        """Starts the main job processing pipeline in a separate thread."""
        if self.is_running_pipeline:
            return
        if not self.job_queue:
            QMessageBox.information(self, "Information", "Please add one or more jobs to the queue first.")
            return

        self._stopped_by_user = False

        self._toggle_ui_state(True)
        thread = threading.Thread(target=self._run_pipeline, daemon=True)
        thread.start()

    def _update_colorize_restore_ui_state(self):
        """Enables or disables the upscale factor widget based on the checkbox."""
        restore_checkbox = self.setting_widgets.get('restore_size_after_colorize')
        factor_widget = self.setting_widgets.get('colorize_upscale_factor')

        if not all([restore_checkbox, factor_widget]):
            return

        is_enabled = restore_checkbox.isChecked()
        factor_widget.setEnabled(is_enabled)

    def _build_final_config_for_job(self, job: dict) -> dict:
        """
        Builds the correct, nested config dictionary for a specific job
        by ONLY using the settings stored within that job object.
        """
        job_type = job.get('job_type')
        settings = job.get('settings', {})
        
        final_config = {}
        all_props = self.config_loader.full_config_data

        for key, prop_info in all_props.items():
            if key not in settings: continue
            
            value = settings.get(key)
            if value == "" or value is None: continue

            # Skip font_family, it's handled manually below
            if key == 'font_family':
                continue

            group = prop_info.get("group", "")
            if "General & Translator" in group:
                target_dict = final_config.setdefault("translator", {})
            elif "Detector & OCR" in group:
                if key in ["ocr", "use_mocr_merge", "min_text_length", "ignore_bubble", "prob"]:
                    target_dict = final_config.setdefault("ocr", {})
                else:
                    target_dict = final_config.setdefault("detector", {})
            elif "Image & Inpainter" in group:
                if key in ["upscaler", "revert_upscaling", "upscale_ratio"]:
                    target_dict = final_config.setdefault("upscale", {})
                elif key in ["colorizer", "colorization_size", "denoise_sigma"]:
                    target_dict = final_config.setdefault("colorizer", {})
                else:
                    target_dict = final_config.setdefault("inpainter", {})
            elif "Render & Output" in group:
                target_dict = final_config.setdefault("render", {})
            else:
                final_config[key] = value
                continue
            
            target_dict[key] = value

        # --- NEW SIMPLIFIED FONT LOGIC ---
        selected_font_name = settings.get('font_family')
        if selected_font_name and selected_font_name in self.font_map:
            # Always get the path from our map and add it for the CLI argument
            final_config['font_path'] = self.font_map[selected_font_name]
            # Also add it to the render config for GIMP, just in case
            final_config.setdefault('render', {})['gimp_font'] = selected_font_name
        # --- END OF FONT LOGIC ---

        # Resolve active translator name based on category
        translator_dict = final_config.setdefault("translator", {})
        category = settings.get('translator_category', 'Offline')
        if category == 'Offline':
            translator_dict['translator'] = settings.get('offline_translator', 'sugoi')
        else:
            translator_dict['translator'] = settings.get('ai_translator', 'gemini')

        if settings.get('translator_chain'):
            final_config.get("translator", {}).pop('translator', None)
        
        final_config['processing_device'] = settings.get('processing_device', 'CPU')

        if job_type in ['R', 'U', 'C']:
            task_key_map = {'R': 'raw_output', 'U': 'upscale', 'C': 'colorize'}
            task_info = self.config_loader.tasks_config.get(task_key_map.get(job_type), {})
            backend_overrides = task_info.get("backend_config", {})
            for category, overrides in backend_overrides.items():
                final_config.setdefault(category, {}).update(overrides)

        return final_config

    def _run_pipeline(self):
        """
        Processes all 'Ready' jobs in the queue sequentially.
        This version includes "resume" functionality and smart folder naming
        to avoid conflicts, based on user settings.
        """
        try:
            while self.is_running_pipeline:
                job_to_process = next((job for job in self.job_queue if job.get('status') == 'Ready'), None)
                if not job_to_process:
                    self.log("PIPELINE", "No more 'Ready' jobs in the queue. Finishing run.")
                    break

                job = job_to_process
                self.currently_processing_job_id = job['id']
                job['status'] = 'Processing'
                self._update_job_list_ui()
                self._toggle_ui_state(True, job['id'])

                settings = job.get('settings', {})
                selected_mode = settings.get('processing_mode', 'Automatic')
                output_format = settings.get('output_format', 'png')

                mode_to_use = 'High VRAM'
                if selected_mode == 'Low VRAM' or (selected_mode == 'Automatic' and self.detected_vram_gb > 0 and self.detected_vram_gb <= 6):
                    mode_to_use = 'Low VRAM'

                # --- NEW FOLDER NAMING LOGIC ---
                source_path = job['source_path']
                job_type_tag = f"TASK-{job.get('job_type')}" if job.get('job_type') != 'T' else settings.get('target_lang', 'ENG')
                base_output_folder_name = f"{os.path.basename(source_path)}-{job_type_tag}"
                output_dir = os.path.dirname(source_path)
                
                final_output_folder_name = base_output_folder_name

                # Check the user's preference for avoiding conflicts
                if settings.get('avoid_conflicts', True):
                    counter = 1
                    # Append (1), (2), etc., until a unique name is found
                    while os.path.exists(os.path.join(output_dir, final_output_folder_name)):
                        final_output_folder_name = f"{base_output_folder_name} ({counter})"
                        counter += 1
                
                final_output_path = os.path.join(output_dir, final_output_folder_name)
                # --- END OF FOLDER NAMING LOGIC ---

                os.makedirs(final_output_path, exist_ok=True)
                all_source_files = sorted([f for f in os.listdir(source_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp'))])

                try:
                    processed_files = {os.path.splitext(f)[0] for f in os.listdir(final_output_path) if f.lower().endswith(f".{output_format}")}
                    files_to_process = [f for f in all_source_files if os.path.splitext(f)[0] not in processed_files]
                except FileNotFoundError:
                    files_to_process = all_source_files

                if not files_to_process:
                    self.log("INFO", f"All files for job '{job['name']}' seem to be processed already. Skipping to avoid errors.")
                    job['status'] = "Completed"
                    self.job_queue.remove(job)
                    self.history_queue.append(job)
                    self._update_job_list_ui()
                    self._update_history_list_ui()
                    # A small delay to let the UI update before the pipeline finishes
                    QApplication.processEvents() 
                    continue # Move to the next job in the queue
                
                # (The rest of the function remains exactly the same as before)
                self.log("INFO", f"Found {len(files_to_process)} unprocessed image(s) for job '{job['name']}'.")

                success = True
                if mode_to_use == 'Low VRAM':
                    try:
                        batch_size = int(settings.get('batch_size', 5))
                        if batch_size <= 0: batch_size = 1
                    except ValueError:
                        batch_size = 5

                    self.log("PIPELINE", f"Resuming job '{job['name']}' in Low VRAM Mode (Batch Size: {batch_size}).")
                    num_batches = (len(files_to_process) + batch_size - 1) // batch_size

                    for i in range(num_batches):
                        if not self.is_running_pipeline:
                            success = False
                            break

                        batch_files = files_to_process[i * batch_size: (i + 1) * batch_size]
                        self.log("INFO", f"Processing batch {i + 1}/{num_batches} ({len(batch_files)} images)...")

                        temp_batch_dir = os.path.join(self.temp_dir, f"batch_{job['id']}")
                        if os.path.exists(temp_batch_dir): shutil.rmtree(temp_batch_dir)
                        os.makedirs(temp_batch_dir)
                        for f in batch_files:
                            shutil.copy(os.path.join(source_path, f), temp_batch_dir)

                        job_for_batch = copy.deepcopy(job)
                        job_for_batch['source_path'] = temp_batch_dir

                        final_config = self._build_final_config_for_job(job_for_batch)
                        is_verbose = settings.get("enable_verbose_output", False)
                        
                        batch_success = self.pipeline.run(job_for_batch, final_output_path, final_config, self.log, is_verbose, output_format)
                        shutil.rmtree(temp_batch_dir)

                        if not batch_success:
                            success = False
                            break
                else:  # High VRAM Mode
                    self.log("PIPELINE", f"Resuming job '{job['name']}' in High VRAM Mode.")

                    temp_source_dir = os.path.join(self.temp_dir, "high_vram_processing")
                    if os.path.exists(temp_source_dir): shutil.rmtree(temp_source_dir)
                    os.makedirs(temp_source_dir)
                    for f in files_to_process:
                        shutil.copy(os.path.join(source_path, f), temp_source_dir)

                    job_for_run = copy.deepcopy(job)
                    job_for_run['source_path'] = temp_source_dir

                    final_config = self._build_final_config_for_job(job_for_run)
                    is_verbose = settings.get("enable_verbose_output", False)
                    success = self.pipeline.run(job_for_run, final_output_path, final_config, self.log, is_verbose, output_format)
                    shutil.rmtree(temp_source_dir)

                job['status'] = "Completed" if success else ("Stopped" if self._stopped_by_user else "Failed")

                if not success and not self._stopped_by_user:
                    QTimer.singleShot(0, lambda j=job: QMessageBox.critical(self, "Job Failed", f"The job '{j['name']}' failed due to a critical error.\n\nCheck the Live Log for details."))

                self.job_queue.remove(job)
                self.history_queue.append(job)
                self.currently_processing_job_id = None
                self._update_job_list_ui()
                self._update_history_list_ui()

                if self._stopped_by_user:
                    self.log("PIPELINE", "Pipeline stopped by user command.")
                    break
        finally:
            self.pipeline_finished_signal.emit()

    def _stop_pipeline(self):
        """Stops the running pipeline process immediately and updates the UI."""
        if not self.is_running_pipeline:
            return

        self.log("PIPELINE", "Stop command received. Terminating backend process...")

        # --- GÜNCELLEME: Set the flag BEFORE stopping the process ---
        self._stopped_by_user = True

        # The pipeline object will handle the actual process killing.
        self.pipeline.stop(self.log)

    def _toggle_ui_state(self, is_running: bool, running_job_id: str = None):
        """
        Locks ONLY the essential UI elements during processing.
        - Toggles Start/Stop buttons.
        - Disables the specific list item being processed.
        - The rest of the UI remains interactive.
        """
        self.is_running_pipeline = is_running

        # 1. Toggle Start/Stop buttons
        self.start_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)

        # 2. Find and visually lock/unlock the specific job item in the queue
        for i in range(self.queue_list_widget.count()):
            item = self.queue_list_widget.item(i)
            # If a job is running and its ID matches this item's ID
            if is_running and item.data(Qt.ItemDataRole.UserRole) == running_job_id:
                # Disable interaction (can't be selected, moved, or right-clicked)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            else:
                # Ensure all other items are fully enabled
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)

    def _set_settings_panel_enabled(self, is_enabled: bool):
        """Helper function to enable or disable all widgets in the settings panel."""
        interactive_widget_types = (QPushButton, QComboBox, QCheckBox, QSlider, QLineEdit)

        if hasattr(self, 'settings_tab_view'):
            # CORRECTED LOGIC: Loop through each type and call findChildren separately.
            for widget_type in interactive_widget_types:
                # Find all widgets of a specific type within the settings area
                for widget in self.settings_tab_view.findChildren(widget_type):
                    widget.setEnabled(is_enabled)

    def _update_progress(self, percent: float, text: str):
        """Thread-safe method to update the progress bar and label."""
        self.progress_bar.setValue(int(percent * 100))
        self.progress_label.setText(text)

    def _reset_task_settings(self, task_key: str):
        """Resets the settings of a specific task to its defaults from tasks.json."""
        if task_key not in self.task_settings:
            return

        task_info = self.config_loader.tasks_config.get(task_key, {})
        defaults = task_info.get("defaults", {})

        # Update the settings dictionary
        self.task_settings[task_key] = defaults.copy()

        # Update the widgets on the UI
        for setting_key, default_value in defaults.items():
            widget = self.task_widgets.get(task_key, {}).get(setting_key)
            if widget:
                # We must block signals here as well to prevent loops
                widget.blockSignals(True)
                self._set_widget_value(setting_key, default_value, widget)
                widget.blockSignals(False)

        self.log("INFO", f"Settings for task '{task_info.get('label')}' have been reset.")

    def _assign_task_to_selection(self, task_key: str):
        """Applies a special task's configuration and type to all selected jobs."""
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Job Selected", "Please select one or more jobs from the queue to assign this task.")
            return

        task_info = self.config_loader.tasks_config.get(task_key, {})
        task_settings_from_ui = self.task_settings.get(task_key, {})

        job_type_map = {'raw_output': 'R', 'upscale': 'U', 'colorize': 'C'}
        job_type = job_type_map.get(task_key, '?')

        for item in selected_items:
            job_id = item.data(Qt.ItemDataRole.UserRole)
            job_data = next((job for job in self.job_queue if job['id'] == job_id), None)
            if job_data:
                current_job_settings = task_settings_from_ui.copy()

                if task_key == 'upscale':
                    # Get value from our special grid widget
                    upscale_value_str = current_job_settings.pop('task_upscale_grid', '2x')
                    # Save it under the key the backend expects ('upscale_ratio')
                    current_job_settings['upscale_ratio'] = int(upscale_value_str.replace('x', ''))

                if task_key == 'colorize' and current_job_settings.get('restore_size_after_colorize'):
                    try:
                        source_dir = job_data['source_path']
                        first_image_name = next((f for f in os.listdir(source_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))), None)

                        if first_image_name:
                            image_path = os.path.join(source_dir, first_image_name)
                            with Image.open(image_path) as img:
                                width, height = img.size

                            original_long_side = max(width, height)
                            target_colorize_size = int(current_job_settings.get('colorization_size', 576))

                            if target_colorize_size > 0 and original_long_side > target_colorize_size:
                                division_ratio = original_long_side / target_colorize_size
                                calculated_upscale_ratio = max(2, round(division_ratio))

                                current_job_settings['upscale_ratio'] = calculated_upscale_ratio
                                current_job_settings['revert_upscaling'] = False
                                self.log("INFO", f"Job '{job_data['name']}': Auto-calculated upscale ratio: {calculated_upscale_ratio}x")
                        else:
                            self.log("WARNING", f"Job '{job_data['name']}': Could not find an image to calculate upscale ratio. Skipping auto-upscale.")

                    except Exception as e:
                        self.log("ERROR", f"Failed to auto-calculate upscale ratio for '{job_data['name']}': {e}")

                device_widget = self.tasks_processing_device_widget
                button_group = device_widget.findChild(QButtonGroup)
                selected_device = "CPU"
                if button_group and button_group.checkedButton():
                    selected_device = button_group.checkedButton().text()
                
                current_job_settings['processing_device'] = selected_device

                current_job_settings['processing_mode'] = self._get_value_from_widget('processing_mode', self.setting_widgets.get('processing_mode'))
                current_job_settings['batch_size'] = self._get_value_from_widget('batch_size', self.setting_widgets.get('batch_size'))

                job_data['settings'] = current_job_settings
                job_data['job_type'] = job_type
                job_data['status'] = 'Ready'

        self.log("INFO", f"Assigned task '{task_info.get('label')}' to {len(selected_items)} job(s).")
        self._update_job_list_ui()

    def _on_pipeline_finished(self):
        """
        A dedicated, thread-safe function to call when the pipeline finishes.
        This centralizes the UI reset logic.
        """
        self.is_running_pipeline = False
        self.currently_processing_job_id = None
        self._update_progress(1.0, "Finished!")
        # A brief delay before unlocking allows the progress bar to show "Finished!"
        QTimer.singleShot(100, lambda: self._toggle_ui_state(False))
        QTimer.singleShot(2000, lambda: self._update_progress(0, "Ready"))

    def closeEvent(self, event):
        """Handles the window close event to save the application state."""
        if self.is_running_pipeline:
            reply = QMessageBox.question(self, "Confirm Exit",
                                         "A process is still running. Are you sure you want to stop it and exit?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self._stop_pipeline()
            else:
                event.ignore()
                return

        self._save_app_state()
        event.accept()

    def _load_app_state(self):
        """Loads application state (window geometry, last directory) from a config file."""
        self.app_settings_path = os.path.join(self.project_base_dir, "MangaStudio_Data", "studio_config.json")
        try:
            if os.path.exists(self.app_settings_path):
                with open(self.app_settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # Restore window geometry
                geometry_hex = settings.get("window_geometry")
                if geometry_hex:
                    self.restoreGeometry(QByteArray.fromHex(geometry_hex.encode('utf-8')))

                # Restore last used directory
                self.last_selected_directory = settings.get("last_directory")
                print("[INFO] Application state loaded.")
        except Exception as e:
            print(f"[WARNING] Could not load app settings: {e}")

    def _save_app_state(self):
        """Saves the current application state to a config file."""
        if not hasattr(self, 'app_settings_path'):
            self.app_settings_path = os.path.join(self.project_base_dir, "MangaStudio_Data", "studio_config.json")

        settings = {
            # Convert QByteArray to a JSON-compatible hex string
            "window_geometry": self.saveGeometry().toHex().data().decode('utf-8'),
            "last_directory": getattr(self, 'last_selected_directory', None)
        }
        try:
            with open(self.app_settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            print("[INFO] Application state saved.")
        except Exception as e:
            print(f"[ERROR] Could not save app settings: {e}")

    def _create_theme_manager_widget(self) -> QWidget:
        """Creates the UI component for theme selection."""
        theme_frame = QFrame()
        theme_layout = QVBoxLayout(theme_frame)
        theme_layout.setContentsMargins(0, 10, 0, 0)

        label = QLabel("Appearance & Theme")
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        theme_layout.addWidget(label)

        # A sub-frame for the actual controls
        controls_frame = QWidget()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("Select Theme ⚠⚠⚠")
        label.setToolTip(
            "Note:\n"
            "Selected button colors\n"
            "might not be styled correctly\n"
            "when using themes.\n"
            "Default: Default Qt"
        )
        controls_layout.addWidget(label)

        self.theme_combobox = SearchableComboBox()
        self.theme_combobox.setToolTip("Changes the visual appearance of the application. Default: Default Qt")
        self._load_themes()  # Populate the combobox
        self.theme_combobox.setCurrentText("Default Qt")  # Set Default Qt as initial theme
        self.theme_combobox.currentTextChanged.connect(self._apply_theme)

        controls_layout.addWidget(self.theme_combobox, stretch=1)
        theme_layout.addWidget(controls_frame)

        return theme_frame

    def _load_themes(self):
        """Scans the themes directory and populates the theme combobox."""
        self.available_themes.clear()
        themes_dir = os.path.join(self.project_base_dir, "MangaStudio_Data", "themes")

        # Add a special option to revert to the default style
        self.available_themes["Default Qt"] = {"name": "Default Qt", "style": {}}

        if not os.path.isdir(themes_dir):
            # Even if folder not found, still allow reverting to default
            self.theme_combobox.addItems(sorted(self.available_themes.keys()))
            return

        for filename in os.listdir(themes_dir):
            if filename.endswith(".json"):
                try:
                    filepath = os.path.join(themes_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                        theme_name = theme_data.get("name", filename)
                        self.available_themes[theme_name] = theme_data
                except Exception as e:
                    print(f"Warning: Could not load theme file {filename}. Error: {e}")

        self.theme_combobox.addItems(sorted(self.available_themes.keys()))

    def _apply_theme(self, theme_name: str):
        """
        Applies the selected theme's stylesheet to the entire application,
        with detailed styling for interactive widget states.
        """
        font_size_text = self.font_scale_combobox.currentText()
        percentage = int(font_size_text.split('%')[0])
        base_font_size = 10
        font_size = f"{base_font_size * (percentage / 100.0)}pt"

        if theme_name == "Default Qt":
            minimal_style = f"""
                QWidget {{ font-size: {font_size}; }}
                QPushButton {{
                    background-color: #f0f0f0;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                    padding: 5px;
                    border-radius: 3px;
                }}
                QPushButton:hover {{
                    background-color: #e0e0e0;
                }}
                QPushButton:checked {{
                    background-color: #3a7ebf;
                    color: white;
                    border: 2px solid #3a7ebf;
                    font-weight: bold;
                }}
                QPushButton:checked:hover {{
                    background-color: #2c5e8f;
                    border: 2px solid #2c5e8f;
                    color: white;
                }}
            """
            self.setStyleSheet(minimal_style)
            self.log("INFO", "Reverted to default Qt theme.")
            return

        theme_data = self.available_themes.get(theme_name)
        if not theme_data or "style" not in theme_data:
            return

        colors = theme_data["style"].get("colors", {})
        # Get all colors with fallbacks
        bg_main = colors.get("background_main", "#2d2d2d")
        bg_frame = colors.get("background_frame", "#2d2d2d")
        btn_primary = colors.get("primary_button", "#3a7ebf")
        btn_hover = colors.get("primary_button_hover", "#56a9e8")
        slider_groove = colors.get("slider_groove", "#242424")
        slider_handle = colors.get("slider_handle", "#3a7ebf")
        txt_main = colors.get("text_main", "#dce4ee")
        border = colors.get("border", "#555555")
        accent = colors.get("accent", "#4a9fcf")
        indicator = colors.get("checkbox_indicator", "#dce4ee")

        style_sheet = f"""
            /* --- GLOBAL --- */
            QWidget {{
                font-size: {font_size};
                background-color: {bg_main};
                color: {txt_main};
            }}
            /* --- FRAMES & PANELS --- */
            QFrame#StyledPanel, QFrame#LeftPanel {{
                background-color: {bg_frame};
                border: 1px solid {border};
                border-radius: 5px;
            }}
            /* --- PUSH BUTTONS --- */
            QPushButton {{
                background-color: {btn_primary};
                color: {txt_main};
                border: 1px solid {border};
                padding: 5px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
            QPushButton:checked {{
                background-color: {accent};
                color: white;
                border: 2px solid {accent};
            }}
            QPushButton:checked:hover {{
                background-color: {accent};
                border: 2px solid {accent};
                color: white;
            }}
            QPushButton:disabled {{ background-color: #555555; color: #888888; }}
            
            /* --- COMBOBOX & LINEEDIT --- */
            QComboBox, QLineEdit {{
                background-color: {bg_main};
                border: 1px solid {border};
                padding: 2px;
            }}
            QComboBox::drop-down {{ border: none; }}
            /* QComboBox::down-arrow {{ image: url(./path/to/your/arrow.png); }} */

            /* --- CHECKBOX --- */
            QCheckBox::indicator {{
            width: 14px;
            height: 14px;
            border: 1px solid {border};
            border-radius: 3px;
            }}
            QCheckBox::indicator:unchecked {{ 
                background-color: {bg_main}; 
            }}
            QCheckBox::indicator:checked {{
                background-color: {accent};
                border-color: {accent};
            }}

            /* --- SLIDERS --- */
            QSlider::groove:horizontal {{
                border: 1px solid {border};
                background: {slider_groove};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {slider_handle};
                border: 1px solid {slider_handle};
                width: 14px;
                margin: -6px 0; 
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {btn_hover};
                border: 1px solid {btn_hover};
            }}
            /* --- LIST WIDGET & TEXT EDIT --- */
            QListWidget, QTextEdit {{
                background-color: {bg_main};
                color: {txt_main};
                border: 1px solid {border};
                border-radius: 3px;
            }}
            /* --- TAB WIDGET --- */
            QTabWidget::pane {{
                background-color: {bg_main};
                border: 1px solid {border};
                border-radius: 5px;
            }}
            QTabBar::tab {{
                background: {bg_main};
                padding: 6px;
                border: 1px solid {border};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background: {bg_frame};
                color: {txt_main};
                border-bottom: 1px solid {bg_frame}; /* Hide bottom border */
            }}
            QTabBar::tab:!selected {{
                background: {bg_main};
                color: {txt_main};
            }}
            QTabBar::tab:!selected:hover {{
                background: {bg_frame};
            }}
            /* --- TOOLTIP --- */
            QToolTip {{
                color: {txt_main};
                background-color: {bg_frame};
                border: 1px solid {border};
            }}
        """

        self.setStyleSheet(style_sheet)
        self.log("INFO", f"Theme '{theme_name}' applied successfully.")

    def _show_queue_context_menu(self, position):
        """Creates and shows the context menu for the queue list with Checkpoint logic."""
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            return

        menu = QMenu()

        # Action 1: Save settings TO the job
        save_action = menu.addAction("✅ Save Settings to Job (Checkpoint)")
        save_action.triggered.connect(self._save_settings_to_job)

        # Action 2: Load settings FROM the job
        load_action = menu.addAction("✏️ Load Job Settings to Panel")
        if len(selected_items) != 1:
            load_action.setDisabled(True)
            load_action.setToolTip("Select only one job to load its settings.")
        load_action.triggered.connect(self._load_settings_from_job)

        menu.addSeparator()

        # Action 3: Duplicate Job
        duplicate_action = menu.addAction("➕ Duplicate Job (as new task)")
        duplicate_action.triggered.connect(self._duplicate_selected_jobs)

        # Action 4: Remove
        remove_action = menu.addAction("🗑️ Remove from Queue")
        remove_action.triggered.connect(self._remove_selected_jobs_from_queue)

        menu.exec(self.queue_list_widget.mapToGlobal(position))

    def _apply_settings_to_selection(self):
        """Applies the main configuration from the 'Configuration' tabs to the selected jobs."""
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            job_id = item.data(Qt.ItemDataRole.UserRole)
            job_data = next((job for job in self.job_queue if job['id'] == job_id), None)
            if job_data:
                # Assign settings from the main config tabs
                job_data['settings'] = self.current_settings.copy()
                job_data['status'] = 'Ready'
                job_data['job_type'] = 'T'

        self.log("INFO", f"Applied 'Translate [T]' settings to {len(selected_items)} job(s).")
        self._update_job_list_ui()

    def _remove_selected_jobs_from_queue(self):
        """Removes all selected jobs from the queue."""
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            return

        ids_to_remove = {item.data(Qt.ItemDataRole.UserRole) for item in selected_items}

        # Rebuild the job_queue, excluding the jobs to be removed
        self.job_queue = [job for job in self.job_queue if job['id'] not in ids_to_remove]

        self.log("INFO", f"Removed {len(ids_to_remove)} job(s) from the queue.")
        # If the currently selected job was removed, clear the selection
        if self.selected_job_id in ids_to_remove:
            self.selected_job_id = None
            self._populate_settings_panel()

        self._update_job_list_ui()

    def _save_settings_to_job(self):
        """Saves the current panel settings to the selected job(s) (Checkpoint)."""
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            return
        
        processing_mode_value = self._get_value_from_widget('processing_mode', self.setting_widgets.get('processing_mode'))
        batch_size_value = self._get_value_from_widget('batch_size', self.setting_widgets.get('batch_size'))
        
        for item in selected_items:
            job_id = item.data(Qt.ItemDataRole.UserRole)
            job = next((j for j in self.job_queue if j['id'] == job_id), None)
            if job:
                job['settings'] = copy.deepcopy(self.current_settings)
                job['status'] = 'Ready'
                # If the job has no type, default it to 'Translate'
                if not job.get('job_type'):
                    job['job_type'] = 'T'

        self._update_job_list_ui()
        self.log("SUCCESS", f"Checkpoint created. Saved settings to {len(selected_items)} job(s).")

    def _load_settings_from_job(self):
        """Loads a selected job's settings back into the main panel for editing."""
        selected_items = self.queue_list_widget.selectedItems()
        # This action should only work when a single job is selected
        if len(selected_items) != 1:
            return

        job_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        job = next((j for j in self.job_queue if j['id'] == job_id), None)

        if job:
            # Load the job's settings into the main panel
            self.current_settings = copy.deepcopy(job['settings'])
            self._populate_settings_panel()
            self.log("INFO", f"Loaded settings from '{job['name']}' into the panel for editing.")

    def _create_api_manager_widget(self, info: dict) -> QWidget:
        """Creates a self-contained widget for the API key manager button."""
        container = QFrame()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 10, 0, 0)

        label = QLabel(info.get("label", "API Keys:"))
        layout.addWidget(label)
        layout.addStretch()

        button = QPushButton("Create / Open keys.yaml File")
        button.setToolTip(info.get("tooltip", "Click to manage your API keys."))
        button.clicked.connect(self._handle_create_keys_file)
        layout.addWidget(button)

        return container

    def _handle_create_keys_file(self):
        """Checks for, creates, and opens the keys.yaml file in the .config directory."""
        keys_dir = os.path.join(self.project_base_dir, ".config")
        os.makedirs(keys_dir, exist_ok=True)
        keys_path = os.path.join(keys_dir, "keys.yaml")
        self.log("INFO", f"Managing keys.yaml file at: {keys_path}")

        # The list of API keys and related settings for the template (YAML format)
        KEYS_TEMPLATE = [
            "# --- Baidu Translate ---",
            "BAIDU_APP_ID: \"\"",
            "BAIDU_SECRET_KEY: \"\"",
            "\n# --- Youdao Translate ---",
            "YOUDAO_APP_KEY: \"\"",
            "YOUDAO_SECRET_KEY: \"\"",
            "\n# --- DeepL Translate ---",
            "DEEPL_AUTH_KEY: \"\"",
            "\n# --- Caiyun Translate ---",
            "CAIYUN_TOKEN: \"\"",
            "\n# --- OpenAI ---",
            "OPENAI_API_KEY: \"\"",
            "OPENAI_MODEL: \"gpt-4o\"",
            "OPENAI_API_BASE: \"https://api.openai.com/v1\"",
            "OPENAI_HTTP_PROXY: \"\"",
            "OPENAI_GLOSSARY_PATH: \"./dict/mit_glossary.txt\"",
            "\n# --- Groq ---",
            "GROQ_API_KEY: \"\"",
            "GROQ_MODEL: \"mixtral-8x7b-32768\"",
            "\n# --- Gemini ---",
            "GEMINI_API_KEY: \"\"",
            "GEMINI_MODEL: \"gemini-1.5-flash\"",
            "\n# --- DeepSeek ---",
            "DEEPSEEK_API_KEY: \"\"",
            "DEEPSEEK_MODEL: \"deepseek-chat\"",
            "DEEPSEEK_API_BASE: \"https://api.deepseek.com\"",
            "\n# --- Sakura Translator ---",
            "SAKURA_API_BASE: \"http://127.0.0.1:8080/v1\"",
            "SAKURA_DICT_PATH: \"./dict/sakura_dict.txt\"",
            "\n# --- Custom OpenAI (Ollama, etc.) ---",
            "CUSTOM_OPENAI_API_KEY: \"ollama\"",
            "CUSTOM_OPENAI_MODEL: \"\"",
            "CUSTOM_OPENAI_API_BASE: \"http://localhost:11434/v1\"",
        ]

        try:
            if not os.path.exists(keys_path):
                self.log("INFO", "keys.yaml file not found. Creating a new template...")
                with open(keys_path, 'w', encoding='utf-8') as f:
                    f.write("# This file stores your API keys and configuration parameters.\n")
                    f.write("# Place your keys below. Do NOT share this file with anyone.\n\n")
                    f.write("\n".join(KEYS_TEMPLATE))

            # Open the file with the default system application
            if sys.platform == "win32":
                os.startfile(keys_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", keys_path])
            else:  # linux
                subprocess.run(["xdg-open", keys_path])

        except Exception as e:
            error_msg = f"Could not open the keys.yaml file. Please open it manually.\nPath: {keys_path}\nError: {e}"
            self.log("ERROR", error_msg)
            QMessageBox.warning(self, "Could Not Open File", error_msg)

    def _requeue_job(self):
        """Moves the selected job(s) from the history back to the queue for another run."""
        selected_items = self.history_list_widget.selectedItems()
        if not selected_items:
            return

        # Process the list in reverse to avoid index issues with multiple selections
        for item in reversed(selected_items):
            job_id_to_requeue = item.data(Qt.ItemDataRole.UserRole)
            job_to_move = next((job for job in self.history_queue if job['id'] == job_id_to_requeue), None)

            if job_to_move:
                # Remove from history
                self.history_queue.remove(job_to_move)

                # IMPORTANT: Reset status to 'Ready' so it can be processed again,
                # but keep its settings and job type intact.
                job_to_move['status'] = 'Ready'

                # Add to the end of the job queue
                self.job_queue.append(job_to_move)

        # Update both UI lists to reflect the change
        self._update_history_list_ui()
        self._update_job_list_ui()

        self.log("INFO", f"Re-queued {len(selected_items)} job(s) from history.")

    def _show_history_context_menu(self, position):
        """Creates and shows the context menu for the history list."""
        selected_items = self.history_list_widget.selectedItems()
        if not selected_items:
            return

        menu = QMenu()

        # Action to re-queue the job
        requeue_action = menu.addAction("↪️ Re-queue Job")
        requeue_action.setToolTip("Moves the selected job(s) back to the queue with their last used settings.")
        requeue_action.triggered.connect(self._requeue_job)

        menu.exec(self.history_list_widget.mapToGlobal(position))

    def _build_font_map(self):
        """Scans the project's /fonts folder to create a name-to-filepath map."""
        self.font_map = {}
        fonts_dir = os.path.join(self.project_base_dir, "fonts")
        
        if not os.path.isdir(fonts_dir):
            print(f"[WARNING] Fonts directory not found at: {fonts_dir}")
            return

        for font_file in sorted(os.listdir(fonts_dir)):
            if font_file.lower().endswith(('.ttf', '.otf')):
                font_path = os.path.join(fonts_dir, font_file)
                # Use the filename as the key
                self.font_map[font_file] = font_path

    def _create_font_combobox(self, info: dict) -> QComboBox:
        """Creates a combobox populated with fonts from the project's /fonts folder."""
        combo_box = SearchableComboBox()
        
        font_names = list(self.font_map.keys())
        
        if font_names:
            combo_box.addItems(font_names)
        else:
            combo_box.addItem("No fonts found in /fonts folder")
            combo_box.setEnabled(False)

        # Try to set the default font, otherwise select the first one
        default_font = info.get("default", "")
        if default_font in font_names:
            combo_box.setCurrentText(default_font)
        elif font_names:
            combo_box.setCurrentIndex(0)
            
        return combo_box
    
        