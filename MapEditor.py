
from concurrent.futures import ThreadPoolExecutor
import sys
import json
from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QMainWindow, QVBoxLayout, QWidget, QCheckBox, QGraphicsPolygonItem
from PyQt5.QtGui import QPixmap, QTransform, QPen, QPolygonF, QImage
from PyQt5.QtCore import Qt, QPointF 
import PyQt5.QtCore

from controller import InteractiveGraphicsView
from data_manager import DataManager
# from map_view import MapService

# def tpe (max_workers: int | None = 1):
#     if max_workers == 0:
#         max_workers = 1
#     elif max_workers < 0:
#         max_workers = abs(max_workers)
#     def in_thread(func):
#         def args(*args, **kwargs):
#             with ThreadPoolExecutor(max_workers,f"{max_workers}; {func}; {args};") as exe:
#                 exe.submit(func, args, kwargs)
#         return args
#     return in_thread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Map Editor")
        self.setGeometry(0,0,1920,1020)
        self.size = 2**14.5
        self.offset = -10
        self.scene = QGraphicsScene(self.offset, self.offset, self.size, self.size, self)
        
        self.data_manager = DataManager(self.scene)
                
        self.view = InteractiveGraphicsView(self.scene, self.data_manager, abs(self.offset), self.size)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    print(type(window.init_ui))
    window.showMaximized()
    sys.exit(app.exec_())
