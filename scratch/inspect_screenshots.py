from PIL import Image
import glob
import os

images = glob.glob("scratch/screenshots/popup_*.png")
for img_path in sorted(images):
    img = Image.open(img_path)
    width, height = img.size
    # Let's get the color at (2, 2) which is near the border corner
    # and (20, 40) which is inside the list widget area
    color_corner = img.getpixel((2, 2))
    color_inside = img.getpixel((20, 60))
    print(f"{os.path.basename(img_path)}: Size={width}x{height}, Corner color={color_corner}, Inside color={color_inside}")
