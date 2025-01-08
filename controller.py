import numpy as np
import math
import collections
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from data_manager import DataManager
import random as r
from command_manager import AddPointCommand, PopPointCommand, AddCurrentPolygonCommand, AddPolygonCommand, DeletePolygonCommand

from PyQt5.QtWidgets import QGraphicsPolygonItem, QGraphicsView, QGraphicsPixmapItem, QRubberBand, QUndoStack, QGraphicsItem, QGraphicsScene, QGraphicsLineItem
from PyQt5.QtGui import QPolygonF, QPen, QBrush, QColor, QPolygon
from PyQt5.QtCore import Qt, QPoint, QPointF, QRectF, QRect, QSize, pyqtSignal, QTimer


class InteractiveGraphicsView(QGraphicsView):
    cursorMove = pyqtSignal(QPoint)

    def __init__(self, scene: QGraphicsScene, dataManager: DataManager, offset: int, size: int):
        super().__init__(scene)
        self.dataManager = dataManager
        self.sceneOffset = offset
        self.sceneSize = size
        self.undoStack = QUndoStack(self)
        # self.polygon_item = polygon_item
        
        self.rubberBand: QRubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        
        self._current_province = QPolygonF()
        self._cp_item = QGraphicsPolygonItem(self._current_province)
        self._cp_item.setBrush(QBrush(QColor(150,0,150,100)))
        self._cp_item.setPen(QPen(QColor(150,0,150, 50)))
        self.scene().addItem(self._cp_item)
        
        # self._current_province.
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
        self.circle_item.setPen(QPen(QColor(0, 255, 0, 150), self.circle_width, Qt.DashLine))
        self.circle_item.setBrush(QBrush(QColor(0,0,0,0)))
        self.circle_item.setVisible(False)
        self.scene().addItem(self.circle_item)  # Добавляем круг на сцену
        
        self.closest_point_line = QGraphicsLineItem()
        self.closest_point_line.setPen(QPen(QColor(0, 0, 100, 150), self.circle_width))
        self.closest_point_line.setVisible(False)
        self.scene().addItem(self.closest_point_line)
        
        self.cursorMove.connect(self.updateCircle)
        self.timer = QTimer(self)
        self.timer.setInterval(15)
        self.timer.timeout.connect(self.checkCursor)
        self.timer.start()
        self._cursorPos = self.cursor().pos()

    def checkCursor(self):
        pos = self.mapToScene(self.cursor().pos()).toPoint() if self.geometry().contains(self.cursor().pos(), True) else None
        if pos != self._cursorPos and pos is not None:
            self._cursorPos = pos
            self.cursorMove.emit(pos)

    def add_province_polygon(self, polygon: QPolygonF):
        """Update the polygon for the current province."""
        self.undoStack.push(AddCurrentPolygonCommand(self))
        # polygon.clear()
        # self._cp_item.setPolygon(polygon)
        # item = QGraphicsPolygonItem(polygon)
        # item.setFlag(QGraphicsItem.ItemIsSelectable,True)
        # item.setPen(QPen(Qt.red))
        # item.setBrush(self.QRColor())
        # self.dataManager.scene.addItem(item)

    def deleteProvince(self, province:QGraphicsPolygonItem):
        self.undoStack.push(DeletePolygonCommand(self, province))
        # self.scene().removeItem(province)

    def addPoint(self, position):
        """Add a point to the current province."""
        self.undoStack.push(AddPointCommand(self, position))
        
    def popPoint(self):
        self.undoStack.push(PopPointCommand(self,))
        # QGraphicsItem().setFlag(Qt.)
    
    def selectingRect(self, rect: QRect, saveSelection: bool): 
        condition = lambda item: QPolygon(rect, False).intersects(item.polygon().toPolygon()) or (item.isSelected() and saveSelection)
        list(map(lambda item: item.setSelected(condition(item)),
                filter(lambda item: isinstance(item, QGraphicsPolygonItem) and condition, self.scene().items())))

    def selectPolygon(self, polygon: QPolygonF, saveSelection: bool):
        condition = lambda item: polygon.intersects(item.polygon()) or (item.isSelected() and saveSelection)
        list(map(lambda item: item.setSelected(condition(item)), 
                filter(lambda item: isinstance(item, QGraphicsPolygonItem) and condition, self.scene().items())))
    
    def clearSelection(self):
        self.dataManager.scene.clearSelection()

    def updateCircle(self, position):
        if not self.isConnectCircleVisible: return
        scene_pos = position + (QPoint(-10,-30) / self.scaleFactor)

        radius = self.circle_radius / self.scaleFactor if self.scaleFactor else self.circle_radius
        width = self.circle_width / self.scaleFactor if self.scaleFactor else self.circle_width
        pen = self.circle_item.pen()
        # print(pen)
        pen.setWidthF(width)
        pen1 = self.closest_point_line.pen()
        # print(pen1)
        pen1.setWidthF(width)
        
        circle_polygon = self.generate_circle_polygon(scene_pos, radius, 24)
        
        self.circle_item.setPolygon(circle_polygon)
        self.circle_item.setPen(pen)

        self.closest_point = None
        min_distance = radius
        
        for item in filter(lambda item: isinstance(item,QGraphicsPolygonItem) and not (item is self.circle_item or item is self._cp_item), self.scene().items(circle_polygon)):
            polygon = item.polygon()
            for point in filter(lambda point: circle_polygon.containsPoint(point, 1) ,polygon):
                distance = math.hypot(scene_pos.x() - point.x(), scene_pos.y() - point.y())
                if distance < min_distance:
                    self.closest_point:QPoint = point.toPoint()
                    min_distance = distance
        
        if self.closest_point:
            self.closest_point_line.setLine(scene_pos.x(), scene_pos.y(), self.closest_point.x(), self.closest_point.y())
            self.closest_point_line.setVisible(True)
            # self.closest_point = self.closest_point
        else:
            self.closest_point_line.setVisible(False) if self.closest_point_line.isVisible() else None

    def unitingProvinces(self):
        selectedItems = self.scene().selectedItems()

        if len(selectedItems) < 2:
            return  # Нечего объединять, если выбрано меньше двух элементов

        # Преобразуем QPolygonF в Shapely Polygon
        def to_shapely_polygon(qpolygonf:QPolygonF):
            points = [(point.x(), point.y()) for point in qpolygonf]
            return Polygon(points)

        # Преобразуем Shapely Polygon обратно в QPolygonF
        def from_shapely_polygon(polygon:Polygon):
            if polygon.is_empty:
                return QPolygonF()
            return QPolygonF([QPointF(x, y) for x, y in polygon.exterior.coords])

        # Используем map для преобразования всех выбранных элементов в Shapely Polygon
        shapely_polygons = map(lambda item: to_shapely_polygon(item.polygon()), selectedItems)

        # Объединяем все полигоны с использованием unary_union для повышения производительности
        unified_polygon = unary_union(list(shapely_polygons))
        # Если результат - несколько полигонов, берем только основные части
        if isinstance(unified_polygon, MultiPolygon):
            unified_polygon = max(unified_polygon, key=lambda p: p.area)  # Выбираем самый большой

        # Создаем новый QGraphicsPolygonItem
        new_polygon_qt = from_shapely_polygon(unified_polygon)
        new_poly_item = QGraphicsPolygonItem(new_polygon_qt)
        
        list(map(lambda item: self.deleteProvince(item), selectedItems))
        self.undoStack.push(AddPolygonCommand(self, new_poly_item))

    def keyPressEvent(self, event):
        """Handle keyboard events for translation and zoom."""
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
                    self.translation_step+=1
            case Qt.Key_Minus:
                if self.translation_step > 10:
                    self.translation_step-=1
            case Qt.Key_Plus:
                if self.circle_radius<150:
                    self.circle_radius+=1
                    self.updateCircle(self._cursorPos)
            case Qt.Key_Underscore:
                if self.circle_radius>0:
                    self.circle_radius-=1
                    self.updateCircle(self._cursorPos)
            case Qt.Key_F1:
                self.isSaveSelecting = not self.isSaveSelecting
            case Qt.Key_F2:
                # self.isF2Pressed = not self.isF2Pressed
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
                self.checkCursor()
            case Qt.Key_F5:
                self.isF5Pressed = not self.isF5Pressed
            case Qt.Key_F6:
                self.unitingProvinces()
            case Qt.Key_1:
                list(map(lambda item: item.setVisible(not self.isBackVisible), filter(lambda item: isinstance(item, QGraphicsPixmapItem), self.scene().items())))
                self.repaint()
                self.isBackVisible = not self.isBackVisible
            case Qt.Key_2:
                list(map(self.redrawPolygonEdge, filter(lambda item: isinstance(item,QGraphicsPolygonItem) and not (item is self._cp_item or item is self.circle_item), self.scene().items())))
                self.repaint()
                self.isPolygonEdgeVisible = not self.isPolygonEdgeVisible
            case Qt.Key_3:
                list(map(self.redrawPolygonBody, filter(lambda item: isinstance(item,QGraphicsPolygonItem) and not (item is self._cp_item or item is self.circle_item), self.scene().items())))
                self.repaint()
                self.isPolygonBodyVisible = not self.isPolygonBodyVisible
            case Qt.Key_Delete:
                list(map(lambda item:self.deleteProvince(item), self.scene().selectedItems()))
                self.repaint()
            case Qt.Key_Backspace:
                self.popPoint()
            case Qt.Key_Space:
                self.add_province_polygon(self.current_province)
            case Qt.Key_Z:
                if event.modifiers() & Qt.ControlModifier:
                    # print("undo")
                    self.undoStack.undo()
            case Qt.Key_Y:
                if event.modifiers() & Qt.ControlModifier:
                    # print("redo")
                    self.undoStack.redo()
            case Qt.Key_End:
                self.timer.timeout.disconnect()
                self.scene().removeItem(self.cp_item)
                self.scene().removeItem(self.circle_item)
                # if event.modifiers() & Qt.ControlModifier:
                self.dataManager.save_jsons()
                self.timer.timeout.connect(self.checkCursor)
                self.scene().addItem(self.cp_item)
                self.scene().addItem(self.circle_item)
            case Qt.Key_Home:
                self.dataManager.load_background(self.dataManager.pixoffset)
                self.dataManager.import_data(self.dataManager.pixoffset)
            case _:
                super().keyPressEvent(event)
            
    def mouseMoveEvent(self, event):
        button = event.buttons()
        x = event.x()
        y = event.y()
        # print(x, y)
        dx = -(x - self.old_x)
        dy = -(y - self.old_y)
        if button == Qt.RightButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            vertical_bar = self.verticalScrollBar()
            horizontal_bar = self.horizontalScrollBar()
            vertical_bar.setValue(vertical_bar.value() + dy)
            horizontal_bar.setValue(horizontal_bar.value() + dx)
            # self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif button == Qt.LeftButton and not self.origin.isNull():
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
        elif self.isConnectCircleVisible:
            self.updateCircle(event.pos())
        
        self.old_x = x
        self.old_y = y

    def mousePressEvent(self, event):
        self.old_x = event.x()
        self.old_y = event.y()
        if event.button() == Qt.LeftButton:
            self.origin = QPoint(event.pos())
            self.rubberBand.setGeometry(QRect())
            self.rubberBand.show()
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        # super().mousePressEvent(event)
        
    def mouseDoubleClickEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if event.button() == Qt.LeftButton:
            if self.isConnectCircleVisible:
                pos = self.closest_point
                self.addPoint(pos) 
            elif self.isF5Pressed:
                pos = self.mapToScene(event.pos()).toPoint()
                self.addPoint(pos) 
            pos: QPoint = event.pos()
            if not self.isSaveSelecting:
                self.clearSelection()
            # item = self.itemAt(self.mapToScene(pos).toPoint())
            item = self.itemAt(pos)
            if not item is None:
                item.setSelected(not item.isSelected())

        # super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rubberBand.hide()
            point0 = self.mapToScene(self.origin).toPoint()
            point1 = self.mapToScene(event.pos()).toPoint()
            if (self.origin - event.pos()).manhattanLength() > 10:
                self.selectingRect(QRect(point0, point1), self.isSaveSelecting)
            else:
                super().mouseReleaseEvent(event)
        elif event.button() == Qt.RightButton:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            
    def wheelEvent(self, event):
        self.scaleView(math.pow(2.0, event.angleDelta().y() / 240.0))
        if self.scaleFactor is None:
            self.scaleFactor = math.pow(2.0, event.angleDelta().y() / 240.0)

    def scaleView(self, scaleFactor):
        self.scaleFactor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()
        if self.scaleFactor < 0.07 or self.scaleFactor > 100:
            return
        self.scale(scaleFactor, scaleFactor)

    # def resizeEvent(self, QResizeEvent):
        # self.setSceneRect(QRectF(self.sceneport().rect()))

    def redrawPolygonEdge(self, item):
                if self.isPolygonEdgeVisible:
                    item.setPen(QPen(QColor(0,0,0,0)))
                else:
                    item.setPen(QPen(Qt.red))

    def redrawPolygonBody(self, item):
            # if isinstance(item, QGraphicsPolygonItem) and not item is self._cp_item:
                if self.isPolygonBodyVisible:
                    item.setBrush(QBrush(QColor(0,0,0,0)))
                else:
                    item.setBrush(QBrush(self.QRColor()))
    
    @property
    def current_province(self):
        """The current_province property."""
        return self._current_province
    @current_province.setter
    def current_province(self, value:QPolygonF):
        self._current_province = value
    
    @property
    def cp_item(self):
        """The cp_item property."""
        return self._cp_item
    @cp_item.setter
    def cp_item(self, value:QGraphicsPolygonItem):
        self._cp_item = value

    @staticmethod
    def generate_circle_polygon(center: QPointF, radius: float, sides: int):
        """
        Generates a regular n-sided polygon.

        :param center: Center point of the polygon.
        :param radius: Radius of the polygon's circumscribed circle.
        :param sides: Number of sides of the polygon (n >= 3).
        :return: QPolygonF representing the polygon.
        """
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
        """The QRColor property."""
        return QColor(r.randint(20,255), r.randint(20,255), r.randint(20,255), 70)

