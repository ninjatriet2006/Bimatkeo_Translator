"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.langs.verify
- RESPONSIBILITY: Integrity and sanity check for localization vs UI map.
- CALLED BY: app.core.langs.manager
- CALLS TO: None
- IN = OUT: Evaluates dictionaries, returns validation results/warnings.
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

        for lang_id, lang_data in self.localization.items():
            logger.info(f"  -> Verifying language '{lang_id}'...")
            lang_tabs = set(lang_data.get("tabs", {}).keys())
            lang_settings = set(lang_data.get("settings", {}).keys())
            lang_enums = set(lang_data.get("enums", {}).keys())

            # Check missing
            missing_tabs = required_tabs - lang_tabs
            missing_settings = required_settings - lang_settings
            missing_enums = required_enums - lang_enums

            if missing_tabs:
                logger.warning(f"     [Missing Tabs]: {', '.join(missing_tabs)}")
            if missing_settings:
                logger.warning(f"     [Missing Settings]: {', '.join(missing_settings)}")
            if missing_enums:
                logger.warning(f"     [Missing Enums]: {', '.join(missing_enums)}")

            # Check orphans (defined in language file but not in UI map)
            orphan_tabs = lang_tabs - required_tabs
            orphan_settings = lang_settings - required_settings
            orphan_enums = lang_enums - required_enums

            if orphan_tabs:
                logger.warning(f"     [Orphan Tabs]: {', '.join(orphan_tabs)}")
            if orphan_settings:
                logger.warning(f"     [Orphan Settings]: {', '.join(orphan_settings)}")
            if orphan_enums:
                logger.warning(f"     [Orphan Enums]: {', '.join(orphan_enums)}")
