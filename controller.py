import math
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from data_manager import DataManager, ProvenceItem, MEPolygonF, MEPolygonItem
import random as r
from command_manager import AddPointAfterCommand, AddPointBeforeCommand, AddPointCommand, MovePointCommand, PopPointCommand, AddCurrentPolygonCommand, AddPolygonCommand, DeletePolygonCommand, DeletePolygonPointCommand

from PySide6.QtWidgets import QGraphicsPolygonItem, QGraphicsView, QGraphicsPixmapItem, QRubberBand, QGraphicsItem, QGraphicsScene, QGraphicsLineItem, QWidget
from PySide6.QtGui import QPolygonF, QPen, QBrush, QColor, QPolygon, QUndoStack
from PySide6.QtCore import Qt, QPoint, QPointF, QRectF, QRect, QSize, Signal, QTimer, QLineF
import typing


class InteractiveGraphicsView(QGraphicsView):
    cursorMove = Signal(QPoint)

    def __init__(self, scene: QGraphicsScene, dataManager: DataManager, offset: int, size: int, parent:QWidget=None):
        super().__init__(scene, parent)
        self.dataManager = dataManager
        self.sceneOffset = offset
        self.sceneSize = size
        self.undoStack = QUndoStack(self)
        self.provence_level = list(filter(lambda item: isinstance(item, ProvenceItem), self.scene().items()))[0].zValue()

        self.rubberBand: QRubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()

        self.cursorMove.connect(self.updateCircle)
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.checkCursor)
        self.timer.start()
        self.current_scale = self.transform().scale(1, 1).mapRect(QRectF(0, 0, 1, 1)).width()
        self._cursorPos = self.cursor().pos()

        self._current_province_polygon = MEPolygonF()
        self._current_province = MEPolygonItem(self._current_province_polygon)
        self._current_province.setBrush(QBrush(QColor(150, 0, 150, 100)))
        self._current_province.setPen(QPen(QColor(150, 0, 150, 50)))
        self.scene().addItem(self._current_province)

        self.setRenderHints(self.renderHints())
        self.translation_step = 2500

        self.isSaveSelecting = False
        self.isF2Pressed = False
        self.isF3Pressed = False
        self.isConnectCircleVisible = False
        self.isF5Pressed = False

        self.isBackVisible = True
        self.isPolygonEdgeVisible = True
        self.isPolygonBodyVisible = True

        self.circle_radius = 35  # Фиксированный радиус
        self.circle_width = 3
        self.circle_scale = self.current_scale
        self.circle_item = MEPolygonItem()  # Круг-объект для визуализации
        self.circle_item.setZValue(self.provence_level + 1)
        self.circle_item.setPen(QPen(QColor(0, 255, 0, 150), self.circle_width, Qt.DashLine))
        self.circle_item.setBrush(QBrush(QColor(0, 0, 0, 0)))
        self.circle_item.setVisible(False)
        self.circle_item_polygon = self.generate_circle_polygon(self.mapToScene(QPoint()), self.circle_radius)
        self.circle_item.setPolygon(self.circle_item_polygon)
        self.scene().addItem(self.circle_item)
        
        self.closest_point_line = QGraphicsLineItem()
        self.line_width = self.circle_width + 3
        self.closest_point_line.setPen(QPen(QColor(0, 0, 150, 200), self.line_width))
        self.closest_point_line.setVisible(False)
        self.scene().addItem(self.closest_point_line)

        self.current_point_line = QGraphicsLineItem()
        self.current_point_line.setPen(QPen(QColor(0, 150, 150, 150), self.line_width))
        self.current_point_line.setVisible(False)
        self.scene().addItem(self.current_point_line)

        self.current_point_item = MEPolygonItem()
        self.current_point_item_pos = QPointF()
        self.current_point_item.setZValue(self.provence_level + 1)
        self.current_point_item_radius = 2
        self.current_point_item_sides = 9
        self.current_point_item.setPolygon(self.generate_circle_polygon(self.current_point_item_pos, self.current_point_item_radius, self.current_point_item_sides))
        self.current_point_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.current_point_item.setVisible(False)
        self.scene().addItem(self.current_point_item)
        self.dataItems = []


    def add_province_polygon(self, polygon: QPolygonF):
        """Update the polygon for the current province."""
        self.undoStack.push(AddCurrentPolygonCommand(self))

    def deleteProvince(self, province: ProvenceItem):
        self.undoStack.push(DeletePolygonCommand(self, province))

    def addPoint(self, position):
        """Add a point to the current province."""
        self.undoStack.push(AddPointCommand(self, position))

    def popPoint(self):
        self.undoStack.push(PopPointCommand(self))

    def selectingRect(self, rect: QRect, saveSelection: bool):
        condition = lambda item: QPolygonF(rect).intersects(item.polygon()) or (item.isSelected() and saveSelection)
        for item in filter(lambda item: isinstance(item, ProvenceItem), self.scene().items()):
            item.setSelected(condition(item))

    def selectPolygon(self, polygon: QPolygonF, saveSelection: bool):
        condition = lambda item: polygon.intersects(item.polygon()) or (item.isSelected() and saveSelection)
        for item in filter(lambda item: isinstance(item, ProvenceItem), self.scene().items()):
            item.setSelected(condition(item))

    def clearSelection(self, exceptionPolygonItem=None):
        if exceptionPolygonItem:
            old_sel = exceptionPolygonItem.isSelected() if len(self.scene().selectedItems()) == 1 else False
        self.scene().clearSelection()
        if exceptionPolygonItem:
            exceptionPolygonItem.setSelected(not old_sel)

    def updateCircle(self, position:QPoint|QPointF):
        if not self.isConnectCircleVisible:
            return

        radius = self.circle_radius / self.current_scale if self.current_scale < 1 else self.circle_radius
        width = self.circle_width / self.current_scale if self.current_scale else self.circle_width
        
        circle_polygon = self.generate_circle_polygon(position, radius, 24)
        self.circle_item.setPolygon(circle_polygon)        

        pen = self.circle_item.pen()
        pen.setWidthF(width)
        self.circle_item.setPen(pen)
        

        self.closest_point = None
        min_distance = radius

        for item in filter(lambda item: isinstance(item, ProvenceItem), self.scene().items(circle_polygon)):
            polygon = item.polygon()
            for point in polygon:
                if circle_polygon.containsPoint(point, Qt.OddEvenFill):
                    distance = math.hypot(position.x() - point.x(), position.y() - point.y())
                    if distance < min_distance:
                        self.closest_point = point.toPoint()
                        min_distance = distance

        if self.closest_point:
            self.closest_point_line.setLine(position.x(), position.y(), self.closest_point.x(), self.closest_point.y())
            self.closest_point_line.setVisible(True) if not self.closest_point_line.isVisible() else None
        else:
            self.closest_point_line.setVisible(False)

        if self.current_point_item_pos:
            if self.isF5Pressed:
                self.current_point_line.setLine(position.x(), position.y(), self.current_point_item_pos.x(), self.current_point_item_pos.y())
                self.current_point_line.setVisible(True) if not self.current_point_line.isVisible() else None
                self.current_point_item.setVisible(True) if not self.current_point_item.isVisible() else None
        else:
            self.current_point_line.setVisible(False)
            self.current_point_item.setVisible(False)

    def unitingProvinces(self):
        selectedItems = self.scene().selectedItems()

        if len(selectedItems) < 2:
            return

        def to_shapely_polygon(polygon: QPolygonF):
            points = [(point.x(), point.y()) for point in polygon]
            return Polygon(points)

        def from_shapely_polygon(polygon: Polygon):
            if polygon.is_empty:
                return QPolygonF()
            return QPolygonF([QPointF(x, y) for x, y in polygon.exterior.coords])

        shapely_polygons = [to_shapely_polygon(item.polygon()) for item in selectedItems]
        unified_polygon = unary_union(shapely_polygons)

        if isinstance(unified_polygon, MultiPolygon):
            unified_polygon = max(unified_polygon, key=lambda p: p.area)

        new_polygon_qt = from_shapely_polygon(unified_polygon)
        new_poly_item = ProvenceItem(new_polygon_qt)

        for item in selectedItems:
            self.deleteProvince(item)
        self.undoStack.push(AddPolygonCommand(self, new_poly_item))

    def _toggle_save_select(self):
        self.isSaveSelecting = not self.isSaveSelecting

    def sub_translation_step(self):
        self.translation_step -= 1 if self.translation_step > 10 else 0

    def add_translation_step(self):
        self.translation_step += 1 if self.translation_step < 250 else 0

    def _toggle_upload_map_data(self):
        self.dataManager.load_background(self.dataManager.pixoffset)
        self.dataManager.import_data(self.dataManager.pixoffset)

    def _toggle_save_jsons(self):
        self.timer.stop()
        self.dataManager.save_jsons()
        self.timer.start()

    def _toggle_delete(self):
        for item in self.scene().selectedItems():
            if isinstance(item, ProvenceItem):
                self.deleteProvince(item)
            elif item is self.current_point_item:
                self.undoStack.push(DeletePolygonPointCommand(self, self.current_point_item_pos, self.dataItems))

    def _toggle_polygon_body_visible(self):
        for item in filter(lambda item: isinstance(item, ProvenceItem), self.scene().items()):
            self.redrawPolygonBody(item)
        self.repaint()
        self.isPolygonBodyVisible = not self.isPolygonBodyVisible

    def _toggle_polygon_edge_visible(self):
        for item in filter(lambda item: isinstance(item, ProvenceItem), self.scene().items()):
            self.redrawPolygonEdge(item)
        self.repaint()
        self.isPolygonEdgeVisible = not self.isPolygonEdgeVisible

    def _toggle_background_visible(self):
        for item in filter(lambda item: isinstance(item, QGraphicsPixmapItem), self.scene().items()):
            item.setVisible(not self.isBackVisible)
        self.repaint()
        self.isBackVisible = not self.isBackVisible

    def selection_from_current_polygon(self):
        self.selectPolygon(self.current_province_polygon, self.isSaveSelecting)
        self.current_province_polygon.clear()
        self._current_province.setPolygon(self.current_province_polygon)

    def _toggle_clear_selection(self):
        self.clearSelection()
        self.current_province_polygon.clear()
        self._current_province.setPolygon(self.current_province_polygon)

    def sub_circle_radius(self):
        if self.circle_radius > 0:
            self.circle_radius -= 1
            self.updateCircle(self._cursorPos)

    def add_circle_radius(self):
        if self.circle_radius < 150:
            self.circle_radius += 1
            self.updateCircle(self._cursorPos)

    def _toggle_select_current_point(self):
        current_point_item_pos = None if self.isF5Pressed else self.current_point_item_pos
        self.isF5Pressed = not self.isF5Pressed
        # self.current_point_item.setVisible(self.isF5Pressed)
        self.current_point_item.setFlag(QGraphicsItem.ItemIsMovable, self.isF5Pressed)
        self.current_point_item.setPos(QPointF() if not self.isF5Pressed else current_point_item_pos) 
        self.current_point_line.setVisible(self.isF5Pressed)
        self.updateCircle(self._cursorPos)

    def _toggle_circle_visible(self):
        self.isConnectCircleVisible = not self.isConnectCircleVisible
        self.circle_item.setVisible(self.isConnectCircleVisible)
        self.closest_point_line.setVisible(self.isConnectCircleVisible)
        self.current_point_line.setVisible(self.isConnectCircleVisible & self.isF5Pressed)
        self.updateCircle(self._cursorPos)
        
    def add_polygon_point_before_current(self):
        # self.undoStack.push(AddPointBeforeCommand(self, self.gen_new_point(self.current_point_item_pos), list(filter(lambda data: data['item'] in self.scene().selectedItems(), self.dataItems)))) if self.dataItems else None
        ...
    def add_polygon_point_after_current(self):
        # self.undoStack.push(AddPointAfterCommand(self, self.gen_new_point(self.current_point_item_pos), list(filter(lambda data: data['item'] in self.scene().selectedItems(), self.dataItems)))) if self.dataItems else None
        ...
    def merge_current_and_closest_points(self):
        ...

    
    def gen_new_point(self, point:QPointF=None):
        theta = r.random() * 2 * math.pi
        radius = math.sqrt(r.random() * self.circle_radius)
        new_point = QPointF(radius * math.cos(theta), radius * math.sin(theta))
        return new_point if point is None else point + new_point
                    
    def keyPressEvent(self, event):
        vertical_bar = self.verticalScrollBar()
        horizontal_bar = self.horizontalScrollBar()
        
        handler = {
            Qt.Key_Up: lambda: vertical_bar.setValue(vertical_bar.value() - self.translation_step),
            Qt.Key_W: lambda: vertical_bar.setValue(vertical_bar.value() - self.translation_step),
            Qt.Key_Down: lambda: vertical_bar.setValue(vertical_bar.value() + self.translation_step),
            Qt.Key_S: lambda: vertical_bar.setValue(vertical_bar.value() + self.translation_step),
            Qt.Key_Left: lambda: horizontal_bar.setValue(horizontal_bar.value() - self.translation_step),
            Qt.Key_A: lambda: horizontal_bar.setValue(horizontal_bar.value() - self.translation_step),
            Qt.Key_Right: lambda: horizontal_bar.setValue(horizontal_bar.value() + self.translation_step),
            Qt.Key_D: lambda: horizontal_bar.setValue(horizontal_bar.value() + self.translation_step),
            Qt.Key_Equal: self.add_circle_radius if event.modifiers() & Qt.ControlModifier else self.add_translation_step,
            Qt.Key_Minus: self.sub_circle_radius if event.modifiers() & Qt.ControlModifier else self.sub_translation_step,
            Qt.Key_F1: self._toggle_clear_selection if event.modifiers() & Qt.ShiftModifier else (self.selection_from_current_polygon if event.modifiers() & Qt.ControlModifier else self._toggle_save_select),
            Qt.Key_F2: self._toggle_select_current_point if event.modifiers() & Qt.ControlModifier else self._toggle_circle_visible,
            Qt.Key_F3: self.merge_current_and_closest_points if event.modifiers() & Qt.ControlModifier else self.unitingProvinces,
            Qt.Key_F4: self.add_polygon_point_before_current if event.modifiers() & Qt.ShiftModifier else self.add_polygon_point_after_current,
            Qt.Key_F5: ...,
            Qt.Key_F6: ...,
            Qt.Key_F7: ...,
            Qt.Key_F8: ...,
            Qt.Key_F9: ...,
            Qt.Key_F10: ...,
            Qt.Key_F11: ...,
            Qt.Key_F12: ...,
            Qt.Key_1: self._toggle_background_visible,
            Qt.Key_2: self._toggle_polygon_edge_visible,
            Qt.Key_3: self._toggle_polygon_body_visible,
            Qt.Key_Delete: self._toggle_delete,
            Qt.Key_Backspace: self.popPoint,
            Qt.Key_Space: lambda: self.add_province_polygon(self.current_province),
            Qt.Key_Z: lambda: self.undoStack.undo() if event.modifiers() & Qt.ControlModifier else None,
            Qt.Key_Y: lambda: self.undoStack.redo() if event.modifiers() & Qt.ControlModifier else None,
            Qt.Key_S: self._toggle_save_jsons if event.modifiers() & Qt.ControlModifier else None,
            Qt.Key_O: self._toggle_upload_map_data if event.modifiers() & Qt.ControlModifier else None
        }.get(event.key(), None)
        
        handler() if isinstance(handler, typing.Callable) else super().keyPressEvent(event)
            
    def mouseMoveEvent(self, event):
        button = event.buttons()
        x = event.x()
        y = event.y()
        self.dx = -(x - self.old_x)
        self.dy = -(y - self.old_y)
        handle = {
            Qt.LeftButton: lambda: self.handle_move_left_button(event),
            Qt.RightButton: self.handle_move_right_button,
            Qt.MiddleButton: ...
        }.get(button, None)
        
        handle() if isinstance(handle, typing.Callable) else super().mouseMoveEvent(event)
        
        self.old_x = x
        self.old_y = y

    def handle_move_right_button(self):
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        pos = self.current_point_item.pos()
        self.undoStack.push(MovePointCommand(self, QPointF(self.old_x, self.old_y), pos - QPointF(self.dx, self.dy) / self.current_scale, self.dataItems)) \
                if self.current_point_item.isSelected() else self.scroll_bar_by(self.dx, self.dy)

    def handle_move_left_button(self, event):
        if not self.origin.isNull() and not self.isF5Pressed:
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.rubberBand.setGeometry(QRect(self.origin.toPoint(), event.position().toPoint()).normalized())

    def scroll_bar_by(self, dx, dy):
        vertical_bar = self.verticalScrollBar()
        horizontal_bar = self.horizontalScrollBar()
        vertical_bar.setValue(vertical_bar.value() + dy)
        horizontal_bar.setValue(horizontal_bar.value() + dx)


    def mousePressEvent(self, event):
        self.old_x = event.x()
        self.old_y = event.y()
        
        handle = {
            Qt.LeftButton: lambda:self.handle_press_left_button(event),
            Qt.RightButton: lambda:self.handle_press_right_button(event),
            Qt.MiddleButton: ...
        }.get(event.button(), None)
        
        handle() if isinstance(handle, typing.Callable) else super().mousePressEvent(event)

    def handle_press_right_button(self, event):
        handle = {
            self.isConnectCircleVisible: lambda: self.addPoint(self.closest_point) if (not self.closest_point is None) &\
                (not (self.isSaveSelecting or self.isF5Pressed)) else None,
            self.isSaveSelecting: lambda: self.addPoint(self.mapToScene(event.position().toPoint()).toPoint()) if not self.isConnectCircleVisible else None,
        }.get(True, None)
        
        handle() if isinstance(handle, typing.Callable) else None

    def handle_press_left_button(self, event):
        self.origin = QPointF(event.position())
        self.rubberBand.setGeometry(QRect())
        self.rubberBand.show()
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseDoubleClickEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        handle = {
            Qt.LeftButton: lambda:self.handle_double_left_button(event),
            Qt.MiddleButton: ...,
            Qt.RightButton: ...
        }.get(event.button(), None)

        handle() if isinstance(handle, typing.Callable) else super().mouseDoubleClickEvent(event)
        
    def handle_double_left_button(self, event):
        if self.isF5Pressed and self.isConnectCircleVisible:
            self.handle_selecting_point(event.position())
        else:
            self.select_item(event.position())

    def select_item(self, position:QPointF):
        pos = self.mapToScene(position.toPoint()).toPoint()
        item = self.scene().itemAt(pos, self.transform())
        self.clearSelection(item) if not self.isSaveSelecting else item.setSelected(not item.isSelected())

    def handle_selecting_point(self, position:QPointF):
        pos = self.mapToScene(position.toPoint())
        item = self.scene().itemAt(pos, self.transform())
        if item and self.closest_point:
            self.current_point_item_old_pos = self.current_point_item_pos = QPointF(self.closest_point)
            self.current_point_item.setPos(self.current_point_item_pos)
            current_point_colliding = list(filter(lambda item: isinstance(item, ProvenceItem), self.current_point_item.collidingItems()))
            self.dataItems:list[dict[str, typing.Any]] = []
            for item in current_point_colliding:
                polygon = item.Polygon
                indexes = [i for i, p in enumerate(polygon) if ((p == self.current_point_item_pos)) | ((p - self.current_point_item_pos).manhattanLength() <= self.current_point_item_radius)]
                if indexes:
                    self.dataItems.append({
                                'item': item,
                                'indexes': indexes,
                                'original_polygon': MEPolygonF(polygon)
                            })
            self.current_point_item.setSelected(True)
        self.updateCircle(self.mapToScene(position.toPoint()))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rubberBand.hide()
            if (self.origin - event.position()).manhattanLength() > 10:
                self.selectPolygon(self.mapToScene(self.rubberBand.geometry()), self.isSaveSelecting)
            else:
                super().mouseReleaseEvent(event)
        elif event.button() == Qt.RightButton:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            if not self.isPolygonBodyVisible:
                pos = self.mapToScene(event.position().toPoint()).toPoint()
                self.addPoint(pos)

    def wheelEvent(self, event):
        self.scaleView(math.pow(2.0, event.angleDelta().y() / 240.0))
        if self.current_scale is None:
            self.current_scale = math.pow(2.0, event.angleDelta().y() / 240.0)

    def scaleView(self, scaleFactor):
        self.current_scale = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()
        if self.current_scale < 0.07 or self.current_scale > 100:
            return
        self.scale(scaleFactor, scaleFactor)
        
        self.scaleCircle(self.current_scale)

    def scaleCircle(self, scale):
        # print(self.mapToScene(self.current_point_item.Polygon.toPolygon()))
        width = self.line_width / scale if scale else self.line_width
        
        pen = self.closest_point_line.pen()
        pen.setWidthF(width) if scale < 1 else None
        self.closest_point_line.setPen(pen)
        
        pen = self.current_point_line.pen()
        pen.setWidthF(width) if scale < 1 else None
        self.current_point_line.setPen(pen)

        pen = self.circle_item.pen()
        pen.setWidthF(float(self.circle_width / scale))
        self.circle_item.setPen(pen)


    def checkCursor(self):
        pos = self.mapToScene(self.cursor().pos() - QPoint(0, 25)).toPoint() if self.geometry().contains(self.cursor().pos(), True) else None
        if (pos != self._cursorPos) and pos is not None:
            self._cursorPos = pos  
            self.cursorMove.emit(pos)
            # self._cursorPos = pos
            # self.cursorMove.emit(pos)

    def redrawPolygonEdge(self, item):
        if self.isPolygonEdgeVisible:
            item.setPen(QPen(QColor(0, 0, 0, 0)))
        else:
            item.setPen(QPen(Qt.red))

    def redrawPolygonBody(self, item):
        if self.isPolygonBodyVisible:
            item.setBrush(QBrush(QColor(0, 0, 0, 0)))
        else:
            item.setBrush(QBrush(self.QRColor()))

    @property
    def current_province_polygon(self):
        return self._current_province_polygon

    @current_province_polygon.setter
    def current_province_polygon(self, value: QPolygonF):
        self._current_province_polygon = value

    @property
    def current_province(self):
        return self._current_province

    @current_province.setter
    def current_province(self, value: MEPolygonItem):
        self._current_province = value

    @staticmethod
    def generate_circle_polygon(center: QPointF, radius: float, sides: int = 24):
        if sides < 3:
            raise ValueError("A polygon must have at least 3 sides.")

        angle_step = 2 * math.pi / sides
        points = [
            QPointF(
                center.x() + radius * math.cos(i * angle_step),
                center.y() + radius * math.sin(i * angle_step)
            )
            for i in range(sides)
        ]
        return MEPolygonF(points)

    def QRColor(self):
        return QColor(r.randint(20, 255), r.randint(20, 255), r.randint(20, 255), 70)