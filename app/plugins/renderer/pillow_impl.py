import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import List, Any

from app.core.interfaces import BaseRenderer
from app.core.factories import RendererFactory

@RendererFactory.register("pillow_renderer")
@RendererFactory.register("default")
class PillowRenderer_Impl(BaseRenderer):
    def __init__(self):
        self.font_path = None
        self.default_font = None
        
    def load_fonts(self, font_path: str, **kwargs) -> None:
        self.font_path = font_path
        # If font path doesn't exist or is empty, fallback to default PIL font
        if not self.font_path or not os.path.exists(self.font_path):
            print(f"[Renderer] Font path invalid: {self.font_path}. Using default system font.")
            self.default_font = ImageFont.load_default()
        else:
            print(f"[Renderer] Loaded font from {self.font_path}")

    def _wrap_text(self, text: str, font: Any, max_width: int, draw: Any) -> List[str]:
        """Simple word wrapping algorithm"""
        lines = []
        words = text.split()
        if not words:
            return lines
            
        current_line = words[0]
        for word in words[1:]:
            # Check length of current_line + word
            test_line = current_line + " " + word
            length = draw.textlength(test_line, font=font)
            if length <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        return lines

    def render(self, image: np.ndarray, bboxes: List[List[int]], texts: List[str]) -> np.ndarray:
        if not texts or not bboxes:
            return image
            
        # Convert OpenCV image (BGR) to Pillow Image (RGB)
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        draw = ImageDraw.Draw(pil_img)
        
        for box, text in zip(bboxes, texts):
            if not text.strip():
                continue
                
            x_min, y_min, x_max, y_max = box
            box_width = x_max - x_min
            box_height = y_max - y_min
            
            if box_width <= 0 or box_height <= 0:
                continue
                
            # Dynamic Font Sizing: try to find a font size that fits the box height and width
            font_size = 20  # initial guess
            if self.font_path and os.path.exists(self.font_path):
                # Auto-fit font size
                best_font = None
                best_lines = []
                best_y_offset = 0
                
                # Test sizes from 40 down to 10
                for size in range(40, 8, -2):
                    try:
                        font = ImageFont.truetype(self.font_path, size)
                    except:
                        font = ImageFont.load_default()
                        break
                        
                    lines = self._wrap_text(text, font, box_width, draw)
                    # Calculate total height
                    line_height = size * 1.2 # approximate
                    total_height = line_height * len(lines)
                    
                    if total_height <= box_height:
                        best_font = font
                        best_lines = lines
                        best_y_offset = (box_height - total_height) / 2
                        break
                
                if best_font is None:
                    # If it couldn't fit even at smallest size, just use smallest size
                    try:
                        best_font = ImageFont.truetype(self.font_path, 10)
                    except:
                        best_font = ImageFont.load_default()
                    best_lines = self._wrap_text(text, best_font, box_width, draw)
                    best_y_offset = 0
                
                # Draw lines
                current_y = y_min + best_y_offset
                for line in best_lines:
                    line_width = draw.textlength(line, font=best_font)
                    x_offset = x_min + (box_width - line_width) / 2
                    
                    # Draw text outline for better visibility
                    outline_color = (255, 255, 255)
                    text_color = (0, 0, 0)
                    
                    # Basic outline
                    for adj in range(-1, 2):
                        for adj2 in range(-1, 2):
                            if adj != 0 or adj2 != 0:
                                draw.text((x_offset + adj, current_y + adj2), line, font=best_font, fill=outline_color)
                    
                    draw.text((x_offset, current_y), line, font=best_font, fill=text_color)
                    font_size = getattr(best_font, "size", 10)
                    current_y += font_size * 1.2
            else:
                # Use default font (no size adjustment)
                font = self.default_font if self.default_font else ImageFont.load_default()
                draw.text((x_min, y_min), text, font=font, fill=(0, 0, 0))

        # Convert back to OpenCV
        result_rgb = np.array(pil_img)
        result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
        return result_bgr
