import os
import re

with open("desktop_ui/mainwindow/job_runner.py", "r") as f:
    content = f.read()

# Replace scene clear logic with specific item removal
content = re.sub(
    r"self\.scene_detector\.clear\(\)\s*self\.scene_detector\.addPixmap\((.*?)\)",
    r"if getattr(self, 'item_detector', None):\n                self.scene_detector.removeItem(self.item_detector)\n                self.item_detector = None\n            self.item_detector = self.scene_detector.addPixmap(\1)",
    content
)

content = re.sub(
    r"self\.scene_inpainter\.clear\(\)\s*self\.scene_inpainter\.addPixmap\((.*?)\)",
    r"if getattr(self, 'item_inpainter', None):\n                self.scene_inpainter.removeItem(self.item_inpainter)\n                self.item_inpainter = None\n            self.item_inpainter = self.scene_inpainter.addPixmap(\1)",
    content
)

content = re.sub(
    r"self\.scene_render\.clear\(\)\s*self\.scene_render\.addPixmap\((.*?)\)",
    r"if getattr(self, 'item_render', None):\n                    self.scene_render.removeItem(self.item_render)\n                    self.item_render = None\n                self.item_render = self.scene_render.addPixmap(\1)",
    content
)

# And for the clear in _load_test_image
content = re.sub(
    r"for scene in \[getattr\(self, 'scene_inpainter', None\), getattr\(self, 'scene_render', None\)\]:\n\s+if scene is not None:\n\s+scene\.clear\(\)",
    r"""if getattr(self, 'item_inpainter', None):
                self.scene_inpainter.removeItem(self.item_inpainter)
                self.item_inpainter = None
            if getattr(self, 'item_render', None):
                self.scene_render.removeItem(self.item_render)
                self.item_render = None""",
    content
)

with open("desktop_ui/mainwindow/job_runner.py", "w") as f:
    f.write(content)
