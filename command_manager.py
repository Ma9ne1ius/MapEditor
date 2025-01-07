from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QUndoCommand, QUndoStack, QUndoGroup
)
from PyQt5.QtGui import QPainter, QColor, QPolygon, QPixmap
import PyQt5.QtCore
from PyQt5.QtCore import QPoint

    
class AddPointCommand(QUndoCommand):
    def __init__(self, view: QGraphicsView, point: QPoint):
        super().__init__()
        self.view = view
        self.point = point

    def redo(self):
        self.view._current_province.append(self.point)
        self.view._cp_item.setPolygon(self.view._current_province)

    def undo(self):
        if not self.view.current_province.isEmpty():
            index = self.view.current_province.count()-1
            self.view.current_province.remove(index)
            self.view._cp_item.setPolygon(self.view.current_province)
        self.view._cp_item.setPolygon(self.view.current_province)
        

class PopPointCommand(QUndoCommand):
    def __init__(self, view,point):
        super().__init__()
        self.view = view
        self.point = point

    def redo(self):
        if not self.view.current_province.isEmpty():
            index = self.view.current_province.count()-1
            self.view.current_province.remove(index)
            self.view._cp_item.setPolygon(self.view.current_province)
        self.view._cp_item.setPolygon(self.view.current_province)
    
    def undo(self):
        self.view._current_province.append(self.point)
        self.view._cp_item.setPolygon(self.view._current_province)
        

class AddProvienceCommand(QUndoCommand):
    """docstring for AddProvienceCommand."""
    def __init__(self, view):
        super().__init__()
        self.view = view
    def undo(self):
        return super().undo()

    
