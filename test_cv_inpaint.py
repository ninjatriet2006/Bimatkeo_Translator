import cv2
import numpy as np

# Create a gradient image
img = np.zeros((1000, 1000, 3), dtype=np.uint8)
for i in range(1000):
    img[:, i] = (i % 255, 0, 0)

# Create a mask that is almost the whole image
mask = np.zeros((1000, 1000), dtype=np.uint8)
mask[10:990, 10:990] = 255

out = cv2.inpaint(img, mask, 5, cv2.INPAINT_TELEA)
cv2.imwrite("test_streak.png", out)
