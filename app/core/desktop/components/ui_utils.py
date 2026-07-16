"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.ui_utils
- RESPONSIBILITY: ui_utils.py module logic.
- CALLED BY: Various
- CALLS TO: Various
- IN = OUT: Defines logic for app.core.desktop.components.ui_utils.
=============================================================================
"""
import re

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def build_grouped_settings_tabs(config_data, tab_order):
    """
    Groups configuration settings by their 'group' attribute and orders them
    according to the tab_order.

    Returns:
        dict: A mapping of tab_name -> list of settings
    """
    grouped_settings = {tab_name: [] for tab_name in tab_order}
    for key, info in config_data.items():
        group = info.get("group", "Other")
        if group in grouped_settings:
            grouped_settings[group].append(info)

    # Sort each group by order
    sorted_groups = {}
    for tab_name in tab_order:
        sorted_groups[tab_name] = sorted(grouped_settings.get(tab_name, []), key=lambda x: x.get('order', 999))
        
    return sorted_groups
