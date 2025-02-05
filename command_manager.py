from PyQt5.QtWidgets import (
    QUndoCommand, QUndoStack, QUndoGroup, QGraphicsItem, QGraphicsView
)
from PyQt5.QtGui import QPainter, QColor, QPixmap, QPen, QPolygonF
from PyQt5.QtCore import QRectF, QPointF, QPoint, Qt
from data_manager import QPolygonFS, ProvenceItem

import random as r
import typing

from data_manager import ProvenceItem, QPolygonFS

    

class AddPointCommand(QUndoCommand):
    def __init__(self, view: QGraphicsView, point):
        super().__init__("Add Point")
        self.view = view
        self.point = point

    def redo(self):
        self.view.current_province.append(self.point)
        self.view.cp_item.setPolygon(self.view.current_province)
        self.view.repaint()

    def undo(self):
        if not self.view.current_province.isEmpty():
            self.view.current_province.remove(self.view.current_province.indexOf(self.point))
            self.view.cp_item.setPolygon(self.view.current_province)
        self.view.repaint()

class PopPointCommand(QUndoCommand):
    def __init__(self, view: QGraphicsView):
        super().__init__()
        self.view = view
        self.last_point = None

    def redo(self):
        if not self.view.current_province.isEmpty():
            self.last_point = self.view.current_province.last()
            self.view.current_province.remove(self.view.current_province.indexOf(self.last_point))
            self.view.cp_item.setPolygon(self.view.current_province)
        self.view.repaint()

    def undo(self):
        if self.last_point:
            self.view.current_province.append(self.last_point)
            self.view.cp_item.setPolygon(self.view.current_province)
        self.view.repaint()

class AddCurrentPolygonCommand(QUndoCommand):
    def __init__(self, view: QGraphicsView):
        super().__init__()
        self.view = view
        self.polygon_item : ProvenceItem = None
        self.cp = self.view.current_province

    def redo(self):
        self.polygon_item = ProvenceItem(self.view.current_province)
        self.polygon_item.setPen(Qt.red)
        self.polygon_item.setBrush(self.view.QRColor())
        self.polygon_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.view.scene().addItem(self.polygon_item)
        self.view.cp_item.setPolygon(QPolygonF())
        self.view.repaint()

    def undo(self):
        if self.polygon_item:
            self.view.scene().removeItem(self.polygon_item)
            self.view.current_province = QPolygonFS(self.cp)
            self.view.cp_item.setPolygon(self.view.current_province)
        self.view.repaint()

class AddPolygonCommand(QUndoCommand):
    def __init__(self, view: QGraphicsView, polygon_item: ProvenceItem):
        super().__init__("Add Polygon")
        self.view = view
        self.polygon_item = None if not polygon_item else polygon_item

    def redo(self):
        self.polygon_item.setPen(Qt.red)
        self.polygon_item.setBrush(self.view.QRColor())
        self.polygon_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.view.scene().addItem(self.polygon_item)
        self.view.repaint()

    def undo(self):
        if self.polygon_item:
            self.view.scene().removeItem(self.polygon_item)
            self.polygon_item = None
        self.view.repaint()


class DeletePolygonCommand(QUndoCommand):
    def __init__(self, view: QGraphicsView, polygon_item):
        super().__init__("Delete Polygon")
        self.view = view
        self.polygon_item = polygon_item

    def redo(self):
        self.view.scene().removeItem(self.polygon_item)
        self.view.repaint()

    def undo(self):
        self.view.scene().addItem(self.polygon_item)
        self.view.repaint()



class MovePointCommand(QUndoCommand):
    def __init__(self, view: QGraphicsView, old_point: QPointF | QPoint, new_point: QPointF | QPoint, dataItems: list[dict[str, typing.Any]]):
        super().__init__()
        self.view = view
        self.old_point = QPointF(old_point)
        self.new_point = self.view.current_point_item.pos() - (QPointF(new_point) / self.view.scaleFactor)
        self.dataItems = dataItems
        

    def redo(self):
        """Применяем новую позицию точки"""
        # print('moving')
        self.moveCurrentPoint(self.new_point)
        # print('')

    def undo(self):
        """Восстанавливаем оригинальную позицию точки"""
        for data in self.dataItems:
            item = data['item']
            
            # Восстанавливаем из оригинального полигона
            item.setPolygon(QPolygonF(data['original_polygon']))
            self.view.cpi_pos = self.old_point
            self.view.current_point_item.setPos(self.old_point)

            item.update()

    def moveCurrentPoint(self, toPoint: QPoint|QPointF):
        for data in self.dataItems:
            polygon = QPolygonFS(data['original_polygon'])
            for point in polygon:
                    for i in data['indexes']:
                        polygon.replace(i, self.new_point)
                    data['item'].setPolygon(polygon)
        self.view.cpi_pos = self.new_point
        self.view.current_point_item.setPos(self.new_point)
