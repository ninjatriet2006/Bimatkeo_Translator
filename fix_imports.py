import os
import re

mapping = {
    'BaseTextDetector': 'app.core.ocr.interfaces',
    'BaseTextRecognizer': 'app.core.ocr.interfaces',
    'BaseCloudOCR': 'app.core.ocr.interfaces',
    'BaseTranslator': 'app.core.translator.interfaces',
    'BaseInpainter': 'app.core.inpainter.interfaces',
    'BaseUpscaler': 'app.core.inpainter.interfaces',
    'BaseColorizer': 'app.core.inpainter.interfaces',
    'BaseRenderer': 'app.core.renderer.interfaces',
    'BaseDiffusionModel': 'app.core.diffusion.interfaces'
}

for root, _, files in os.walk('app'):
    for file in files:
        if file.endswith('.py') and file != 'interfaces.py':
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'from app.core.interfaces import' in content:
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    if 'from app.core.interfaces import' in line:
                        classes = line.replace('from app.core.interfaces import', '').strip().split(',')
                        classes = [c.strip() for c in classes]
                        for c in classes:
                            if c in mapping:
                                new_lines.append(f"from {mapping[c]} import {c}")
                            else:
                                new_lines.append(line) # Fallback if something weird
                    else:
                        new_lines.append(line)
                
                with open(path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                    print(f"Updated {path}")
