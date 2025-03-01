from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsView
)
from PySide6.QtGui import QPainter, QColor, QPixmap, QPen, QPolygonF, QUndoCommand
from PySide6.QtCore import QRectF, QPointF, QPoint, Qt
from data_manager import MEPolygonF, MEPolygonItem, ProvenceItem

import random as r
import shapely.geometry
import typing

from data_manager import ProvenceItem, MEPolygonF

    

class AddPointCommand(QUndoCommand):
    def __init__(self, view:QGraphicsView, point):
        super().__init__()
        self.view = view
        self.point = point

    def redo(self):
        self.view.current_province_polygon.append(self.point)
        self.view.current_province.setPolygon(self.view.current_province_polygon)
        self.view.repaint()

    def undo(self):
        if not self.view.current_province_polygon.isEmpty():
            self.view.current_province_polygon.remove(self.view.current_province_polygon.indexOf(self.point))
            self.view.current_province.setPolygon(self.view.current_province_polygon)
        self.view.repaint()

class PopPointCommand(QUndoCommand):
    def __init__(self, view:QGraphicsView):
        super().__init__()
        self.view = view
        self.last_point = None

    def redo(self):
        if not self.view.current_province_polygon.isEmpty():
            self.last_point = self.view.current_province_polygon.last()
            self.view.current_province_polygon.remove(self.view.current_province_polygon.indexOf(self.last_point))
            self.view.current_province.setPolygon(self.view.current_province_polygon)
        self.view.repaint()

    def undo(self):
        if self.last_point:
            self.view.current_province_polygon.append(self.last_point)
            self.view.current_province.setPolygon(self.view.current_province_polygon)
        self.view.repaint()

class AddCurrentPolygonCommand(QUndoCommand):
    def __init__(self, view:QGraphicsView):
        super().__init__()
        self.view = view
        self.provence_item:ProvenceItem = None
        self.current_province_polygon = self.view.current_province_polygon

    def redo(self):
        self.provence_item = ProvenceItem(self.view.current_province_polygon)
        self.provence_item.setPen(QColor(255, 0, 0))
        self.provence_item.setBrush(self.view.QRColor())
        self.provence_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.view.scene().addItem(self.provence_item)
        self.view.current_province.setPolygon(MEPolygonF())
        self.view.repaint()

    def undo(self):
        if self.provence_item:
            self.view.scene().removeItem(self.provence_item)
            self.view.current_province_polygon = MEPolygonF(self.current_province_polygon)
            self.view.current_province.setPolygon(self.view.current_province_polygon)
        self.view.repaint()

class UnitePolygonsCommand(QUndoCommand):
    def __init__(self, view:QGraphicsView, new_provence:ProvenceItem, old_provinces:typing.Sequence[ProvenceItem]):
        super().__init__("Unite Polygons")
        self.view = view
        self.new_provence = new_provence
        self.old_provinces = old_provinces
    
    def redo(self):
        for item in self.old_provinces:
            self.view.scene().removeItem(item)
        self.view.repaint()
        self.view.scene().addItem(self.new_provence)
    
    def undo(self):
        self.view.scene().removeItem(self.new_provence)
        list(map(lambda item: self.view.scene().addItem(item), self.old_provinces))
            

class AddPolygonCommand(QUndoCommand):
    def __init__(self, view:QGraphicsView, provence_item:ProvenceItem):
        super().__init__("Add Polygon")
        self.view = view
        self.provence_item = None if not provence_item else provence_item

    def redo(self):
        self.provence_item.setZValue(self.view.provence_level)
        self.view.scene().addItem(self.provence_item)
        self.view.repaint()

    def undo(self):
        if self.provence_item:
            self.view.scene().removeItem(self.provence_item)
            self.provence_item = None
        self.view.repaint()


class DeletePolygonCommand(QUndoCommand):
    def __init__(self, view:QGraphicsView, provence_items:typing.Sequence[ProvenceItem]):
        super().__init__("Delete Polygon")
        self.view = view
        self.provence_items = provence_items

    def redo(self):
        for item in self.provence_items:
            self.view.scene().removeItem(item)
        self.view.repaint()

    def undo(self):
        for item in self.provence_items:
            self.view.scene().addItem(item)
        self.view.repaint()



class MovePointCommand(QUndoCommand):
    def __init__(self, view:QGraphicsView, old_point:QPointF | QPoint, new_point:QPointF | QPoint, dataItems:list[dict[str, typing.Any]]):
        super().__init__()
        self.view = view
        self.old_point = QPointF(old_point)
        self.new_point = new_point
        self.dataItems = dataItems
        

    def redo(self):
        """Применяем новую позицию точки"""
        # print('moving')
        self.moveCurrentPoint(self.new_point)
        # print('')

    def undo(self):
        """Восстанавливаем оригинальную позицию точки"""
        for data in self.dataItems:
            item:MEPolygonItem = data['item']
            item.setPolygon(MEPolygonF(data['original_polygon']))
            # item.Polygon = MEPolygonF(data['original_polygon'])
            self.view.current_point_item_pos = self.old_point
            self.view.current_point_item.setPos(self.old_point)

            item.update()

    def moveCurrentPoint(self, toPoint:QPoint|QPointF):
        for data in self.dataItems:
            polygon = MEPolygonF(data['original_polygon'])
            # for point in polygon:
            for i in data['indexes']:
                polygon.replace(i, toPoint)
            data['item'].setPolygon(polygon)
        self.view.current_point_item_pos = (toPoint)
        self.view.current_point_item.setPos((toPoint))
        # self.view.update_circle(toPoint)



class DeletePolygonPointCommand(QUndoCommand):
    def __init__(self, view:QGraphicsView, point:QPointF, dataItems:list[dict[str, MEPolygonF|int|ProvenceItem]]):
        super().__init__()
        self.view = view
        self.point = point
        self.dataItems = dataItems

    def redo(self):
        for data in self.dataItems:
            polygon = MEPolygonF(data['original_polygon'])
            for i in data['indexes']:
                polygon.remove(i)
            polygon = MEPolygonF(polygon)
            data['item'].setPolygon(polygon)
        self.view.current_point_item_pos = None
        self.view.current_point_item.setPos(QPointF())
        self.view.current_point_item.setVisible(False)
        self.view.repaint()
        
    def undo(self):
        for data in self.dataItems:
            item = data['item']
            polygon = MEPolygonF(data['original_polygon'])
            for i in data['indexes']:
                polygon.insert(i, self.point)
            item.setPolygon(polygon)
            item.update()
        self.view.current_point_item_pos = self.point
        self.view.current_point_item.setPos(QPointF(self.point))
        self.view.current_point_item.setVisible(True)
        self.view.current_point_item.setSelected(True)
        self.view.repaint()



class AddPointBeforeCommand(QUndoCommand):
    """docstring for AddPointBeforeCommand."""
    def __init__(self, view:QGraphicsView, point:QPointF, dataItems:list[dict[str, MEPolygonF|int|ProvenceItem]]):
        super().__init__()
        self.view = view
        self.point = point
        self.dataItems = dataItems
    
    def redo(self):
        for data in self.dataItems:
            new_point = self.point 
            polygon = MEPolygonF(data['original_polygon'])
            indexes:list[int]  = data['indexes']
            indexes1 = []
            for i in indexes:
                polygon.insert(i, new_point)
                indexes1.append(i)
            indexes.clear()
            indexes.extend(indexes1)
            data['item'].setPolygon(polygon)
            data['item'].update()
    
    def undo(self):
        for data in self.dataItems:
            item = data['item']
            polygon = MEPolygonF(data['original_polygon'])
            item.setPolygon(polygon)
            item.update()


    
class AddPointAfterCommand(QUndoCommand):
    """docstring for AddPointAfterCommand."""
    def __init__(self, view:QGraphicsView, point:QPointF, dataItems:list[dict[str, MEPolygonF|int|ProvenceItem]]):
        super().__init__()
        self.view = view
        self.point = point
        self.dataItems = dataItems
    
    def redo(self):
        for data in self.dataItems:
            new_point = self.point 
            polygon = MEPolygonF(data['original_polygon'])
            indexes:list[int] = data['indexes']
            indexes1 = []
            for i in indexes:
                polygon.insert(i+1, new_point)
                indexes1.append(i+1)
            indexes.clear()
            indexes.extend(indexes1)
            data['item'].setPolygon(polygon)
            data['item'].update()
    
    def undo(self):
        for data in self.dataItems:
            item = data['item']
            polygon = MEPolygonF(data['original_polygon'])
            item.setPolygon(polygon)
            item.update()