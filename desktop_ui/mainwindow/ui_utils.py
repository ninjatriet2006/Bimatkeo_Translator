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
