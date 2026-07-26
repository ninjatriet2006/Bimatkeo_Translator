## 2026-07-27T01:55:15Z

You are Worker 2 (Modularization & Decoupling Specialist).
Working Directory: /home/bimatkeo/Documents/Translator/Bimatkeo_Translator/.agents/teamwork_preview_worker_m2
Project Root: /home/bimatkeo/Documents/Translator/Bimatkeo_Translator
Authoritative request file: /home/bimatkeo/Documents/Translator/Bimatkeo_Translator/ORIGINAL_REQUEST.md
Scope Document: /home/bimatkeo/Documents/Translator/Bimatkeo_Translator/PROJECT.md
Architecture Survey: /home/bimatkeo/Documents/Translator/Bimatkeo_Translator/.agents/teamwork_preview_explorer_survey_2/handoff.md

Task (Milestone M2 - Modularization & Decoupling):
1. Read `/home/bimatkeo/Documents/Translator/Bimatkeo_Translator/.agents/teamwork_preview_explorer_survey_2/handoff.md` and `PROJECT.md`.
2. Decouple Manager Classes: Refactor `ApiProfileManager`, `ConfigSyncManager`, `JobQueueManager`, `ThemeManager` in `app/core/desktop/logic/` so they take primitive parameters / data dicts into `__init__` instead of `main_window` or PySide6 `QMainWindow` instances. Use PySide6 Signals to notify UI components.
3. Refactor `TranslatorStudioApp` in `app/core/desktop/main_window.py` to replace implicit mixin inheritance (`HandlersMixin`) with explicit controller/handler composition.
4. Consolidate Base Config and Desktop Config systems: Make `app.core.desktop.config.ConfigLoader` delegate core configuration management to `app.core.base.manager.ConfigManager` via composition.
5. Add/update top-of-file `INTEGRITY NOTES` docstrings for all new and modified core files.
6. Verify code imports and integrity using terminal commands (e.g. check no manager imports QMainWindow directly).
7. Write your detailed handoff report to:
   `/home/bimatkeo/Documents/Translator/Bimatkeo_Translator/.agents/teamwork_preview_worker_m2/handoff.md`
