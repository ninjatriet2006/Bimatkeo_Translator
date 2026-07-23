"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.main_window
- RESPONSIBILITY: main_window.py module logic.
- CALLED BY: Various
- CALLS TO: Various
- IN = OUT: Defines logic for app.core.desktop.main_window.
=============================================================================
"""
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
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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

from app.core.desktop.config import ConfigLoader

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


class TranslatorStudioApp(WidgetBuildersMixin, JobRunnerMixin, HandlersMixin, QMainWindow):

    log_signal = Signal(str, str)
    pipeline_finished_signal = Signal()
    pipeline_progress_signal = Signal(int, int, str)
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
        self.project_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        self.config_loader = ConfigLoader(self.project_base_dir)
        self.app_logger = AppLogger(self.config_loader, self)
        
        # Verify language files (reports missing/orphan keys to standard logger)
        self.config_loader.language_manager.run_verification(self.config_loader.ui_map, target_lang=getattr(self.config_loader, 'app_language', 'en'))
        
        # Verify models (reports missing/orphan models to standard logger)
        try:
            from app.core.translator.verify import TranslatorVerifier
            from app.core.ocr.verify import OCRVerifier
            from app.core.inpainter.verify import InpainterVerifier
            from app.core.renderer.verify import RendererVerifier
            from app.core.diffusion.verify import DiffusionVerifier
            
            TranslatorVerifier().run_verification()
            OCRVerifier().run_verification()
            InpainterVerifier().run_verification()
            RendererVerifier().run_verification()
            DiffusionVerifier().run_verification()
        except Exception as e:
            self.app_logger.log_signal.emit("WARNING", f"Failed to run model verifications: {e}")
        
        # Update LANGUAGES dynamically from the backend if loaded
        if hasattr(self.config_loader, 'languages') and self.config_loader.languages:
            global LANGUAGES
            LANGUAGES.clear()
            LANGUAGES.update(self.config_loader.languages)

        # Update TRANSLATOR_GROUPS dynamically from the custom values
        offline_list = self.config_loader.translator_groups.get(CAT_OFFLINE_MODELS, [])
        api_list = self.config_loader.translator_groups.get(CAT_API_BASED, [])

        global TRANSLATOR_GROUPS, LOG_COLORS
        TRANSLATOR_GROUPS.clear()
        
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
        self.detected_vram_gb = 0.0
        def check_vram_background():
            self.log("INFO", "Checking available VRAM...")
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
                            self.log("SUCCESS", f"Detected {self.detected_vram_gb:.2f} GB of VRAM via subprocess.")
                            from PySide6.QtCore import QTimer
                            QTimer.singleShot(0, lambda: self._update_gpu_status_ui(True))
                        else:
                            self.log("SUCCESS", "No dedicated NVIDIA VRAM detected. Using Safe mode defaults.")
                            from PySide6.QtCore import QTimer
                            QTimer.singleShot(0, lambda: self._update_gpu_status_ui(False))
            except Exception as e:
                self.log("WARNING", f"Could not detect VRAM. Automatic mode will default to Safe. Error: {e}")
                from PySide6.QtCore import QTimer
                QTimer.singleShot(0, lambda: self._update_gpu_status_ui(False))

        threading.Thread(target=check_vram_background, daemon=True).start()

        # --- Pipeline for backend processing ---
        self.temp_dir = os.path.join(self.project_base_dir, "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        # Pipeline is instantiated lazily inside background workers to save 15s of startup time.


        self._initialize_app()
        # Connect custom signals to their slots
        self.pipeline_finished_signal.connect(self._on_pipeline_finished)
        self.pipeline_progress_signal.connect(self._update_progress_bar)
        self.visual_test_finished_signal.connect(self._on_visual_test_finished)
        self.visual_test_result_signal.connect(self._display_test_result)
        # Apply saved theme if exists
        saved_theme = self.config_loader.oldsession_config.get("theme", "Default Qt")
        self._apply_theme(saved_theme)
        self._on_translator_category_changed()
        self._on_ocr_category_changed()
        self._update_inpainter_visibility()

    def _update_gpu_status_ui(self, has_gpu: bool):
        processing_widget = getattr(self, 'setting_widgets', {}).get('processing_device')
        if processing_widget:
            from PySide6.QtWidgets import QPushButton
            for button in processing_widget.findChildren(QPushButton):
                if button.property("internal_id") == "cuda":
                    current_text = button.text()
                    if not has_gpu:
                        if "(Unavailable)" not in current_text:
                            button.setText(f"{current_text} (Unavailable)")
                            button.setEnabled(False)
                            if button.isChecked():
                                for b in processing_widget.findChildren(QPushButton):
                                    if b.property("internal_id") == "cpu":
                                        b.setChecked(True)
                                        # Also update the settings dict
                                        if hasattr(self, 'current_settings'):
                                            self.current_settings['processing_device'] = 'cpu'
                                        break
                    else:
                        if "(Unavailable)" in current_text:
                            button.setText(current_text.replace(" (Unavailable)", ""))
                        button.setEnabled(True)

    def get_string(self, string_id: str, **kwargs) -> str:
        """
        Helper method to get translated strings.
        Delegates to LanguageManager using the current app_language.
        """
        if hasattr(self, 'config_loader') and hasattr(self.config_loader, 'app_language'):
            lang_id = self.config_loader.app_language
            return self.config_loader.language_manager.get_string(lang_id, string_id, **kwargs)
        return string_id

    def get_ui_string(self, category: str, string_id: str, sub_key: str | None = None) -> str:
        if hasattr(self, 'config_loader') and hasattr(self.config_loader, 'app_language'):
            lang_id = self.config_loader.app_language
            return self.config_loader.language_manager.get_ui_string(lang_id, category, string_id, sub_key)
        return string_id

    def update_language_ui(self):
        """Dynamically update UI text for all widgets using ID linking."""
        def walk_widget(w):
            lang_id = w.property("lang_id")
            if lang_id:
                lang_type = w.property("lang_type")
                if not lang_type:
                    lang_type = "ui" if str(lang_id).startswith("ui_") else "settings"
                
                if lang_type == "settings":
                    new_text = self.get_ui_string("settings", lang_id, "label")
                elif lang_type == "enums":
                    new_text = self.get_ui_string("enums", lang_id)
                else:
                    new_text = self.get_string(lang_id)
                    
                if new_text and new_text != lang_id:
                    args = w.property("lang_args")
                    if args is not None and isinstance(args, list):
                        new_text = new_text.format(*args)

                    if hasattr(w, 'setText'):
                        w.setText(new_text)
                    elif hasattr(w, 'setTitle'):
                        w.setTitle(new_text)
            
            tooltip_lang_id = w.property("tooltip_lang_id")
            if tooltip_lang_id:
                lang_type = w.property("tooltip_lang_type")
                if not lang_type:
                    lang_type = "ui" if str(tooltip_lang_id).startswith("ui_") else "settings"
                    
                if lang_type == "settings":
                    new_tooltip = self.get_ui_string("settings", tooltip_lang_id, "tooltip")
                    label_text = self.get_ui_string("settings", tooltip_lang_id, "label")
                    if label_text == tooltip_lang_id:
                        label_text = "Settings" # generic fallback if no label
                else:
                    new_tooltip = self.get_string(tooltip_lang_id)
                    label_text = ""
                    
                if new_tooltip and new_tooltip != tooltip_lang_id:
                    args = w.property("tooltip_lang_args")
                    if args is not None and isinstance(args, list):
                        new_tooltip = new_tooltip.format(*args)

                    if hasattr(w, 'setToolTip'):
                        if lang_type == "settings" and label_text:
                            w.setToolTip(f"<b>{label_text}</b><hr>{new_tooltip}")
                        else:
                            w.setToolTip(new_tooltip)

            # Also update tabs
            if isinstance(w, QTabWidget):
                tab_ids = w.property("tab_lang_ids")
                if tab_ids:
                    for i, t_id in enumerate(tab_ids):
                        new_text = self.get_string(t_id)
                        if new_text and new_text != t_id:
                            w.setTabText(i, new_text)

            for child in w.children():
                from PySide6.QtWidgets import QWidget
                if isinstance(child, QWidget):
                    walk_widget(child)

        walk_widget(self)
        
        # Update dynamic zoom label explicitly
        if hasattr(self, 'zoom_label'):
            zoom = getattr(self.preview_image, 'current_zoom', 1.0) if hasattr(self, 'preview_image') else 1.0
            zoom_text = self.get_string("ui_zoom")
            if zoom_text and zoom_text != "ui_zoom":
                self.zoom_label.setText(f"{zoom_text} {zoom * 100:.0f}%")

    def _initialize_app(self):
        """
        Sets up the main window, its properties, and creates the main layout.
        """
        self.log("INFO", "Initializing PySide6 application window...")
        self.setWindowTitle(self.get_string("ui_app_title") if self.get_string("ui_app_title") != "ui_app_title" else "🎌 Bimatkeo Translator - PySide")
        self.setProperty("lang_id", "ui_app_title")
        self.setProperty("lang_type", "ui")
        self.resize(1280, 720)
        self.setMinimumSize(QSize(960, 540))
        self._create_main_layout()
        
        self._update_job_list_ui()
        self._update_history_list_ui()
        
        # Ensure ID linking translations run at startup for hardcoded UI elements
        if hasattr(self, 'update_language_ui'):
            self.update_language_ui()
            
        self.log("SUCCESS", "Main layout and dynamic widgets created successfully.")

    def _create_main_layout(self):
        """Creates the main QWidget and layouts to structure the window."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Build underlying widgets and wrap them in standalone windows
        self._build_auxiliary_windows()

        # Top Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(10)
        
        btn_queue = QPushButton("📋 Job Queue")
        btn_log = QPushButton("📜 Console Log")
        btn_history = QPushButton("🕒 History")
        btn_preview = QPushButton("🔍 Preview Tester")
        btn_standalone_trans = QPushButton("🌐 Translator Tool")
        btn_standalone_ocr = QPushButton("📝 OCR Tool")
        btn_standalone_inpaint = QPushButton("🖌️ Inpaint Tool")
        btn_standalone_diffusion = QPushButton("✨ Diffusion Tool")
        btn_standalone_render = QPushButton("🎨 Render Tool")
        btn_close_all_standalone = QPushButton("❌ Close Standalones")
        
        btn_queue.clicked.connect(lambda: self._show_standalone_window(self.queue_window))
        btn_log.clicked.connect(lambda: self._show_standalone_window(self.log_window))
        btn_history.clicked.connect(lambda: self._show_standalone_window(self.history_window))
        btn_preview.clicked.connect(lambda: self._show_standalone_window(self.preview_window))
        btn_standalone_trans.clicked.connect(lambda: self.launch_standalone_tool("translator", btn_standalone_trans))
        btn_standalone_ocr.clicked.connect(lambda: self.launch_standalone_tool("ocr", btn_standalone_ocr))
        btn_standalone_inpaint.clicked.connect(lambda: self.launch_standalone_tool("inpaint", btn_standalone_inpaint))
        btn_standalone_diffusion.clicked.connect(lambda: self.launch_standalone_tool("diffusion", btn_standalone_diffusion))
        btn_standalone_render.clicked.connect(lambda: self.launch_standalone_tool("render", btn_standalone_render))
        btn_close_all_standalone.clicked.connect(self.close_all_standalones)

        toolbar_layout.addWidget(btn_queue)
        toolbar_layout.addWidget(btn_log)
        toolbar_layout.addWidget(btn_history)
        toolbar_layout.addWidget(btn_preview)
        toolbar_layout.addWidget(btn_standalone_trans)
        toolbar_layout.addWidget(btn_standalone_ocr)
        toolbar_layout.addWidget(btn_standalone_inpaint)
        toolbar_layout.addWidget(btn_standalone_diffusion)
        toolbar_layout.addWidget(btn_standalone_render)
        toolbar_layout.addWidget(btn_close_all_standalone)
        toolbar_layout.addStretch()

        # Main Studio Settings is now the core central area
        settings_panel = self._create_settings_tab_container()

        bottom_panel = self._create_bottom_panel()

        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(settings_panel, stretch=1)
        main_layout.addWidget(bottom_panel)

    def launch_standalone_tool(self, tool_name: str, button=None):
        import subprocess
        import sys
        import os
        from PySide6.QtCore import QTimer
        
        script_map = {
            "translator": "translator_widget.py",
            "ocr": "ocr_widget.py",
            "inpaint": "inpaint_widget.py",
            "diffusion": "diffusion_widget.py",
            "render": "render_widget.py"
        }
        script_name = script_map.get(tool_name)
        if not script_name:
            self.log("ERROR", f"Unknown standalone tool: {tool_name}")
            return
            
        script_path = os.path.join(self.project_base_dir, "app", "core", "desktop", "components", "standalone", script_name)
        python_exe = getattr(self.config_loader, 'python_executable', sys.executable)
        
        reset_btn = None
        if button:
            original_text = button.text()
            button.setText("Loading...")
            button.setEnabled(False)
            
            reset_btn_called = [False]
            def reset_btn_func():
                if not reset_btn_called[0]:
                    reset_btn_called[0] = True
                    button.setText(original_text)
                    button.setEnabled(True)
                
            reset_btn = reset_btn_func
        
        try:
            # Spawn the tool in a completely separate process using module import to fix sys.path
            module_path = f"app.core.desktop.components.standalone.{script_name.replace('.py', '')}"
            import threading
            import platform
            
            kwargs = {}
            if platform.system() == "Windows":
                kwargs['creationflags'] = getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0x00000200)
            else:
                kwargs['start_new_session'] = True
            
            proc = subprocess.Popen(
                [python_exe, "-m", module_path], 
                cwd=self.project_base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                **kwargs
            )
            
            if not hasattr(self, 'standalone_processes'):
                self.standalone_processes = []
            self.standalone_processes.append(proc)
            
            if reset_btn:
                def wait_for_ready():
                    if proc.stdout:
                        for line in iter(proc.stdout.readline, ''):
                            if "STANDALONE_READY" in line:
                                break
                    QTimer.singleShot(0, reset_btn)
                
                threading.Thread(target=wait_for_ready, daemon=True).start()
                
            self.log("INFO", f"Launched standalone tool: {tool_name}")
        except Exception as e:
            self.log("ERROR", f"Failed to launch standalone tool: {e}")
            if reset_btn:
                reset_btn()

    def close_all_standalones(self):
        if not hasattr(self, 'standalone_processes'):
            return
        alive_procs = []
        for proc in self.standalone_processes:
            if proc.poll() is None:
                proc.terminate()
            else:
                alive_procs.append(proc)
        self.standalone_processes = [p for p in self.standalone_processes if p.poll() is None]
        self.log("INFO", "Requested to close all standalone tools.")

    def _show_standalone_window(self, window):
        window.show()
        window.raise_()
        window.activateWindow()

    def _build_auxiliary_windows(self):
        class StandaloneToolWindow(QDialog):
            def __init__(self, parent, title, widget, width=600, height=400):
                super().__init__(parent)
                self.setWindowTitle(title)
                self.setWindowFlags(Qt.WindowType.Window) # Make it act like an independent window
                self.resize(width, height)
                layout = QVBoxLayout(self)
                layout.setContentsMargins(5, 5, 5, 5)
                layout.addWidget(widget)

            def closeEvent(self, event):
                self.hide()
                event.ignore()

        # 1. Queue Window
        queue_widget = self._create_queue_widget()
        self.queue_window = StandaloneToolWindow(self, self.get_string("ui_queue_title") if self.get_string("ui_queue_title") != "ui_queue_title" else "Queue (Next Up)", queue_widget, 400, 600)
        self.queue_window.setProperty("lang_id", "ui_queue_title")
        self.log("SUCCESS", "Job Queue window created.")

        # 2. History Window
        history_widget = self._create_history_widget()
        self.history_window = StandaloneToolWindow(self, self.get_string("ui_history_title") if self.get_string("ui_history_title") != "ui_history_title" else "History (Completed Jobs)", history_widget, 400, 600)
        self.history_window.setProperty("lang_id", "ui_history_title")
        self.log("SUCCESS", "History window created.")

        # 3. Log Window
        self.log_viewer = ConsoleWidget(self)
        self.log_signal.connect(self.log_viewer.insert_log)
        if hasattr(self, 'app_logger'):
            self.app_logger.log_signal.connect(self.log_viewer.insert_log)
            self.app_logger.flush_early_logs()
        self.log_window = StandaloneToolWindow(self, "Console Log", self.log_viewer, 600, 400)
        self.log("SUCCESS", "Console Log window created.")

        # 4. Preview Tester Window
        preview_widget = self._create_preview_tester_tab()
        self.preview_window = StandaloneToolWindow(self, self.get_string("ui_tab_preview_tester") if self.get_string("ui_tab_preview_tester") != "ui_tab_preview_tester" else "Preview Tester", preview_widget, 1000, 700)
        self.preview_window.setProperty("lang_id", "ui_tab_preview_tester")
        self.log("SUCCESS", "Preview Tester window created.")

    def _create_queue_widget(self) -> QWidget:
        queue_frame = QWidget()
        queue_layout = QVBoxLayout(queue_frame)
        queue_layout.setContentsMargins(0, 0, 0, 0)

        self.queue_list_widget = QListWidget()
        self.queue_list_widget.setToolTip("Add folders by clicking 'Add Job' or by dragging and dropping them here.")
        self.queue_list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.queue_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.queue_list_widget.itemSelectionChanged.connect(self._on_job_selection_changed)

        self.queue_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.queue_list_widget.customContextMenuRequested.connect(self._show_queue_context_menu)
        self.queue_list_widget.itemChanged.connect(self._on_queue_item_changed)
        queue_layout.addWidget(self.queue_list_widget)

        job_controls_container = QWidget()
        job_controls_layout = QHBoxLayout(job_controls_container)
        job_controls_layout.setContentsMargins(0, 0, 0, 0)

        add_folder_btn = QPushButton(self.get_string("ui_add_folder") if self.get_string("ui_add_folder") != "ui_add_folder" else "➕ Add Folder")
        add_folder_btn.setProperty("lang_id", "ui_add_folder")
        add_folder_btn.clicked.connect(self._add_job)

        add_file_btn = QPushButton(self.get_string("ui_add_file") if self.get_string("ui_add_file") != "ui_add_file" else "📄 Add File(s)")
        add_file_btn.setProperty("lang_id", "ui_add_file")
        add_file_btn.clicked.connect(self._add_file_job)

        remove_btn = QPushButton(self.get_string("ui_remove_selected") if self.get_string("ui_remove_selected") != "ui_remove_selected" else "🗑️ Remove Selected")
        remove_btn.setProperty("lang_id", "ui_remove_selected")
        remove_btn.clicked.connect(self._remove_selected_jobs_from_queue)

        clear_btn = QPushButton(self.get_string("ui_clear_queue") if self.get_string("ui_clear_queue") != "ui_clear_queue" else "🧹 Clear Queue")
        clear_btn.setProperty("lang_id", "ui_clear_queue")
        clear_btn.clicked.connect(self._clear_queue)

        job_controls_layout.addWidget(add_folder_btn)
        job_controls_layout.addWidget(add_file_btn)
        job_controls_layout.addWidget(remove_btn)
        job_controls_layout.addWidget(clear_btn)

        queue_layout.addWidget(job_controls_container)
        return queue_frame

    def _create_history_widget(self) -> QWidget:
        history_frame = QWidget()
        history_layout = QVBoxLayout(history_frame)
        history_layout.setContentsMargins(0, 0, 0, 0)

        self.history_list_widget = QListWidget()
        self.history_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        self.history_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_list_widget.customContextMenuRequested.connect(self._show_history_context_menu)

        history_layout.addWidget(self.history_list_widget)

        history_controls_container = QWidget()
        history_controls_layout = QHBoxLayout(history_controls_container)
        history_controls_layout.setContentsMargins(0, 0, 0, 0)
        history_controls_layout.addStretch()

        clear_history_btn = QPushButton(self.get_string("ui_clear_history") if self.get_string("ui_clear_history") != "ui_clear_history" else "Clear History")
        clear_history_btn.setProperty("lang_id", "ui_clear_history")
        clear_history_btn.clicked.connect(self._clear_history)
        history_controls_layout.addWidget(clear_history_btn)
        history_layout.addWidget(history_controls_container)

        return history_frame

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

    def log(self, level: str, message: str):
        if hasattr(self, 'app_logger'):
            self.app_logger.log(level, message)
