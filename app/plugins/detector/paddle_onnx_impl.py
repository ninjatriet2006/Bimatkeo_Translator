import os
import cv2
import numpy as np
import logging
from app.core.ocr.interfaces import BaseTextDetector
from app.core.shared_registry import DetectorFactory

@DetectorFactory.register("paddle_onnx")
class PaddleONNXDetectorImpl(BaseTextDetector):
    MODELS = [
        {'key': 'paddle_onnx_v6_tiny', 'check_file': 'models/Detector/Paddle_ONNX/Tiny/inference.onnx', 'source': 'hf://PaddlePaddle/PP-OCRv6_tiny_det_onnx@inference.onnx'},
        {'key': 'paddle_onnx_v6_small', 'check_file': 'models/Detector/Paddle_ONNX/Small/inference.onnx', 'source': 'hf://PaddlePaddle/PP-OCRv6_small_det_onnx@inference.onnx'},
        {'key': 'paddle_onnx_v6_medium', 'check_file': 'models/Detector/Paddle_ONNX/Medium/inference.onnx', 'source': 'hf://PaddlePaddle/PP-OCRv6_medium_det_onnx@inference.onnx'},
    ]

    def __init__(self):
        self.session = None
        self.input_name = None
        self.config = {}
        
    def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
        self.config = kwargs
        try:
            import onnxruntime as ort
        except ImportError:
            raise RuntimeError("Thư viện 'onnxruntime' hoặc 'onnxruntime-gpu' chưa được cài đặt.")
            
        if not model_path or not os.path.exists(model_path):
            raise FileNotFoundError(f"Không tìm thấy model ONNX tại: {model_path}")
            
        try:
            # Try to use CUDA if available, otherwise CPU
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            if log_callback: log_callback("INFO", f"Đang khởi tạo PaddleONNX với trọng số tại: {model_path}")
            self.session = ort.InferenceSession(model_path, providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            if log_callback: log_callback("INFO", "Mô hình Paddle ONNX đã nạp thành công.")
        except Exception as e:
            raise RuntimeError(f"Lỗi khi khởi tạo Paddle ONNX: {e}")
            
    def _preprocess(self, img: np.ndarray, limit_type='max'):
        """
        Resize image and normalize for PP-OCR det.
        """
        limit_side_len = int(self.config.get('detection_size', 2048))
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
        
        # Ensure multiples of 32
        resize_h = max(round(resize_h / 32) * 32, 32)
        resize_w = max(round(resize_w / 32) * 32, 32)
        
        resized_img = cv2.resize(img, (resize_w, resize_h))
        
        # Normalize
        resized_img = resized_img.astype('float32') / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        resized_img -= mean
        resized_img /= std
        
        # HWC to CHW
        resized_img = resized_img.transpose((2, 0, 1))
        # Add batch dimension
        resized_img = np.expand_dims(resized_img, axis=0)
        return resized_img, (h, w), (resize_h, resize_w)

    def _boxes_from_bitmap(self, pred, _bitmap, dest_width, dest_height, box_thresh=0.6, unclip_ratio=1.5):
        """
        Extract bounding boxes from probability map.
        """
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
            points, sside = self._get_mini_boxes(contour)
            if sside < 3:
                continue
            points = np.array(points)
            
            # Unclip to expand bounding boxes (DB specific)
            if use_advanced_clipper and Polygon is not None and pyclipper is not None:
                poly = Polygon(points)
                distance = poly.area * unclip_ratio / poly.length
                offset = pyclipper.PyclipperOffset()  # type: ignore
                offset.AddPath(points, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)  # type: ignore
                expanded = np.array(offset.Execute(distance))
                if len(expanded) == 0:
                    continue
                expanded = expanded[0]
                box, sside = self._get_mini_boxes(expanded)
                if sside < 3 + 2:
                    continue
                points = np.array(box)
            else:
                # Basic expansion if shapely/pyclipper are missing
                rect = cv2.boundingRect(contour)
                x,y,w,h = rect
                expand = int(min(w,h) * 0.1)
                points = np.array([
                    [max(0, x-expand), max(0, y-expand)],
                    [min(width, x+w+expand), max(0, y-expand)],
                    [min(width, x+w+expand), min(height, y+h+expand)],
                    [max(0, x-expand), min(height, y+h+expand)]
                ])
                
            # Scale back to original image size
            points[:, 0] = np.clip(np.round(points[:, 0] / width * dest_width), 0, dest_width)
            points[:, 1] = np.clip(np.round(points[:, 1] / height * dest_height), 0, dest_height)
            
            polygons.append(points.astype(int).tolist())
            
            # Convert 4 points to top-left and bottom-right bbox
            xs = points[:, 0]
            ys = points[:, 1]
            boxes.append([int(np.min(xs)), int(np.min(ys)), int(np.max(xs)), int(np.max(ys))])
            
        return boxes, polygons
        
    def _get_mini_boxes(self, contour):
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

    def detect(self, image: np.ndarray) -> tuple[list[list[int]], list[list[list[int]]]]:
        if self.session is None: raise RuntimeError("Chưa nạp model Paddle ONNX.")
        
        # 1. Preprocess
        tensor, ori_shape, resize_shape = self._preprocess(image)
        
        # 2. Inference
        outputs = self.session.run(None, {self.input_name: tensor})
        preds = outputs[0]
        
        # 3. Postprocess
        text_threshold = float(self.config.get('text_threshold', 0.5))
        box_threshold = float(self.config.get('box_threshold', 0.7))
        unclip_ratio = float(self.config.get('unclip_ratio', 2.3))

        prob_map = preds[0, 0, :, :]
        bitmap = prob_map > text_threshold
        
        boxes, polygons = self._boxes_from_bitmap(prob_map, bitmap, ori_shape[1], ori_shape[0], box_thresh=box_threshold, unclip_ratio=unclip_ratio)
        
        return boxes, polygons
