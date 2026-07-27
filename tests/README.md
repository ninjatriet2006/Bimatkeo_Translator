# Bimatkeo Translator - Test Specifications & Cleanup Policy

## Overview
This directory (`tests/`) contains all automated unit and integration tests for the Bimatkeo Translator system. All reusable test scripts MUST be placed here following the standard `pytest` structure.

---

## Integrity Rules for Test Files (MANDATORY FOR AI AGENTS & DEVELOPERS)

1. **NO LOOSE SCRIPTS IN ROOT**:
   - Never create temporary `test_*.py` or scratch files in the repository root directory.
   - Any reusable test must be added inside `tests/` with the `test_` prefix (e.g., `tests/test_plugin_registry.py`).
   - Any single-use debug script must be created in temporary directories and must NOT be committed to git.

2. **INTEGRITY NOTES REQUIRED**:
   - Every Python file inside `tests/` MUST start with an `INTEGRITY NOTES` docstring block at the top detailing module name, responsibility, called framework, and scope.

3. **PYTEST STANDARDS**:
   - All tests must run cleanly via `.venv/bin/pytest`.
   - Tests requiring GUI widgets MUST use offscreen mode (`os.environ["QT_QPA_PLATFORM"] = "offscreen"`) or `pytest-qt` fixtures to prevent opening desktop windows during automated test runs.

---

## Test Directory Structure

| Test File | Description / Scope |
| :--- | :--- |
| `tests/conftest.py` | Pytest fixtures, mock data, and test initialization setup. |
| `tests/test_core_logic.py` | Unit tests for decoupled managers (`ApiProfileManager`, `ConfigSyncManager`, `ThemeManager`, `JobQueueUIManager`, `ConfigManager`). |
| `tests/test_plugin_registry.py` | Tests for factory registration & plugin discovery (Translator, Cloud OCR, Detector, Renderer). |
| `tests/test_config_and_loader.py` | Tests for config schema validation, model existence checks, registry merging, and registry loader. |
| `tests/test_gui_offscreen.py` | Integration tests verifying `TranslatorStudioApp` window instantiation and layout building in offscreen mode. |
| `tests/test_localization.py` | Sanity and integrity checks for language YAML files (`en.yaml`, `vi.yaml`) against `STUDIO_UI_MAP`. |
| `tests/test_legacy.py` | Compatibility tests for legacy components. |

---

## Cleanup Guidelines

- **Log Files**: `*.log` files are generated at runtime and are ignored by `.gitignore`. They must not be committed.
- **Disposable Debug Scripts**: Scripts containing hardcoded API keys or temporary thread tests are strictly single-use and must be removed after debugging sessions.
