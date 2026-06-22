import os
import hashlib

def hash_file(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

hashes = {}
for root, _, files in os.walk('.'):
    if '.venv' in root or '.git' in root or 'temp' in root or 'result' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py') or file.endswith('.yaml') or file.endswith('.json'):
            path = os.path.join(root, file)
            h = hash_file(path)
            if h in hashes:
                hashes[h].append(path)
            else:
                hashes[h] = [path]

for h, paths in hashes.items():
    if len(paths) > 1:
        print(f"Exact Duplicate Files:")
        for p in paths:
            print(f"  - {p}")
