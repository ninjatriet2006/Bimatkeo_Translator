import os
import ast
import hashlib
from collections import defaultdict
import yaml

def get_ast_hash(node):
    # Simplistic AST hash by dumping the tree
    # Remove docstrings
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if ast.get_docstring(node):
            node.body = node.body[1:]
    # Try to make variable names uniform? Too complex, just dump
    dump = ast.dump(node)
    return hashlib.md5(dump.encode('utf-8')).hexdigest()

def scan_python_dupes(root_dir):
    func_hashes = defaultdict(list)
    for root, dirs, files in os.walk(root_dir):
        if 'venv' in root or '.venv' in root or '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            # Only consider functions longer than 5 statements
                            if len(node.body) > 5:
                                h = get_ast_hash(node)
                                func_hashes[h].append((path, node.name, node.lineno))
                except Exception as e:
                    print(f"Error parsing {path}: {e}")
    
    print("--- DUPLICATE PYTHON FUNCTIONS ---")
    for h, locs in func_hashes.items():
        if len(locs) > 1:
            # Check if they are actually different files or just same name
            unique_files = set(p for p, n, l in locs)
            if len(unique_files) > 1:
                print(f"Duplicate logic found: {locs[0][1]}")
                for p, n, l in locs:
                    print(f"  - {p}:{l} ({n})")
                print()

def scan_yaml_dupes(root_dir):
    yaml_keys = defaultdict(list)
    for root, dirs, files in os.walk(root_dir):
        if 'venv' in root or '.venv' in root or '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith(('.yaml', '.json')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        if file.endswith('.yaml'):
                            data = yaml.safe_load(f)
                        else:
                            import json
                            data = json.load(f)
                    
                    if isinstance(data, dict):
                        for k in data.keys():
                            yaml_keys[k].append(path)
                except Exception:
                    pass

    print("--- FREQUENT CONFIG KEYS ACROSS FILES ---")
    for k, paths in yaml_keys.items():
        unique_paths = set(paths)
        if len(unique_paths) > 2 and k not in ['type', 'properties', 'default', 'title', 'widget', 'description', 'enum']:
            print(f"Key '{k}' found in: {', '.join(unique_paths)}")

scan_python_dupes('.')
scan_yaml_dupes('.config')
