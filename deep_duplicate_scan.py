import os
import ast
import json
import yaml
from collections import defaultdict
import hashlib

def hash_ast_node(node):
    # Create a normalized string representation of an AST node
    if isinstance(node, ast.AST):
        node_type = type(node).__name__
        if hasattr(node, 'id'):
            return f"{node_type}({node.id})"
        elif hasattr(node, 'arg'):
            return f"{node_type}({node.arg})"
        elif isinstance(node, ast.Constant):
            return f"{node_type}({type(node.value).__name__})"
        elif isinstance(node, ast.Name):
            return f"{node_type}(var)"
        else:
            children = [hash_ast_node(c) for c in ast.iter_child_nodes(node)]
            return f"{node_type}({','.join(children)})"
    elif isinstance(node, list):
        return f"[{','.join(hash_ast_node(n) for n in node)}]"
    else:
        return str(node)

def scan_python_files(directory):
    functions_by_hash = defaultdict(list)
    classes_by_name = defaultdict(list)
    constants_by_value = defaultdict(list)
    
    for root, _, files in os.walk(directory):
        if '.venv' in root or '.git' in root or 'temp' in root or 'result' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            # hash function body
                            body_hash = hash_ast_node(node.body)
                            if len(node.body) > 3: # Only consider functions with more than 3 statements
                                functions_by_hash[body_hash].append(f"{path}:{node.name} (line {node.lineno})")
                                
                        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                            if len(node.value) > 20: # Long string constants
                                constants_by_value[node.value].append(f"{path} (line {node.lineno})")
                                
                except Exception as e:
                    pass
    return functions_by_hash, constants_by_value

def scan_config_files(directory):
    yaml_keys = defaultdict(list)
    dict_structures = defaultdict(list)
    
    for root, _, files in os.walk(directory):
        if '.venv' in root or '.git' in root or 'temp' in root or 'result' in root:
            continue
        for file in files:
            if file.endswith(('.yaml', '.yml', '.json')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        if file.endswith('.json'):
                            data = json.load(f)
                        else:
                            data = yaml.safe_load(f)
                    
                    def traverse(obj, current_path=""):
                        if isinstance(obj, dict):
                            keys_tuple = tuple(sorted(obj.keys()))
                            if len(keys_tuple) > 2:
                                dict_structures[keys_tuple].append(f"{path} at {current_path}")
                            for k, v in obj.items():
                                yaml_keys[k].append(f"{path} at {current_path}.{k}")
                                traverse(v, f"{current_path}.{k}")
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                traverse(item, f"{current_path}[{i}]")
                                
                    traverse(data, "$")
                except Exception as e:
                    pass
    return dict_structures, yaml_keys

def main():
    print("=== DEEP SCAN FOR DUPLICATES ===")
    funcs, consts = scan_python_files('.')
    print("\n--- Duplicate Python Functions (Structural clone) ---")
    found_funcs = False
    for h, locs in funcs.items():
        if len(locs) > 1:
            found_funcs = True
            print(f"\nDuplicate structure found in {len(locs)} places:")
            for loc in locs:
                print(f"  - {loc}")
    if not found_funcs:
        print("None found.")

    print("\n--- Duplicate Long String Constants ---")
    found_consts = False
    for val, locs in consts.items():
        if len(locs) > 1:
            found_consts = True
            print(f"\nString: {repr(val[:50])}... found in {len(locs)} places:")
            for loc in set(locs):
                print(f"  - {loc}")
    if not found_consts:
        print("None found.")

    print("\n--- Config Files: Repeated Dictionary Structures ---")
    structs, keys = scan_config_files('.')
    found_structs = False
    for struct, locs in structs.items():
        if len(locs) > 1:
            # Filter out structures that are just in the same file array
            unique_files = set(loc.split(' at ')[0] for loc in locs)
            if len(unique_files) > 1:
                found_structs = True
                print(f"\nStructure with keys {struct} found in {len(locs)} places across {len(unique_files)} files:")
                for loc in locs[:5]: # show up to 5
                    print(f"  - {loc}")
                if len(locs) > 5:
                    print(f"  - ... and {len(locs) - 5} more.")

    print("\n--- Config Files: Repeated Key Names ---")
    # Count how many unique files a key appears in
    key_file_counts = {}
    for k, locs in keys.items():
        unique_files = set(loc.split(' at ')[0] for loc in locs)
        if len(unique_files) > 2: # Appears in more than 2 files
            key_file_counts[k] = unique_files
            
    for k, ufiles in sorted(key_file_counts.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"Key '{k}' appears in {len(ufiles)} files.")

if __name__ == "__main__":
    main()
