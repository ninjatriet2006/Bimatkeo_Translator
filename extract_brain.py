import os
import json
import re

brain_dir = '/home/bimatkeo/.gemini/antigravity-ide/brain'
output_file = '/home/bimatkeo/.gemini/antigravity-ide/skills/self-evolution/python_ai_skill.md'

os.makedirs(os.path.dirname(output_file), exist_ok=True)

patterns = set()
architectural_notes = []

# Scan all transcript.jsonl
total_size = 0
for root, dirs, files in os.walk(brain_dir):
    for file in files:
        if file == 'transcript.jsonl':
            filepath = os.path.join(root, file)
            total_size += os.path.getsize(filepath)
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data.get('source') == 'MODEL' and data.get('content'):
                            content = data['content']
                            # Extract python blocks
                            py_blocks = re.findall(r'```python\n(.*?)\n```', content, re.DOTALL)
                            for block in py_blocks:
                                if 'class ' in block or 'def ' in block:
                                    # Extract class/func names
                                    names = re.findall(r'(?:class|def)\s+([a-zA-Z0-9_]+)', block)
                                    patterns.update(names)
                            
                            # Extract architectural rules mentioned
                            if 'architecture' in content.lower() or 'pattern' in content.lower() or 'mixin' in content.lower():
                                # Just save a snippet
                                snippet = content[:500] + '...' if len(content) > 500 else content
                                if snippet not in architectural_notes:
                                    architectural_notes.append(snippet)
                    except:
                        pass

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# Python AI Skill - Bimatkeo Translator\n\n")
    f.write(f"> Automatically extracted from {total_size / (1024*1024*1024):.2f} GB of Antigravity IDE Brain data.\n\n")
    f.write("## 1. Core Architectural Entities\n")
    f.write("The following classes and functions have been identified as core to the project's evolution:\n")
    f.write(", ".join(sorted(list(patterns))[:100]) + "\n\n")
    
    f.write("## 2. Evolution & Architectural Principles\n")
    for note in architectural_notes[-20:]: # Take last 20 notes
        f.write(f"- {note.replace('\n', ' ')}\n")
        
print(f"Processed {total_size / (1024*1024):.2f} MB of transcripts.")
