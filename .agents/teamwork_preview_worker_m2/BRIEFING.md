# BRIEFING — 2026-07-27T01:55:15Z

## Mission
Milestone M2 - Modularization & Decoupling Specialist task for Bimatkeo_Translator.

## 🔒 My Identity
- Archetype: implementer/qa/specialist
- Roles: implementer, qa, specialist
- Working directory: /home/bimatkeo/Documents/Translator/Bimatkeo_Translator/.agents/teamwork_preview_worker_m2
- Original parent: 85441a1a-9373-4250-b317-4abd3e910913
- Milestone: M2 - Modularization & Decoupling

## 🔒 Key Constraints
- Must NOT write temporary python scripts to edit code. Use direct IDE edit tools (replace_file_content, write_to_file, multi_replace_file_content).
- Add/update top-of-file `INTEGRITY NOTES` docstrings for all new and modified core files.
- Decouple Manager Classes in `app/core/desktop/logic/` (`ApiProfileManager`, `ConfigSyncManager`, `JobQueueManager`, `ThemeManager`) so they take primitive parameters / data dicts into `__init__` instead of `main_window` or PySide6 `QMainWindow` instances.
- Use PySide6 Signals to notify UI components.
- Refactor `TranslatorStudioApp` in `app/core/desktop/main_window.py` to replace implicit mixin inheritance (`HandlersMixin`) with explicit controller/handler composition.
- Make `app.core.desktop.config.ConfigLoader` delegate core configuration management to `app.core.base.manager.ConfigManager` via composition.

## Current Parent
- Conversation ID: 85441a1a-9373-4250-b317-4abd3e910913
- Updated: 2026-07-27T01:55:15Z

## Task Summary
- **What to build**: Decouple desktop manager classes, replace HandlersMixin with composition in main_window.py, consolidate desktop ConfigLoader with base ConfigManager.
- **Success criteria**: All manager classes decoupled from UI/QMainWindow, HandlersMixin eliminated or turned into explicit handlers composition, ConfigLoader uses ConfigManager, all tests pass, no import of QMainWindow in logic managers.
- **Interface contracts**: PROJECT.md
- **Code layout**: PROJECT.md

## Key Decisions Made
- Starting investigation of Explorer Survey handoff report and relevant source files.

## Artifact Index
- DISPATCH.md — Task assignment
- BRIEFING.md — Context tracking
- progress.md — Liveness log

## Change Tracker
- **Files modified**: None yet
- **Build status**: TBD
- **Pending issues**: TBD

## Quality Status
- **Build/test result**: TBD
- **Lint status**: TBD
- **Tests added/modified**: TBD
