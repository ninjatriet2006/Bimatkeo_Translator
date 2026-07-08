"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.base_config.parser
- RESPONSIBILITY: Phân tích cấu trúc (parse) các schema config và factory defaults.
- CALLED BY: app.core.base_config.base_loader
- CALLS TO: None
- IN = OUT: Nhận schema dict -> trả về các giá trị hoặc flat properties.
=============================================================================
"""
from typing import Any, Optional

def get_definition_from_ref(backend_schema: dict[str, Any], ref_path: str) -> Optional[Any]:
    try:
        parts = ref_path.split('/')[1:]
        node = backend_schema
        for part in parts:
            if not isinstance(node, dict):
                return None
            node = node[part]
        return node
    except Exception:
        return None

def get_flat_properties(backend_schema: dict[str, Any]) -> dict[str, Any]:
    """Gathers all root and nested properties from the schema."""
    all_properties = {}
    root_props = backend_schema.get("properties", {}) if backend_schema else {}
    all_properties.update(root_props)

    for prop in root_props.values():
        ref_path = prop.get("allOf", [{}])[0].get('$ref')
        if ref_path:
            config_def = get_definition_from_ref(backend_schema, ref_path)
            if config_def and "properties" in config_def:
                all_properties.update(config_def["properties"])
    return all_properties

def parse_factory_defaults(backend_schema: dict[str, Any]) -> dict[str, Any]:
    """Deep-parses the schema to get ALL default values, including nested ones."""
    if not backend_schema:
        return {}
    defaults = {}
    properties = backend_schema.get("properties", {})

    for prop_key, prop_value in properties.items():
        if "default" in prop_value and isinstance(prop_value.get("default"), dict):
            defaults.update(prop_value["default"])
        elif "default" in prop_value:
            defaults[prop_key] = prop_value["default"]
    return defaults
