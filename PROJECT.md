# PROJECT: Bimatkeo_Translator

## Architecture
```
+-----------------------------------------------------------------------+
|                              UI LAYER                                 |
|   app.core.desktop.main_window (TranslatorStudioApp container)        |
|   app.core.desktop.components (Widgets, Standalone Tools, Panels)     |
+-----------------------------------+-----------------------------------+
                                    | Qt Signals / Slots / DTOs
                                    v
+-----------------------------------------------------------------------+
|                           CONTROLLER LAYER                            |
|   app.core.desktop.logic.controllers / handlers                       |
|   (Mediators binding UI events to Core Services)                      |
+-------------------+-------------------------------+-------------------+
                    |                               |
                    v                               v
+-----------------------------------+   +-------------------------------+
|         CORE SERVICES LAYER       |   |       PIPELINE & ENGINE       |
|  app.core.api.manager             |   |  app.core.pipeline.manager    |
|  app.core.base.manager            |   |  app.core.shared_context DTO  |
|  app.core.langs.manager           |   |  app.core.fonts.manager       |
|  app.core.shared_registry         |   |  app.core.{ocr,translator,...}|
+-----------------------------------+   +-------------------------------+
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Top Toolbar ID Linking | Assign `lang_id` & `lang_type` to all 10 top toolbar buttons in `main_window.py:379-388` | M1 | Survey 1 |
| 2 | Preview Tester & Panel Localization | Assign `lang_id` to Preview Tester controls, Inspector panel, File Explorer, Font Install dialog | M1 | Survey 1 |
| 3 | Standalone Tools Localization | Add `lang_id` property assignments and `update_language_ui()` integration across all 5 standalone widgets | M1 | Survey 1 |
| 4 | Language Code Fix in `tabs.py` | Fix `tabs.py:85` to pass valid language codes (`en`/`vi`) instead of display names | M1 | Survey 1 |
| 5 | Manager Decoupling | Refactor `ApiProfileManager`, `ConfigSyncManager`, `JobQueueManager`, `ThemeManager` to remove `main_window` injection | M2 | Survey 2 |
| 6 | Controller Composition | Replace mixin inheritance in `TranslatorStudioApp` (`HandlersMixin`) with explicit controller composition | M2 | Survey 2 |
| 7 | Base & Desktop Config Consolidation | Delegate core config loading to `app.core.base.manager.ConfigManager`, preserving `INTEGRITY NOTES` | M2 | Survey 2 |
| 8 | Test Infrastructure | Create `pytest.ini` and `tests/conftest.py` with offscreen PySide6 `qapp` fixture | M3 | Survey 3 |
| 9 | Localization & UI Pytest Suite | Build `tests/test_localization.py` and `tests/test_ui_buttons.py` covering ID linking and button triggers | M3 | Survey 3 |
| 10 | Core Logic & Registry Pytest Suite | Build `tests/test_core_logic.py` and `tests/test_registry.py` for decoupled modules | M3 | Survey 3 |
| 11 | Legacy Test Refactoring | Fix legacy root `test_*.py` files (`test_check.py` class name, `test_merge.py` keys, collection errors) | M3 | Survey 3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | UI Repair & Localization ID Linking | Fix broken buttons/menus, add `lang_id` & `lang_type` to all UI elements, update language dicts, fix `tabs.py` | None | DONE |
| M2 | Modularization & Decoupling | Decouple manager classes from `main_window`, replace mixins with controllers, consolidate config system | M1 | DONE |
| M3 | Test Infrastructure & 100% Pass Pytest Suite | Build `tests/` directory, write fixtures in `conftest.py`, unit/UI test modules, fix legacy scripts | M1, M2 | DONE |

## Interface Contracts
### UI Widgets ↔ LanguageManager
- UI widgets MUST call `.setProperty("lang_id", "<key>")` and `.setProperty("lang_type", "ui")`.
- Dynamic language updating MUST be executed recursively via `TranslatorStudioApp.update_language_ui(parent_widget=None)`.
- Language dictionaries (`en.yaml`, `vi.yaml`) MUST contain valid string mappings for all registered `lang_id` keys.

### UI Handlers / Controllers ↔ Core Managers
- Managers (`ApiProfileManager`, `ConfigManager`, `PipelineManager`) MUST NOT take `main_window` or PySide6 `QMainWindow` instances into `__init__`.
- Communication from Managers to UI MUST happen via PySide6 `Signal` or plain return values / DTOs.
- All new or refactored core logic files MUST include `INTEGRITY NOTES` docstrings at top-of-file.

### Pytest Runner ↔ UI Application Testing
- PySide6 UI tests MUST use headless mode (`QT_QPA_PLATFORM=offscreen`).
- A single shared `qapp` fixture MUST be provided by `tests/conftest.py` to prevent libshiboken singleton collision errors.

## Code Layout
- `app/core/desktop/main_window.py`: Main PySide6 application window container (`TranslatorStudioApp`).
- `app/core/desktop/components/`: Sub-components, standalone widgets (`translator_widget.py`, etc.), preview panels.
- `app/core/desktop/logic/`: Controllers, handlers, and GUI business logic.
- `app/core/api/`: API management, profiles, verification, model fetching.
- `app/core/base/`: Base configuration management, loaders, parsers, schema loaders.
- `app/core/langs/`: Language manager, dictionary YAML files (`dicts/en.yaml`, `dicts/vi.yaml`), verification logic.
- `tests/`: Automated pytest test suite (`conftest.py`, `test_localization.py`, `test_ui_buttons.py`, `test_core_logic.py`, `test_registry.py`).
