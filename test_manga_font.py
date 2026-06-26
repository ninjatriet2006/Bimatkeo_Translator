from PIL import Image, ImageDraw, ImageFont
import numpy as np

pil_img = Image.new("RGB", (800, 200), color="white")
draw = ImageDraw.Draw(pil_img)
font_path = "app/assets/fonts/manga_font.ttf"
try:
    font = ImageFont.truetype(font_path, 40)
    text = "Cậu thực sự đang tiết sữa sao?"
    draw.text((10, 10), text, font=font, fill="black")
    pil_img.save("test_manga_vi.png")
    print("Length:", draw.textlength(text, font=font))
except Exception as e:
    print(e)
