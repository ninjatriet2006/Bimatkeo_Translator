## 2026-07-27T02:16:20Z
Task (Milestone M3 - Test Infrastructure & 100% Passing Pytest Suite):
1. Read `/home/bimatkeo/Documents/Translator/Bimatkeo_Translator/.agents/teamwork_preview_explorer_survey_3/handoff.md` and `PROJECT.md`.
2. Create `pytest.ini` at project root configuring `testpaths = tests`.
3. Create `tests/conftest.py` with shared headless PySide6 `qapp` fixture (`QT_QPA_PLATFORM=offscreen`) to eliminate libshiboken singleton collision errors.
4. Refactor/Fix legacy root test files (`test_check.py`, `test_invoke.py`, `test_merge.py`, `test_qtimer_thread.py`, `test_real_loader.py`, `test_timer.py`) by converting them to standard pytest functions inside `tests/` and fixing broken class imports (`BimatkeoTranslator` -> `TranslatorStudioApp`), registry instantiations, and dict keys.
5. Create comprehensive test modules inside `tests/`:
   - `tests/test_localization.py`: Test ID linking (`lang_id`, `lang_type`), dynamic language updating (`update_language_ui`), and dictionary completeness.
   - `tests/test_ui_buttons.py`: Test top toolbar buttons, standalone widgets, preview tester, inspector, and font dialog buttons.
   - `tests/test_core_logic.py`: Test decoupled managers (`ApiProfileManager`, `ConfigSyncManager`, `JobQueueManager`, `ThemeManager`), `ConfigManager`, and composition.
   - `tests/test_registry.py`: Test plugin discovery and factory loaders.
6. Execute `./.venv/bin/pytest` via terminal command and ensure 100% pass (0 failures, 0 collection errors).
7. Write your detailed handoff report to:
   `/home/bimatkeo/Documents/Translator/Bimatkeo_Translator/.agents/teamwork_preview_test_writer_m3/handoff.md`
