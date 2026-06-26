from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

def _wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    if not words:
        return lines
        
    current_line = words[0]
    for word in words[1:]:
        test_line = current_line + " " + word
        length = draw.textlength(test_line, font=font)
        if length <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines

# Simulate BBOX
box_width = 380
box_height = 306
text = "Cậu thực sự đang tiết sữa sao? Cái cơ thể dâm đãng này vừa mới chịch có vài lần mà đã tiết sữa rồi. Quên chuyện làm Tướng quân đi, cậu nên trở thành tiên bò sữa đi, hahaha!"

pil_img = Image.new("RGB", (800, 800), color="white")
draw = ImageDraw.Draw(pil_img)
font_path = "app/assets/fonts/manga_font.ttf" # Or whatever is the default
try:
    f = ImageFont.truetype(font_path, 20)
except:
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

min_size = 10
max_size = min(int(box_height), 150)
best_font = None
best_lines = []
best_y_offset = 0

print(f"Start binary search: min={min_size}, max={max_size}")
while min_size <= max_size:
    mid_size = (min_size + max_size) // 2
    try:
        font = ImageFont.truetype(font_path, mid_size)
    except Exception as e:
        print("Font error", e)
        break
        
    lines = _wrap_text(text, font, box_width, draw)
    line_height = mid_size * 1.2
    total_height = line_height * len(lines)
    max_line_width = max([draw.textlength(line, font=font) for line in lines] + [0])
    
    print(f"Testing size {mid_size}: total_height={total_height}, max_line_width={max_line_width}")
    
    if total_height <= box_height and max_line_width <= box_width:
        best_font = font
        best_lines = lines
        best_y_offset = (box_height - total_height) / 2
        min_size = mid_size + 1
        print(" -> Fits!")
    else:
        max_size = mid_size - 1
        print(" -> Too big!")

print("Best font size:", getattr(best_font, "size", None))
