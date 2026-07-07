#!/usr/bin/env python3
"""
=============================================================================
[AI_ARCH_NOTE]: LEGACY MIGRATION SCRIPT
- PURPOSE: One-time script to migrate old file structures and data formats 
  into the new architecture. 
- USAGE: Run manually when upgrading from a legacy version.
- WHY: Keeps the main application code clean from one-off migration logic.
=============================================================================
"""

import os
import sys

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ruamel.yaml import YAML
yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False

def migrate_font_versions_from_oldsession(oldsession_path: str, local_versions_path: str):
    """
    Migrates font versions stored in oldsession.yaml into the modern local_versions.yaml 
    under the 'fonts' key. This removes UI coupling for font initialization.
    """
    if not os.path.exists(oldsession_path):
        return

    with open(oldsession_path, "r", encoding="utf-8") as f:
        oldsession = yaml.load(f) or {}

    if "font_versions" not in oldsession:
        return

    font_versions = oldsession.pop("font_versions")
    
    with open(oldsession_path, "w", encoding="utf-8") as f:
        yaml.dump(oldsession, f)
        
    print("[Migration] Migrated font_versions from oldsession.yaml to local_versions.yaml")

    local_versions = {}
    if os.path.exists(local_versions_path):
        with open(local_versions_path, "r", encoding="utf-8") as lf:
            local_versions = yaml.load(lf) or {}

    local_versions["fonts"] = font_versions
    
    with open(local_versions_path, "w", encoding="utf-8") as lf:
        yaml.dump(local_versions, lf)


def migrate_hf_local_versions(local_versions_path: str, registry_path: str):
    """
    Migrates flat local_versions.yaml structure into categorized nested structures 
    based on model_registry.yaml. Removes UI coupling from config loader.
    """
    if not os.path.exists(local_versions_path):
        return

    with open(local_versions_path, "r", encoding="utf-8") as lf:
        local_versions = yaml.load(lf) or {}

    if not local_versions:
        return

    # Check if it's already nested (if any value is a dictionary, it's considered migrated)
    is_flat = any(isinstance(v, str) for v in local_versions.values())
    if not is_flat:
        return

    print("[Migration] Migrating local_versions.yaml to nested structure...")
    
    registry = {}
    if os.path.exists(registry_path):
        with open(registry_path, "r", encoding="utf-8") as rf:
            registry = yaml.load(rf) or {}

    # Build a map from model_key -> category
    model_to_category = {}
    fields = registry.get("fields", {})
    for tab, categories in fields.items():
        if isinstance(categories, dict):
            for category, models in categories.items():
                if isinstance(models, list):
                    for model in models:
                        model_to_category[model.get("key")] = category

    new_versions = {}
    for k, v in local_versions.items():
        if isinstance(v, dict):
            new_versions[k] = v
            continue
            
        cat = model_to_category.get(k, "uncategorized")
        if cat not in new_versions:
            new_versions[cat] = {}
        new_versions[cat][k] = v

    with open(local_versions_path, "w", encoding="utf-8") as lf:
        yaml.dump(new_versions, lf)
    print("[Migration] Migration of local_versions.yaml complete.")

if __name__ == "__main__":
    oldsession_path = os.path.join(project_root, ".config", "configs", "oldsession.yaml")
    local_versions_path = os.path.join(project_root, ".config", "models", "local_versions.yaml")
    registry_path = os.path.join(project_root, ".config", "models", "model_registry.yaml")
    
    print("Starting legacy migrations...")
    migrate_font_versions_from_oldsession(oldsession_path, local_versions_path)
    migrate_hf_local_versions(local_versions_path, registry_path)
    print("Legacy migrations completed.")
