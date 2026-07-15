"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.preview_widgets.interactive_canvas
- RESPONSIBILITY: Provide a unified QGraphicsView for previewing and interacting with bounding boxes.
- CALLED BY: app.core.desktop.components.preview_panel
- CALLS TO: None
- IN = OUT: Defines the canvas view and graphics items.
=============================================================================
"""
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPen, QColor, QBrush, QPixmap

class BBoxGraphicsItem(QGraphicsRectItem):
    def __init__(self, box_id, rect, parent=None):
        super().__init__(rect, parent)
        self.box_id = box_id
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self._setup_style()
        self.original_rect = rect

    def _setup_style(self):
        pen = QPen(QColor(0, 255, 0, 200))
        pen.setWidth(2)
        self.setPen(pen)
        brush = QBrush(QColor(0, 255, 0, 50))
        self.setBrush(brush)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value:
                self.setPen(QPen(QColor(255, 0, 0, 255), 3))
                self.setBrush(QBrush(QColor(255, 0, 0, 80)))
            else:
                self._setup_style()
        return super().itemChange(change, value)

class InteractivePreviewCanvas(QGraphicsView):
    box_selected = Signal(int)
    box_moved = Signal(int, QRectF)
    box_created = Signal(QRectF)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_obj = QGraphicsScene(self)
        self.setScene(self.scene_obj)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        self.base_layer = QGraphicsPixmapItem()
        self.rendered_layer = QGraphicsPixmapItem()
        
        self.scene_obj.addItem(self.base_layer)
        self.scene_obj.addItem(self.rendered_layer)
        self.rendered_layer.setZValue(1)
        
        self.bboxes = {} # id -> BBoxGraphicsItem
        self.selected_box_index = -1
        self.scene_obj.selectionChanged.connect(self._on_selection_changed)
        
        # Drawing tools
        self.current_mode = "select" # "select" or "draw"
        self.temp_rect_item = None
        self.start_point = None

    def set_mode(self, mode: str):
        self.current_mode = mode
        if mode == "draw":
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if self.current_mode == "draw" and event.button() == Qt.MouseButton.LeftButton:
            self.start_point = self.mapToScene(event.pos())
            self.temp_rect_item = QGraphicsRectItem(QRectF(self.start_point, self.start_point))
            self.temp_rect_item.setPen(QPen(QColor(0, 0, 255, 200), 2, Qt.PenStyle.DashLine))
            self.temp_rect_item.setBrush(QBrush(QColor(0, 0, 255, 50)))
            self.temp_rect_item.setZValue(3)
            self.scene_obj.addItem(self.temp_rect_item)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.current_mode == "draw" and self.temp_rect_item and self.start_point:
            end_point = self.mapToScene(event.pos())
            rect = QRectF(self.start_point, end_point).normalized()
            self.temp_rect_item.setRect(rect)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.current_mode == "draw" and event.button() == Qt.MouseButton.LeftButton:
            if self.temp_rect_item:
                rect = self.temp_rect_item.rect()
                self.scene_obj.removeItem(self.temp_rect_item)
                self.temp_rect_item = None
                self.start_point = None
                
                # Only emit if the box is big enough
                if rect.width() > 10 and rect.height() > 10:
                    self.box_created.emit(rect)
        else:
            super().mouseReleaseEvent(event)

    def set_base_image(self, pixmap: QPixmap):
        self.base_layer.setPixmap(pixmap)
        self.setSceneRect(self.base_layer.boundingRect())

    def set_rendered_image(self, pixmap: QPixmap):
        self.rendered_layer.setPixmap(pixmap)

    def set_rendered_visible(self, visible: bool):
        self.rendered_layer.setVisible(visible)

    def add_boxes(self, boxes_data: list):
        self.clear_boxes()
        for i, bbox in enumerate(boxes_data):
            x, y, w, h = bbox
            rect = QRectF(x, y, w, h)
            item = BBoxGraphicsItem(i, rect)
            item.setZValue(2)
            self.scene_obj.addItem(item)
            self.bboxes[i] = item

    def clear_boxes(self):
        for item in self.bboxes.values():
            self.scene_obj.removeItem(item)
        self.bboxes.clear()

    def set_boxes_visible(self, visible: bool):
        for item in self.bboxes.values():
            item.setVisible(visible)

    def _on_selection_changed(self):
        selected = self.scene_obj.selectedItems()
        if selected and isinstance(selected[0], BBoxGraphicsItem):
            self.selected_box_index = selected[0].box_id
            self.box_selected.emit(self.selected_box_index)
        else:
            self.selected_box_index = -1
            self.box_selected.emit(-1)
