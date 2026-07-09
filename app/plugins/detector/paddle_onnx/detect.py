"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.detector.paddle_onnx.detect
- RESPONSIBILITY: Tiền xử lý, chạy inference ONNX và hậu xử lý trích xuất boxes.
- CALLED BY: app.plugins.detector.paddle_onnx.main_impl
- CALLS TO: None
- IN = OUT: Nhận session, image, trả về list các bounding box.
=============================================================================
"""
import cv2
import numpy as np
import logging

def _preprocess(img: np.ndarray, config: dict, limit_type='max'):
    limit_side_len = int(config.get('detection_size', 2048))
    h, w, _ = img.shape
    
    if limit_type == 'max':
        if max(h, w) > limit_side_len:
            if h > w:
                ratio = float(limit_side_len) / h
            else:
                ratio = float(limit_side_len) / w
        else:
            ratio = 1.
    else:
        ratio = 1.
        
    resize_h = int(h * ratio)
    resize_w = int(w * ratio)
    
    resize_h = max(round(resize_h / 32) * 32, 32)
    resize_w = max(round(resize_w / 32) * 32, 32)
    
    resized_img = cv2.resize(img, (resize_w, resize_h))
    
    resized_img = resized_img.astype('float32') / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    resized_img -= mean
    resized_img /= std
    
    resized_img = resized_img.transpose((2, 0, 1))
    resized_img = np.expand_dims(resized_img, axis=0)
    return resized_img, (h, w), (resize_h, resize_w)

def _get_mini_boxes(contour):
    bounding_box = cv2.minAreaRect(contour)
    points = sorted(list(cv2.boxPoints(bounding_box)), key=lambda x: x[0])
    index_1, index_2, index_3, index_4 = 0, 1, 2, 3
    if points[1][1] > points[0][1]:
        index_1 = 0
        index_4 = 1
    else:
        index_1 = 1
        index_4 = 0
    if points[3][1] > points[2][1]:
        index_2 = 2
        index_3 = 3
    else:
        index_2 = 3
        index_3 = 2
    box = [points[index_1], points[index_2], points[index_3], points[index_4]]
    return box, min(bounding_box[1])

def _boxes_from_bitmap(_bitmap, dest_width, dest_height, box_thresh=0.6, unclip_ratio=1.5):
    Polygon = None
    pyclipper = None
    try:
        from shapely.geometry import Polygon
        import pyclipper
        use_advanced_clipper = True
    except ImportError:
        use_advanced_clipper = False
        logging.warning("pyclipper or shapely not found. Box extraction will be less accurate. Install 'shapely pyclipper'.")
        
    bitmap = _bitmap
    height, width = bitmap.shape

    contours, _ = cv2.findContours((bitmap * 255).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    num_contours = min(len(contours), 1000)
    boxes = []
    polygons = []
    for index in range(num_contours):
        contour = contours[index]
        points, sside = _get_mini_boxes(contour)
        if sside < 3:
            continue
        points = np.array(points)
        
        if use_advanced_clipper and Polygon is not None and pyclipper is not None:
            poly = Polygon(points)
            distance = poly.area * unclip_ratio / poly.length
            offset = pyclipper.PyclipperOffset()  # type: ignore
            offset.AddPath(points, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)  # type: ignore
            expanded = np.array(offset.Execute(distance))
            if len(expanded) == 0:
                continue
            expanded = expanded[0]
            box, sside = _get_mini_boxes(expanded)
            if sside < 3 + 2:
                continue
            points = np.array(box)
        else:
            rect = cv2.boundingRect(contour)
            x,y,w,h = rect
            expand = int(min(w,h) * 0.1)
            points = np.array([
                [max(0, x-expand), max(0, y-expand)],
                [min(width, x+w+expand), max(0, y-expand)],
                [min(width, x+w+expand), min(height, y+h+expand)],
                [max(0, x-expand), min(height, y+h+expand)]
            ])
            
        points[:, 0] = np.clip(np.round(points[:, 0] / width * dest_width), 0, dest_width)
        points[:, 1] = np.clip(np.round(points[:, 1] / height * dest_height), 0, dest_height)
        
        polygons.append(points.astype(int).tolist())
        xs = points[:, 0]
        ys = points[:, 1]
        boxes.append([int(np.min(xs)), int(np.min(ys)), int(np.max(xs)), int(np.max(ys))])
        
    return boxes, polygons

def detect_text_paddle_onnx(session, input_name, config, image: np.ndarray) -> tuple[list[list[int]], list[list[list[int]]]]:
    if session is None: 
        raise RuntimeError("Chưa nạp model Paddle ONNX.")
    
    tensor, ori_shape, resize_shape = _preprocess(image, config)
    
    outputs = session.run(None, {input_name: tensor})
    preds = outputs[0]
    
    text_threshold = float(config.get('text_threshold', 0.5))
    box_threshold = float(config.get('box_threshold', 0.7))
    unclip_ratio = float(config.get('unclip_ratio', 2.3))

    prob_map = preds[0, 0, :, :]
    bitmap = prob_map > text_threshold
    
    boxes, polygons = _boxes_from_bitmap(prob_map, ori_shape[1], ori_shape[0], box_thresh=box_threshold, unclip_ratio=unclip_ratio)
    return boxes, polygons
