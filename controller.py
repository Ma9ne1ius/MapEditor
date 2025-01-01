import numpy as np
import math
from  PyQt5.QtWidgets import QGraphicsPolygonItem, QGraphicsView, QGraphicsPixmapItem, QRubberBand
from PyQt5.QtGui import QPixmap, QTransform, QPolygonF, QPen, QBrush, QColor
from PyQt5.QtCore import Qt, QPoint, QRectF, QRect, QSize
from data_manager import DataManager
import random as r



class InteractiveGraphicsView(QGraphicsView):
    def __init__(self, scene:QGraphicsView, dataManager:DataManager):
        super().__init__(scene)
        self.scene = scene
        self.dataManager = dataManager
        # self.polygon_item = polygon_item
        
        self.rubberBand: QRubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        
        self._current_province = QPolygonF()
        self._cp_item = QGraphicsPolygonItem(self._current_province)
        self._cp_item.setBrush(QBrush(QColor(150,0,150,100)))
        self.scene.addItem(self._cp_item)
        
        # self._current_province.
        self.setRenderHints(self.renderHints())
        self.translation_step = 10
        self.scaleFactor = None
        
        self.isF1Pressed = False
        self.isCtrlPressed = False
        self.isAltPressed = False
        
        self.isBackVisible = True
        self.isPolygonEdgeVisible = True
        self.isPolygonBodyVisible = True
        
    # def remove_nearest_point(self, position):
    #     """Remove the nearest point from the current province."""
    #     if not self._current_province:
    #         return
    #     nearest_point = min(self._current_province, key=lambda p: (p.x() - position.x()) ** 2 + (p.y() - position.y()) ** 2)
    #     self._current_province.remove(nearest_point)
    #     self.update_province_polygon()

    def update_province_polygon(self):
        """Update the polygon for the current province."""
        # points = [QPointF(p.x(), p.y()) for p in self._current_province.toList()]
        polygon = QPolygonF(self._current_province)
        item = QGraphicsPolygonItem(polygon)
        provinces = self.dataManager.provinces
        provinces.append({"points":polygon.toList(), "province":item})
        
    def addPoint(self, position):
        """Add a point to the current province."""
        position = self.mapToScene(position)
        self._current_province.append(position)
        self._cp_item.setPolygon(self._current_province)
        self.repaint()
        
        
    def popPoint(self):
        if not self._current_province.isEmpty():
            index = self._current_province.count()-1
            self._current_province.remove(index)
            self._cp_item.setPolygon(self._current_province)
        self.repaint()
            
            
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
            case Qt.Key_F1:
                self.isF1Pressed = not self.isF1Pressed
            # case Qt.Key_Control:
                # ...
            case Qt.Key_Backspace:
                self.popPoint()
            case Qt.Key_1:
                # array = np.array(self.scene.items())
                # np.vectorize(self.redrawBackground)(array)
                
                list(map(lambda item: item.setVisible(not self.isBackVisible), filter(lambda item: isinstance(item, QGraphicsPixmapItem), self.scene.items())))
                self.repaint()
                self.isBackVisible = not self.isBackVisible
            case Qt.Key_2:
                # self.isPolygonEdgeVisible = self.redrawPolygonEdge(self.isPolygonEdgeVisible)
                list(map(self.redrawPolygonEdge, filter(lambda item: isinstance(item,QGraphicsPolygonItem) and not item is self._cp_item, self.scene.items())))
                self.repaint()
                self.isPolygonEdgeVisible = not self.isPolygonEdgeVisible
            case Qt.Key_3:
                list(map(self.redrawPolygonBody, filter(lambda item: isinstance(item,QGraphicsPolygonItem) and not item is self._cp_item, self.scene.items())))
                self.repaint()
                self.isPolygonBodyVisible = not self.isPolygonBodyVisible                
            case Qt.Key_Equal:
                if self.translation_step<250:
                    self.translation_step+=1
            case Qt.Key_Underscore:
                if self.translation_step>10:
                    self.translation_step-=1
            case _:
                super().keyPressEvent(event)
            
    def mouseMoveEvent(self, event):
        button = event.buttons()
        x = event.x()
        y = event.y()
        dx = -(x - self.old_x)
        dy = -(y - self.old_y)
        if button == Qt.RightButton:
            vertical_bar = self.verticalScrollBar()
            horizontal_bar = self.horizontalScrollBar()
            vertical_bar.setValue(vertical_bar.value() + dy)
            horizontal_bar.setValue(horizontal_bar.value() + dx)
        elif button == Qt.LeftButton and not self.origin.isNull():                    
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
            # print(self.rubberBand.rect().top(),self.rubberBand.rect().bottom(),self.rubberBand.rect().left(),self.rubberBand.rect().right())
        # self.repaint()
        self.old_x = x
        self.old_y = y

    def mousePressEvent(self, event):
        self.old_x = event.x()
        self.old_y = event.y()
        if event.button() == Qt.LeftButton:
            self.origin = QPoint(event.pos())
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()
        super().mousePressEvent(event)
        
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.addPoint(event.pos())
        super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rubberBand.hide()
            for item in self.scene.items():
                if isinstance(item, QGraphicsPolygonItem):
                    point0 = self.mapToScene(self.origin).toPoint()
                    point1 = self.mapToScene(event.pos()).toPoint()
                    mapped = QRect(QRectF(point0.x(), point0.y(), point1.x() - point0.x(), point1.y() - point0.y()).toRect())
                    # mapped = self.rubberBand.rect()
                    # mapped.setX(mapped.x() + point0.x())
                    # mapped.setY(mapped.y() + point0.y())
                    # rubberBand:QRect = self.rubberBand.rect()
                    # # print(rubberBand.top(),rubberBand.bottom(),rubberBand.left(),rubberBand.right())
                    # # mapped = self.mapToScene(rubberBand)
                    # # rubberBand.setCoords(self.origin.x(), \
                    # #                     self.origin.y(), \
                    # #                     self.rubberBand.size().width(), \
                    # #                     self.rubberBand.size().height())
                    # mapped = rubberBand
                    # # flag = mapped.intersects(item.polygon())
                    flag = mapped.intersects(item.polygon().boundingRect().toRect())
                    item.setSelected(flag)
        super().mouseReleaseEvent(event)
        
    def wheelEvent(self, event):
        self.scaleView(math.pow(2.0, event.angleDelta().y() / 240.0))
        if self.scaleFactor is None:
            self.scaleFactor = math.pow(2.0, event.angleDelta().y() / 240.0)

    def scaleView(self, scaleFactor):
        factor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()
        if factor < 0.07 or factor > 100:
            return
        self.scale(scaleFactor, scaleFactor)

    def redrawBackground(self, item):
        # if isinstance(item,QGraphicsPixmapItem):
            item.setVisible(not self.isBackVisible)


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
                    item.setBrush(QBrush(self.QRColor))
    
    @property
    def QRColor(self):
        """The QRColor property."""
        return QColor(r.randint(20,255), r.randint(20,255), r.randint(20,255), 70)
