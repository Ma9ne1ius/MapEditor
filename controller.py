import math
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from data_manager import DataManager, ProvenceItem, QPolygonFS
import random as r
from command_manager import AddPointCommand, MovePointCommand, PopPointCommand, AddCurrentPolygonCommand, AddPolygonCommand, DeletePolygonCommand

from PyQt5.QtWidgets import QGraphicsPolygonItem, QGraphicsView, QGraphicsPixmapItem, QRubberBand, QUndoStack, QGraphicsItem, QGraphicsScene, QGraphicsLineItem
from PyQt5.QtGui import QPolygonF, QPen, QBrush, QColor, QPolygon
from PyQt5.QtCore import Qt, QPoint, QPointF, QRectF, QRect, QSize, pyqtSignal, QTimer
import typing


class InteractiveGraphicsView(QGraphicsView):
    cursorMove = pyqtSignal(QPoint)

    def __init__(self, scene: QGraphicsScene, dataManager: DataManager, offset: int, size: int):
        super().__init__(scene)
        self.dataManager = dataManager
        self.sceneOffset = offset
        self.sceneSize = size
        self.undoStack = QUndoStack(self)

        self.rubberBand: QRubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()

        self._current_province = QPolygonF()
        self._cp_item = QGraphicsPolygonItem(self._current_province)
        self._cp_item.setBrush(QBrush(QColor(150, 0, 150, 100)))
        self._cp_item.setPen(QPen(QColor(150, 0, 150, 50)))
        self.scene().addItem(self._cp_item)

        self.setRenderHints(self.renderHints())
        self.translation_step = 2500
        self.scaleFactor = 1

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
        self.circle_item = QGraphicsPolygonItem()  # Круг-объект для визуализации
        self.circle_item.setZValue(2)
        self.circle_item.setPen(QPen(QColor(0, 255, 0, 150), self.circle_width, Qt.DashLine))
        self.circle_item.setBrush(QBrush(QColor(0, 0, 0, 0)))
        self.circle_item.setVisible(False)
        self.scene().addItem(self.circle_item)

        self.closest_point_line = QGraphicsLineItem()
        self.closest_point_line.setPen(QPen(QColor(0, 0, 150, 150), self.circle_width))
        self.closest_point_line.setVisible(False)
        self.scene().addItem(self.closest_point_line)

        self.current_point_line = QGraphicsLineItem()
        self.current_point_line.setPen(QPen(QColor(0, 150, 150, 150), self.circle_width))
        self.current_point_line.setVisible(False)
        self.scene().addItem(self.current_point_line)

        self.current_point_item = QGraphicsPolygonItem()
        self.cpi_pos = QPointF()
        self.cpi_radius = 2
        self.cpi_sides = 8
        self.current_point_item.setPolygon(self.generate_circle_polygon(self.cpi_pos, self.cpi_radius, self.cpi_sides))
        self.current_point_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        # self.current_point_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        # self.current_point_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.current_point_item.setVisible(False)
        self.scene().addItem(self.current_point_item)

        self.cursorMove.connect(self.updateCircle)
        self.timer = QTimer(self)
        self.timer.setInterval(15)
        self.timer.timeout.connect(self.checkCursor)
        self.timer.start()
        self._cursorPos = self.cursor().pos()
        self.current_point_enum: list[tuple[int, QPolygonFS]] = []

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

    def updateCircle(self, position):
        if not self.isConnectCircleVisible:
            return

        radius = self.circle_radius / self.scaleFactor if self.scaleFactor else self.circle_radius
        width = self.circle_width / self.scaleFactor if self.scaleFactor else self.circle_width
        pen = self.circle_item.pen()
        pen.setWidthF(width)
        pen1 = self.closest_point_line.pen()
        pen1.setWidthF(width)

        circle_polygon = self.generate_circle_polygon(position, radius, 24)
        self.circle_item.setPolygon(circle_polygon)
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
            self.closest_point_line.setVisible(True)
        else:
            self.closest_point_line.setVisible(False)

        if self.cpi_pos:
            self.current_point_line.setLine(position.x(), position.y(), self.cpi_pos.x(), self.cpi_pos.y())
            self.current_point_line.setVisible(True)
            self.current_point_item.setVisible(True)
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

    def keyPressEvent(self, event):
        vertical_bar = self.verticalScrollBar()
        horizontal_bar = self.horizontalScrollBar()

        match event.key():
            case Qt.Key_Up | Qt.Key_W:
                vertical_bar.setValue(vertical_bar.value() - self.translation_step)
            case Qt.Key_Down | Qt.Key_S:
                vertical_bar.setValue(vertical_bar.value() + self.translation_step)
            case Qt.Key_Left | Qt.Key_A:
                horizontal_bar.setValue(horizontal_bar.value() - self.translation_step)
            case Qt.Key_Right | Qt.Key_D:
                horizontal_bar.setValue(horizontal_bar.value() + self.translation_step)
            case Qt.Key_Equal:
                if self.translation_step < 250:
                    self.translation_step += 1
            case Qt.Key_Minus:
                if self.translation_step > 10:
                    self.translation_step -= 1
            case Qt.Key_Plus:
                if self.circle_radius < 150:
                    self.circle_radius += 1
                    self.updateCircle(self._cursorPos)
            case Qt.Key_Underscore:
                if self.circle_radius > 0:
                    self.circle_radius -= 1
                    self.updateCircle(self._cursorPos)
            case Qt.Key_F1:
                self.isSaveSelecting = not self.isSaveSelecting
            case Qt.Key_F2:
                self.clearSelection()
                self.current_province.clear()
                self._cp_item.setPolygon(self.current_province)
            case Qt.Key_F3:
                self.selectPolygon(self.current_province, self.isSaveSelecting)
                self.current_province.clear()
                self._cp_item.setPolygon(self.current_province)
            case Qt.Key_F4:
                self.isConnectCircleVisible = not self.isConnectCircleVisible
                self.circle_item.setVisible(self.isConnectCircleVisible)
                self.closest_point_line.setVisible(self.isConnectCircleVisible)
                self.current_point_line.setVisible(self.isConnectCircleVisible)
            case Qt.Key_F5:
                self.cpi_pos = None if self.isF5Pressed else self.cpi_pos
                self.isF5Pressed = not self.isF5Pressed
                self.current_point_item.setVisible(self.isF5Pressed)
                self.current_point_item.setFlag(QGraphicsItem.ItemIsMovable, self.isF5Pressed)
                self.current_point_item.setPos(QPointF()) if not self.isF5Pressed else None
                self.updateCircle(self._cursorPos)
            case Qt.Key_F6:
                self.unitingProvinces()
            case Qt.Key_1:
                for item in filter(lambda item: isinstance(item, QGraphicsPixmapItem), self.scene().items()):
                    item.setVisible(not self.isBackVisible)
                self.repaint()
                self.isBackVisible = not self.isBackVisible
            case Qt.Key_2:
                for item in filter(lambda item: isinstance(item, ProvenceItem), self.scene().items()):
                    self.redrawPolygonEdge(item)
                self.repaint()
                self.isPolygonEdgeVisible = not self.isPolygonEdgeVisible
            case Qt.Key_3:
                for item in filter(lambda item: isinstance(item, ProvenceItem), self.scene().items()):
                    self.redrawPolygonBody(item)
                self.repaint()
                self.isPolygonBodyVisible = not self.isPolygonBodyVisible
            case Qt.Key_Delete:
                for item in self.scene().selectedItems():
                    self.deleteProvince(item)
                self.repaint()
            case Qt.Key_Backspace:
                self.popPoint()
            case Qt.Key_Space:
                self.add_province_polygon(self.current_province)
            case Qt.Key_Z:
                if event.modifiers() & Qt.ControlModifier:
                    self.undoStack.undo()
            case Qt.Key_Y:
                if event.modifiers() & Qt.ControlModifier:
                    self.undoStack.redo()
            case Qt.Key_S:
                if event.modifiers() & Qt.ControlModifier:
                    self.timer.stop()
                    self.scene().removeItem(self.cp_item)
                    self.scene().removeItem(self.circle_item)
                    self.dataManager.save_jsons()
                    self.timer.start()
                    self.scene().addItem(self.cp_item)
                    self.scene().addItem(self.circle_item)
            case Qt.Key_O:
                if event.modifiers() & Qt.ControlModifier:
                    self.dataManager.load_background(self.dataManager.pixoffset)
                    self.dataManager.import_data(self.dataManager.pixoffset)
            case _:
                super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        button = event.buttons()
        x = event.x()
        y = event.y()
        dx = -(x - self.old_x)
        dy = -(y - self.old_y)
        if button == Qt.RightButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            if self.current_point_item.isSelected():
                self.undoStack.push(MovePointCommand(self, QPointF(self.cpi_old_pos), QPointF(dx,dy), self.dataItems))
            else:
                vertical_bar = self.verticalScrollBar()
                horizontal_bar = self.horizontalScrollBar()
                vertical_bar.setValue(vertical_bar.value() + dy)
                horizontal_bar.setValue(horizontal_bar.value() + dx)
        elif button == Qt.LeftButton:
            if not self.origin.isNull() and not self.isF5Pressed:
                self.setCursor(Qt.CursorShape.CrossCursor)
                self.rubberBand.setGeometry(QRect(self.origin.toPoint(), event.pos()).normalized())

        self.old_x = x
        self.old_y = y


    def mousePressEvent(self, event):
        self.old_x = event.x()
        self.old_y = event.y()
        if event.button() == Qt.LeftButton:
            self.origin = QPointF(event.pos())
            self.rubberBand.setGeometry(QRect())
            self.rubberBand.show()
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        elif event.button() == Qt.RightButton:
            if self.isConnectCircleVisible:
                pos = self.closest_point 
                self.addPoint(pos) if self.closest_point else None
            elif self.isSaveSelecting:
                pos = self.mapToScene(event.pos()).toPoint()
                self.addPoint(pos)

    def mouseDoubleClickEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if event.button() == Qt.LeftButton:
            if self.isF5Pressed and self.isConnectCircleVisible:
                pos = self.mapToScene(event.pos())
                item = self.scene().itemAt(pos, self.transform())
                if item and self.closest_point:
                    self.cpi_old_pos = self.cpi_pos = self.closest_point
                    self.current_point_item.setPos(self.cpi_pos)
                    self.current_point_colliding = list(filter(lambda item: isinstance(item, ProvenceItem), self.current_point_item.collidingItems()))
                    self.dataItems:list[dict[str, typing.Any]] = []
                    for item in self.current_point_colliding:
                        polygon = item.polygon()
                        indexes = [i for i, p in enumerate(polygon) if ((p == self.cpi_pos) & polygon.contains(self.cpi_pos)) | ((p - self.cpi_pos).manhattanLength() <= self.cpi_radius)]
                        if indexes:
                            self.dataItems.append({
                                'item': item,
                                'indexes': indexes,
                                'original_polygon': QPolygonFS(polygon)
                            })
                    self.current_point_item.setSelected(True)
                self.updateCircle(self.mapToScene(event.pos()))
            else:
                pos = self.mapToScene(event.pos()).toPoint()
                item = self.scene().itemAt(pos, self.transform())
                if not self.isSaveSelecting:
                    self.clearSelection(item)
                else:
                    item.setSelected(not item.isSelected())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rubberBand.hide()
            if (self.origin - event.pos()).manhattanLength() > 10:
                self.selectPolygon(self.mapToScene(self.rubberBand.geometry()), self.isSaveSelecting)
            else:
                super().mouseReleaseEvent(event)
        elif event.button() == Qt.RightButton:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            if not self.isPolygonBodyVisible:
                pos = self.mapToScene(event.pos()).toPoint()
                self.addPoint(pos)

    def wheelEvent(self, event):
        self.scaleView(math.pow(2.0, event.angleDelta().y() / 240.0))
        if self.scaleFactor is None:
            self.scaleFactor = math.pow(2.0, event.angleDelta().y() / 240.0)

    def scaleView(self, scaleFactor):
        self.scaleFactor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()
        if self.scaleFactor < 0.07 or self.scaleFactor > 100:
            return
        self.scale(scaleFactor, scaleFactor)

    def checkCursor(self):
        pos = self.mapToScene(self.cursor().pos()).toPoint() if self.geometry().contains(self.cursor().pos(), True) else None
        if pos != self._cursorPos and pos is not None:
            self._cursorPos = pos + (QPoint(-10, -30) / self.scaleFactor)
            self.cursorMove.emit(pos + (QPoint(-10, -30) / self.scaleFactor))

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
    def current_province(self):
        return self._current_province

    @current_province.setter
    def current_province(self, value: QPolygonF):
        self._current_province = value

    @property
    def cp_item(self):
        return self._cp_item

    @cp_item.setter
    def cp_item(self, value: QGraphicsPolygonItem):
        self._cp_item = value

    @staticmethod
    def generate_circle_polygon(center: QPointF, radius: float, sides: int):
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
        return QPolygonF(points)

    def QRColor(self):
        return QColor(r.randint(20, 255), r.randint(20, 255), r.randint(20, 255), 70)