"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.langs.verify
- RESPONSIBILITY: Integrity and sanity check for localization vs UI map.
- CALLED BY: app.core.langs.manager
- CALLS TO: None
- IN = OUT: Evaluates dictionaries, logs validation results/warnings to system logger.
=============================================================================
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class LanguageVerifier:
    def __init__(self, localization: Dict[str, Any]):
        self.localization = localization

    def run_verification(self, raw_ui_map: dict, hardcoded_keys: dict | None = None, target_lang: str | None = None):
        """
        Cross-checks loaded localization dictionaries against the raw UI Map and hardcoded keys.
        Reports missing translations and orphaned keys.
        """
        logger.info("[LanguageVerifier] Running integrity check on languages...")
        if not self.localization:
            logger.warning("  [!] No localization files loaded.")
            return

        # Extract all needed keys from raw_ui_map
        required_tabs = set()
        required_settings = set()
        required_enums = set()

        for tab_name, widgets in raw_ui_map.items():
            if tab_name.startswith("__"):
                continue
            required_tabs.add(tab_name)
            
            for key, info in widgets.items():
                if not isinstance(info, dict):
                    continue
                required_settings.add(key)
                if "values" in info and isinstance(info["values"], list):
                    for v in info["values"]:
                        required_enums.add(v)

        # Baseline required keys from python source code (hardcoded_keys)
        hardcoded_keys = hardcoded_keys or {}
        required_ui_strings = hardcoded_keys.get("ui_strings", set())
        required_messages = hardcoded_keys.get("messages", set())
        required_tasks = hardcoded_keys.get("tasks", set())

        # If hardcoded_keys were not provided or failed to load, fallback to 'en' baseline
        baseline = self.localization.get("en", {})
        if not required_ui_strings:
            required_ui_strings = set(baseline.get("ui_strings", {}).keys())
        if not required_messages:
            required_messages = set(baseline.get("messages", {}).keys())
        if not required_tasks:
            required_tasks = set(baseline.get("tasks", {}).keys())

        # Check all languages (or just the target_lang if specified)
        for lang_id, lang_data in self.localization.items():
            if target_lang and lang_id != target_lang:
                continue
                
            logger.info(f"  -> Verifying language '{lang_id}'...")
            lang_tabs = set(lang_data.get("tabs", {}).keys())
            lang_settings = set(lang_data.get("settings", {}).keys())
            lang_enums = set(lang_data.get("enums", {}).keys())
            lang_ui_strings = set(lang_data.get("ui_strings", {}).keys())
            lang_messages = set(lang_data.get("messages", {}).keys())
            lang_tasks = set(lang_data.get("tasks", {}).keys())

            has_errors = False

            # Check missing
            missing_tabs = required_tabs - lang_tabs
            missing_settings = required_settings - lang_settings
            missing_enums = required_enums - lang_enums
            missing_ui_strings = required_ui_strings - lang_ui_strings
            missing_messages = required_messages - lang_messages
            missing_tasks = required_tasks - lang_tasks

            if missing_tabs:
                has_errors = True
                logger.warning(f"     [Missing Tabs]: {', '.join(missing_tabs)}")
            if missing_settings:
                has_errors = True
                logger.warning(f"     [Missing Settings]: {', '.join(missing_settings)}")
            if missing_enums:
                has_errors = True
                logger.warning(f"     [Missing Enums]: {', '.join(missing_enums)}")
            if missing_ui_strings:
                has_errors = True
                logger.warning(f"     [Missing UI Strings]: {', '.join(missing_ui_strings)}")
            if missing_messages:
                has_errors = True
                logger.warning(f"     [Missing Messages]: {', '.join(missing_messages)}")
            if missing_tasks:
                has_errors = True
                logger.warning(f"     [Missing Tasks]: {', '.join(missing_tasks)}")

            # Check orphans (defined in language file but not in UI map or codebase)
            orphan_tabs = lang_tabs - required_tabs
            orphan_settings = lang_settings - required_settings
            orphan_enums = lang_enums - required_enums
            orphan_ui_strings = lang_ui_strings - required_ui_strings
            orphan_messages = lang_messages - required_messages
            orphan_tasks = lang_tasks - required_tasks

            if orphan_tabs:
                has_errors = True
                logger.warning(f"     [Orphan Tabs]: {', '.join(orphan_tabs)}")
            if orphan_settings:
                has_errors = True
                logger.warning(f"     [Orphan Settings]: {', '.join(orphan_settings)}")
            if orphan_enums:
                has_errors = True
                logger.warning(f"     [Orphan Enums]: {', '.join(orphan_enums)}")
            if orphan_ui_strings:
                has_errors = True
                logger.warning(f"     [Orphan UI Strings]: {', '.join(orphan_ui_strings)}")
            if orphan_messages:
                has_errors = True
                logger.warning(f"     [Orphan Messages]: {', '.join(orphan_messages)}")
            if orphan_tasks:
                has_errors = True
                logger.warning(f"     [Orphan Tasks]: {', '.join(orphan_tasks)}")

            if not has_errors:
                logger.info(f"     [OK] Language '{lang_id}' passed verification with no missing or orphan keys.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Language Verification Script Loaded. To use it, it must be run via the manager during app startup.")
    print("Since version 2.0, the script cross-checks 'en.yaml' as a baseline against other languages.")
