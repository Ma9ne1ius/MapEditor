from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QUndoCommand, QUndoStack, QUndoGroup
)
from PyQt5.QtGui import QPainter, QColor, QPolygon, QPixmap
import PyQt5.QtCore
from PyQt5.QtCore import QPoint


class AddPointCommand(QUndoCommand):
    def __init__(self, view: QGraphicsView, point: QPoint, province: QPolygon):
        super().__init__()
        self.view = view
        self.point = point

    # def undo(self):
        # self.view.current_province.remove(self.)