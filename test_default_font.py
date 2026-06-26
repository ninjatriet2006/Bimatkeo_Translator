from PIL import Image, ImageDraw, ImageFont
import numpy as np

box_width = 380
box_height = 306
text = "Cậu thực sự đang tiết sữa sao? Cái cơ thể dâm đãng này vừa mới chịch có vài lần mà đã tiết sữa rồi. Quên chuyện làm Tướng quân đi, cậu nên trở thành tiên bò sữa đi, hahaha!"

pil_img = Image.new("RGB", (800, 800), color="white")
draw = ImageDraw.Draw(pil_img)

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

font = ImageFont.load_default()
lines = _wrap_text(text, font, box_width, draw)
print(f"Lines length: {len(lines)}")
best_y_offset = max(0, (box_height - (10 * 1.2 * len(lines))) / 2)
print(f"best_y_offset: {best_y_offset}")

draw.rectangle([30, 245, 410, 551], outline="red")
current_y = 245 + best_y_offset
for line in lines:
    line_width = draw.textlength(line, font=font)
    x_offset = 30 + (box_width - line_width) / 2
    draw.text((x_offset, current_y), line, font=font, fill="black")
    current_y += 12

pil_img.save("test_default_font.png")
