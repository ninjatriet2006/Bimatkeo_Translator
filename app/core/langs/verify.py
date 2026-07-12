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

    def run_verification(self, raw_ui_map: dict):
        """
        Cross-checks loaded localization dictionaries against the raw UI Map.
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

        # Baseline required keys from 'en' language (or fallback)
        baseline = self.localization.get("en", {})
        required_ui_strings = set(baseline.get("ui_strings", {}).keys())
        required_messages = set(baseline.get("messages", {}).keys())
        required_tasks = set(baseline.get("tasks", {}).keys())

        # Check all languages
        for lang_id, lang_data in self.localization.items():
            if lang_id == "en":
                continue # Skip verifying the baseline against itself, though checking it against ui_map is useful

            logger.info(f"  -> Verifying language '{lang_id}'...")
            lang_tabs = set(lang_data.get("tabs", {}).keys())
            lang_settings = set(lang_data.get("settings", {}).keys())
            lang_enums = set(lang_data.get("enums", {}).keys())
            lang_ui_strings = set(lang_data.get("ui_strings", {}).keys())
            lang_messages = set(lang_data.get("messages", {}).keys())
            lang_tasks = set(lang_data.get("tasks", {}).keys())

            # Check missing
            missing_tabs = required_tabs - lang_tabs
            missing_settings = required_settings - lang_settings
            missing_enums = required_enums - lang_enums
            missing_ui_strings = required_ui_strings - lang_ui_strings
            missing_messages = required_messages - lang_messages
            missing_tasks = required_tasks - lang_tasks

            if missing_tabs:
                logger.warning(f"     [Missing Tabs]: {', '.join(missing_tabs)}")
            if missing_settings:
                logger.warning(f"     [Missing Settings]: {', '.join(missing_settings)}")
            if missing_enums:
                logger.warning(f"     [Missing Enums]: {', '.join(missing_enums)}")
            if missing_ui_strings:
                logger.warning(f"     [Missing UI Strings]: {', '.join(missing_ui_strings)}")
            if missing_messages:
                logger.warning(f"     [Missing Messages]: {', '.join(missing_messages)}")
            if missing_tasks:
                logger.warning(f"     [Missing Tasks]: {', '.join(missing_tasks)}")

            # Check orphans (defined in language file but not in UI map or baseline)
            orphan_tabs = lang_tabs - required_tabs
            orphan_settings = lang_settings - required_settings
            orphan_enums = lang_enums - required_enums
            orphan_ui_strings = lang_ui_strings - required_ui_strings
            orphan_messages = lang_messages - required_messages
            orphan_tasks = lang_tasks - required_tasks

            if orphan_tabs:
                logger.warning(f"     [Orphan Tabs]: {', '.join(orphan_tabs)}")
            if orphan_settings:
                logger.warning(f"     [Orphan Settings]: {', '.join(orphan_settings)}")
            if orphan_enums:
                logger.warning(f"     [Orphan Enums]: {', '.join(orphan_enums)}")
            if orphan_ui_strings:
                logger.warning(f"     [Orphan UI Strings]: {', '.join(orphan_ui_strings)}")
            if orphan_messages:
                logger.warning(f"     [Orphan Messages]: {', '.join(orphan_messages)}")
            if orphan_tasks:
                logger.warning(f"     [Orphan Tasks]: {', '.join(orphan_tasks)}")

        # Also verify 'en' against raw_ui_map
        if "en" in self.localization:
            lang_tabs = set(baseline.get("tabs", {}).keys())
            lang_settings = set(baseline.get("settings", {}).keys())
            lang_enums = set(baseline.get("enums", {}).keys())
            missing_tabs = required_tabs - lang_tabs
            missing_settings = required_settings - lang_settings
            missing_enums = required_enums - lang_enums
            if missing_tabs or missing_settings or missing_enums:
                logger.info(f"  -> Verifying language 'en' against raw UI map...")
                if missing_tabs:
                    logger.warning(f"     [Missing Tabs]: {', '.join(missing_tabs)}")
                if missing_settings:
                    logger.warning(f"     [Missing Settings]: {', '.join(missing_settings)}")
                if missing_enums:
                    logger.warning(f"     [Missing Enums]: {', '.join(missing_enums)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Language Verification Script Loaded. To use it, it must be run via the manager during app startup.")
    print("Since version 2.0, the script cross-checks 'en.yaml' as a baseline against other languages.")
