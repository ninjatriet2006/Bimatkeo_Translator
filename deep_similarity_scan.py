import os
import ast
from collections import defaultdict
import difflib

def get_ast_tokens(node):
    tokens = []
    if isinstance(node, ast.AST):
        tokens.append(type(node).__name__)
        if hasattr(node, 'id'):
            tokens.append(str(node.id))
        elif hasattr(node, 'arg'):
            tokens.append(str(node.arg))
        for child in ast.iter_child_nodes(node):
            tokens.extend(get_ast_tokens(child))
    return tokens

def scan_python_similarity(directory):
    functions = []
    
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
                            if len(node.body) > 3: # Ignore trivial functions
                                tokens = get_ast_tokens(node.body)
                                if len(tokens) > 20: # Ignore very short functions
                                    functions.append({
                                        'path': path,
                                        'name': node.name,
                                        'line': node.lineno,
                                        'tokens': tokens,
                                        'code': ast.unparse(node) if hasattr(ast, 'unparse') else ""
                                    })
                except Exception as e:
                    pass
                    
    # Compare all pairs
    results = []
    for i in range(len(functions)):
        for j in range(i + 1, len(functions)):
            f1 = functions[i]
            f2 = functions[j]
            # Fast Jaccard similarity check
            set1 = set(f1['tokens'])
            set2 = set(f2['tokens'])
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            if union == 0: continue
            jaccard = intersection / union
            
            if jaccard > 0.8: # Very similar tokens
                # Do SequenceMatcher for exact structural similarity
                sm = difflib.SequenceMatcher(None, f1['tokens'], f2['tokens'])
                ratio = sm.ratio()
                if ratio > 0.75 and f1['name'] != f2['name']: # Ignore exactly same named functions across files unless ratio is high
                     results.append((ratio, f1, f2))
                elif ratio > 0.9:
                     results.append((ratio, f1, f2))

    results.sort(key=lambda x: x[0], reverse=True)
    return results

def main():
    print("=== DEEP SIMILARITY SCAN (PYTHON) ===")
    results = scan_python_similarity('.')
    
    seen_pairs = set()
    count = 0
    for ratio, f1, f2 in results:
        # Create a signature
        sig1 = f"{f1['path']}:{f1['name']}"
        sig2 = f"{f2['path']}:{f2['name']}"
        pair_sig = tuple(sorted([sig1, sig2]))
        if pair_sig in seen_pairs:
            continue
        seen_pairs.add(pair_sig)
        
        print(f"\nSimilarity: {ratio:.2f}")
        print(f"  A: {sig1} (line {f1['line']})")
        print(f"  B: {sig2} (line {f2['line']})")
        count += 1
        if count >= 30: # limit to top 30
            break

if __name__ == "__main__":
    main()
