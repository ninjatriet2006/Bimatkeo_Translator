from PIL import ImageFont
try:
    font = ImageFont.truetype("Ubuntu-R.ttf", 50)
    print("Has size?", hasattr(font, "size"))
    print("Size:", getattr(font, "size", None))
except Exception as e:
    print(e)
    # fall back to a system font just for test
    font = ImageFont.load_default()
    print("Has size?", hasattr(font, "size"))
    print("Size:", getattr(font, "size", None))
