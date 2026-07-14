"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.renderer.pillow.render
- RESPONSIBILITY: Thực thi render text lên ảnh bằng Pillow.
- CALLED BY: app.plugins.renderer.pillow.main_impl
- CALLS TO: None
- IN = OUT: Nhận ảnh (OpenCV), danh sách bboxes, texts, config; trả về ảnh đã vẽ chữ (OpenCV format).
=============================================================================
"""
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import List, Any

def hex_to_rgb(hex_code: str, default: tuple) -> tuple:
    if not hex_code:
        return default
    hex_code = hex_code.lstrip('#')
    try:
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
    except:
        return default

def wrap_text(text: str, font: Any, max_width: int, draw: Any) -> List[str]:
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

def render_pillow(renderer_instance, image: np.ndarray, bboxes: List[List[int]], texts: List[str]) -> np.ndarray:
    if not texts or not bboxes:
        return image
        
    # Parse configs
    font_color_hex = renderer_instance.config.get("font_color", "000000")
    outline_color_hex = renderer_instance.config.get("outline_color", "FFFFFF")
    text_color = hex_to_rgb(font_color_hex, (0, 0, 0))
    outline_color = hex_to_rgb(outline_color_hex, (255, 255, 255))
    
    alignment = renderer_instance.config.get("alignment", "auto")
    font_size_override = renderer_instance.config.get("font_size")
    try: font_size_override = int(str(font_size_override).replace("none", "0") or 0)
    except ValueError: font_size_override = 0
    
    font_size_offset = renderer_instance.config.get("font_size_offset", 0)
    try: font_size_offset = int(str(font_size_offset).replace("none", "0") or 0)
    except ValueError: font_size_offset = 0
    
    font_size_minimum = renderer_instance.config.get("font_size_minimum", -1)
    try: font_size_minimum = int(str(font_size_minimum).replace("none", "-1") or -1)
    except ValueError: font_size_minimum = -1
    
    uppercase = renderer_instance.config.get("uppercase", False)
    lowercase = renderer_instance.config.get("lowercase", False)
    
    line_spacing_scale = renderer_instance.config.get("line_spacing")
    if not line_spacing_scale:
        line_spacing_scale = 1.2
    else:
        line_spacing_scale = line_spacing_scale / 10.0
        
    outline_width = renderer_instance.config.get("outline_width", 2)
    disable_font_border = renderer_instance.config.get("disable_font_border", False)
    is_bold = renderer_instance.config.get("is_bold", False)

    # Convert OpenCV image (BGR) to Pillow Image (RGB)
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)
    
    for box, text in zip(bboxes, texts):
        if not text.strip():
            continue
            
        if uppercase:
            text = text.upper()
        elif lowercase:
            text = text.lower()
            
        x_min, y_min, x_max, y_max = box
        box_width = x_max - x_min
        box_height = y_max - y_min
        
        # Add dynamic padding (10%) to keep text inside circular/elliptical bubbles
        pad_x = int(box_width * 0.1)
        pad_y = int(box_height * 0.1)
        
        x_min += pad_x
        x_max -= pad_x
        y_min += pad_y
        y_max -= pad_y
        
        box_width = x_max - x_min
        box_height = y_max - y_min
        
        if box_width <= 0 or box_height <= 0:
            # Revert if the box is too small
            x_min, y_min, x_max, y_max = box
            box_width = x_max - x_min
            box_height = y_max - y_min
            
        if box_width <= 0 or box_height <= 0:
            continue
            
        if renderer_instance.font_path and os.path.exists(renderer_instance.font_path):
            best_font = None
            best_lines = []
            best_y_offset = 0
            
            if font_size_override and font_size_override > 0:
                target_size = font_size_override
                try:
                    best_font = ImageFont.truetype(renderer_instance.font_path, target_size)
                except:
                    best_font = ImageFont.load_default()
                best_lines = wrap_text(text, best_font, box_width, draw)
                total_height = target_size * line_spacing_scale * len(best_lines)
                best_y_offset = max(0, (box_height - total_height) / 2)
            else:
                # Auto-fit font size
                min_size = 1
                max_size = min(box_height, 150)
                
                while min_size <= max_size:
                    mid_size = (min_size + max_size) // 2
                    try:
                        font = ImageFont.truetype(renderer_instance.font_path, mid_size)
                    except:
                        font = ImageFont.load_default()
                        best_font = font
                        best_lines = wrap_text(text, font, box_width, draw)
                        best_y_offset = (box_height - (10 * line_spacing_scale * len(best_lines))) / 2
                        break
                        
                    lines = wrap_text(text, font, box_width, draw)
                    
                    line_height = mid_size * line_spacing_scale
                    total_height = line_height * len(lines)
                    
                    max_line_width = max([draw.textlength(line, font=font) for line in lines] + [0])
                    
                    if total_height <= box_height and max_line_width <= box_width:
                        best_font = font
                        best_lines = lines
                        best_y_offset = (box_height - total_height) / 2
                        min_size = mid_size + 1
                    else:
                        max_size = mid_size - 1
                
                if best_font is None:
                    try:
                        best_font = ImageFont.truetype(renderer_instance.font_path, 10)
                    except:
                        best_font = ImageFont.load_default()
                    best_lines = wrap_text(text, best_font, box_width, draw)
                    best_y_offset = max(0, (box_height - (10 * line_spacing_scale * len(best_lines))) / 2)
                
                # Apply offset and minimum
                final_size = getattr(best_font, "size", 10) + font_size_offset
                if font_size_minimum > 0 and final_size < font_size_minimum:
                    final_size = font_size_minimum
                
                try:
                    best_font = ImageFont.truetype(renderer_instance.font_path, final_size)
                except:
                    pass
                best_lines = wrap_text(text, best_font, box_width, draw)
                total_height = final_size * line_spacing_scale * len(best_lines)
                best_y_offset = (box_height - total_height) / 2
            
            # Draw lines
            current_y = y_min + best_y_offset
            for line in best_lines:
                line_width = draw.textlength(line, font=best_font)
                
                if alignment == "left":
                    x_offset = x_min
                elif alignment == "right":
                    x_offset = x_max - line_width
                else: # auto / center
                    x_offset = x_min + (box_width - line_width) / 2
                
                # Draw text outline
                if not disable_font_border and outline_width > 0:
                    for adj in range(-outline_width, outline_width + 1):
                        for adj2 in range(-outline_width, outline_width + 1):
                            if adj != 0 or adj2 != 0:
                                draw.text((x_offset + adj, current_y + adj2), line, font=best_font, fill=outline_color)
                
                # Fake Bold
                if is_bold:
                    draw.text((x_offset + 1, current_y), line, font=best_font, fill=text_color)
                    draw.text((x_offset, current_y + 1), line, font=best_font, fill=text_color)
                
                draw.text((x_offset, current_y), line, font=best_font, fill=text_color)
                
                font_size = getattr(best_font, "size", 10)
                current_y += font_size * line_spacing_scale
        else:
            # Use default font (no size adjustment)
            font = renderer_instance.default_font if renderer_instance.default_font else ImageFont.load_default()
            draw.text((x_min, y_min), text, font=font, fill=text_color)

    # Convert back to OpenCV
    result_rgb = np.array(pil_img)
    result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
    return result_bgr
