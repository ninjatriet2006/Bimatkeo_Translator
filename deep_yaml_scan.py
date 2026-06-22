import os
import yaml
from collections import defaultdict

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    if not isinstance(d, dict):
        return [(parent_key, d)]
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)

def scan_all_yaml():
    key_locations = defaultdict(list)
    val_locations = defaultdict(list)
    
    for root, _, files in os.walk('.config'):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    
                    if not data: continue
                    
                    flat = flatten_dict(data)
                    for k, v in flat.items():
                        # Extract just the last part of the key to see if the property name is duplicated
                        leaf_key = k.split('.')[-1]
                        key_locations[leaf_key].append(path)
                        val_locations[str(v)].append((path, k))
                        
                except Exception as e:
                    pass
                    
    print("=== Duplicate Keys across different YAML files ===")
    for k, locs in key_locations.items():
        unique_files = set(locs)
        if len(unique_files) > 2: # Appears in more than 2 files
            # Ignore langs/ and themes/ if they are just translations
            filtered_files = [f for f in unique_files if 'langs/' not in f and 'themes/' not in f]
            if len(filtered_files) > 1:
                print(f"\nKey '{k}' appears in {len(filtered_files)} files:")
                for f in filtered_files:
                    print(f"  - {f}")

if __name__ == "__main__":
    scan_all_yaml()
