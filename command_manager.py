from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsPolygonItem, QUndoCommand, QUndoStack, QUndoGroup, QGraphicsItem
)
from PyQt5.QtGui import QPainter, QColor, QPolygonF, QPixmap, QPen
from PyQt5.QtCore import Qt

import random as r

    
@property
def QRColor():
    """The QRColor property."""
    return QColor(r.randint(20,255), r.randint(20,255), r.randint(20,255), 70)

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
        super().__init__("Remove Last Point")
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
        super().__init__("Add Polygon")
        self.view = view
        self.polygon_item = None
        self.cp = self.view.current_province

    def redo(self):
        self.polygon_item = QGraphicsPolygonItem(self.view.current_province)
        self.polygon_item.setPen(Qt.red)
        self.polygon_item.setBrush(self.view.QRColor())
        self.polygon_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.view.scene().addItem(self.polygon_item)
        self.view.cp_item.setPolygon(QPolygonF())
        self.view.repaint()

    def undo(self):
        if self.polygon_item:
            self.view.scene().removeItem(self.polygon_item)
            self.view.current_province = QPolygonF(self.cp)
            self.view.cp_item.setPolygon(self.view.current_province)
        self.view.repaint()

class AddPolygonCommand(QUndoCommand):
    def __init__(self, view: QGraphicsView, polygon_item: QGraphicsPolygonItem):
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

    
