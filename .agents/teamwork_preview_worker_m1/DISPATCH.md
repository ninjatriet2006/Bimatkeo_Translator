## 2026-07-27T01:44:26Z
Task (Milestone M1 - UI Repair & Localization ID Linking):
1. Read `/home/bimatkeo/Documents/Translator/Bimatkeo_Translator/.agents/teamwork_preview_explorer_survey_1/handoff.md` and `PROJECT.md`.
2. Fix Top Toolbar buttons in `app/core/desktop/main_window.py:379-388`: Add `.setProperty("lang_id", "...")` and `.setProperty("lang_type", "ui")` for `btn_queue`, `btn_log`, `btn_history`, `btn_preview`, 5 standalone tool buttons, and `btn_close_all_standalone`.
3. Fix controls in `app/core/desktop/components/widget_factory/layout_builder/preview_tester.py`: Add `lang_id` to `zoom_label`, `limit_zoom_check`, `btn_mode_select`, `btn_mode_draw`.
4. Fix File Explorer Panel `file_explorer_panel.py`, Inspector Panel `inspector_panel.py`, and Font Install Dialog `font_install_dialog.py`: Add `lang_id` properties to all labels and buttons.
5. Fix all 5 Standalone Tool Widgets in `app/core/desktop/components/standalone/*.py` (`translator_widget.py`, `ocr_widget.py`, `inpaint_widget.py`, `diffusion_widget.py`, `render_widget.py`): Add `lang_id` & `lang_type` properties and ensure titles, buttons, and labels update dynamically via `update_language_ui()`.
6. Fix language code lookup in `app/core/desktop/components/widget_factory/layout_builder/tabs.py:85` to pass valid language codes (`'en'` / `'vi'`) instead of display names.
7. Update language dictionary files (`app/core/langs/dicts/en.yaml`, `vi.yaml`) with all new `lang_id` keys and English / Vietnamese translations.
8. Run verification scripts (`python3 app/core/desktop/config/ui_verify.py` and `python3 app/core/langs/verify.py`) via terminal command and record passing results in your handoff report.
9. Write your detailed handoff report to:
   `/home/bimatkeo/Documents/Translator/Bimatkeo_Translator/.agents/teamwork_preview_worker_m1/handoff.md`
