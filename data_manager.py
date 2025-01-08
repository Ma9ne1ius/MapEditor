import asyncio
from concurrent.futures import ThreadPoolExecutor
import os, re, orjson
import numpy as np
import typing
import random as r
from pathlib import Path
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsItem, QGraphicsPixmapItem, QGraphicsPolygonItem, QFileDialog, QMessageBox, QGraphicsEllipseItem, QGraphicsView
from PyQt5.QtGui import QColor, QPixmap, QPen, QBrush, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QPoint, pyqtSignal, QObject
# from undo_mabager 



class DataManager:
    """Класс для работы с файлами."""
    def __init__(self, scene:QGraphicsScene):
        self.provinces = []
        self.background_tiles = []
        self.scene = scene
        self.pixoffset = 1
        
        tiles = DataManager.load_background(self.pixoffset)
        for tile in tiles:
            scene.addItem(tile)

        data = DataManager.import_data(self.pixoffset)
        provinces =data [0] if data else []
        for province in provinces:
            # prov:QGraphicsPolygonItem = province
            # prov = prov.topLevelItem()
            scene.addItem(province)
            
    @staticmethod
    def preprocess_json(content):
        """Обработка JSON для устранения ошибок в формате."""
        content = re.sub(r'(\b\w+\b)\s*:', r'"\1":', content)
        content = re.sub(r':\s*(\b\w+\b)', r': "\1"', content)
        content = content.replace("},\n]","}\n]")
        return content
    
    # @tpe(15) 
    @staticmethod
    def load_data_from_folder(folder_path: str, pixoffset: int):
        """Загрузка данных из всех JSON-файлов в папке."""
        if not folder_path:
            raise ValueError("Путь к папке не указан.")

        json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]

        if not json_files:
            raise FileNotFoundError("В указанной папке нет JSON-файлов.")

        errors = []
        # provinces = np.array([])
        provinces = []
        points = []
        pointsSet = set()

        for file in json_files:
            file_path = os.path.join(folder_path, file)
            try:
                raw_content = DataManager.read_file(file_path)
                processed_content = DataManager.preprocess_json(raw_content)
                file_data = orjson.loads(processed_content)

                cells = file_data.get("Data", [])
                for cell in cells:
                    poly_item: QGraphicsPolygonItem = DataManager.create_polygon_item(cell, pixoffset)
                    # provinces = np.append(provinces, poly_item)
                    provinces.append(poly_item)
            except Exception as e:
                errors.append(f"{file}: {e}")
        print(errors)
        return provinces, points, pointsSet
        
    @staticmethod
    def create_point_item(position:QPointF):
        item: QGraphicsEllipseItem = QGraphicsEllipseItem(position.x() - 0.5, position.y() - 0.5, 1, 1)
        item.setPen(QPen(Qt.red))
        item.setBrush(QBrush(Qt.red))
        item.setVisible(False)
        return item
    
    @staticmethod
    def create_point_items_from(points: set):
        items = set()
        for point in points:
            items.add(DataManager.create_point_item(point))
            # item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        return items
                
    @staticmethod
    def create_polygon_item(province: dict, pixoffset: int):
        points = DataManager.read_points(province, pixoffset)
        polygon = QPolygonF(points)
        item:QGraphicsPolygonItem = QGraphicsPolygonItem(polygon)
        item.setPen(QPen(Qt.red))
        item.setFlag(QGraphicsItem.ItemIsSelectable,True)
        item.setBrush(QBrush(QColor(r.randint(100,255), r.randint(100,255), r.randint(100,255), 75)))
        return item
        # return {"points":points, "province":item}
    
    @staticmethod
    def read_points(province:dict, pixoffset: int):
        return [QPointF(x + pixoffset, y + pixoffset) for x, y in zip(province["pX"], province["pY"])]

    def read_file(file_path):
        """Чтение содержимого файла."""
        with open(file_path, "r", encoding="utf-8") as f:
            # print(f.read())
            res: str = f.read()
            return res
    
    @staticmethod
    def import_data(pixoffset:int):
        """Обработчик загрузки данных с использованием DataLoader."""
        folder_path = QFileDialog.getExistingDirectory(None, "Выберите папку с JSON-файлами провинций")
        if not folder_path:
            QMessageBox.warning(None, "Внимание", "Папка не выбрана!")
            return []
        try:
            res = DataManager.load_data_from_folder(folder_path, pixoffset)
            return res
            
        except ValueError as e:
            QMessageBox.warning(None, "Ошибка", str(e))
        except FileNotFoundError as e:
            QMessageBox.warning(None, "Ошибка", str(e))
        except Exception as e:
            QMessageBox.critical(None, "Критическая ошибка", f"Не удалось загрузить данные: {e}")
        return[]

    # @tpe(15) 
    @staticmethod
    def load_background(pixoffset: int):
        """Обработчик загрузки фона."""
        
        folder_path = QFileDialog.getExistingDirectory(None, "Выберите папку с PNG-файлами фона")
        if not folder_path:
            QMessageBox.warning(None, "Внимание", "Папка не выбрана!")
            return []

        """Загружает PNG-файлы из папки в словарь с координатами."""
        pngs = [f for f in os.listdir(folder_path) if f.endswith(".png")]

        # background_tiles = np.array([])
        background_tiles = []
        fullWidth = fullHeight = 0
        for file in pngs:
            try:
                parts = file.split(".")[0].split("_")
                if len(parts) == 2:
                    y, x = float(parts[0]), float(parts[1])
                    pixmap = QPixmap(os.path.join(folder_path, file))
                    wX, wY = float(pixmap.width()) * x + pixoffset, float(pixmap.height()) * y + pixoffset
                    tile: QGraphicsPixmapItem = QGraphicsPixmapItem(pixmap)
                    tile.setOffset(wX, wY)
                    # background_tiles = np.append(background_tiles, tile)
                    background_tiles.append(tile)

            except ValueError as e:
                QMessageBox.warning(None, "Ошибка", str(e))
            except FileNotFoundError as e:
                QMessageBox.warning(None, "Ошибка", str(e))
            except Exception as e:
                QMessageBox.critical(None, "Критическая ошибка", f"Не удалось загрузить фон: {e}")
        
        return background_tiles

    def save_jsons(self):
        """Обработчик сохранения JSON-файлов."""
        folder_path = QFileDialog.getExistingDirectory(None, "Выберите папку для JSON-файлалов")
        
        if not folder_path:
            QMessageBox.warning(None, "Внимание", "Папка не выбрана!")
            return
        try:
            self.exportProviense(folder_path, self.pixoffset)
        except Exception as e:
            # QMessageBox.critical(None, "Критическая ошибка", f"Не удалось загрузить данные: {e}")
            raise e
    
    def exportProviense(self, floder_path: str, pixoffset: int):
        provinces = [
                    {
                        "pX": [point.x() - pixoffset for point in item.polygon()],
                        "pY": [point.y() - pixoffset for point in item.polygon()]
                    }
                    for item in filter(lambda item: isinstance(item, QGraphicsPolygonItem), self.scene.items())
                    ]
        if not provinces:
            return
        
        batch_size = 500
        for idx, i in enumerate(range(0, len(provinces), batch_size)):
            batch = provinces[i:i + batch_size]
            file_name = f"ProvincePoints_{idx}.json" if idx > 0 else "ProvincePoints.json"
            file_path = os.path.join(floder_path, file_name)
            self.save_json(batch, file_path)
        QMessageBox.information(None, 'Успех!', 'Файлы успешно экспортированы.')

    @staticmethod
    def save_json(data, file_path):
        """Сохранение данных в JSON-файл."""
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("{\n")
            file.write('Age_of_History: Data,\n')
            file.write('Data: [\n')
            for i, item in enumerate(data):
                pX = ','.join(map(str, item["pX"]))
                pY = ','.join(map(str, item["pY"]))
                file.write(f'{{\npX:[{pX}],\npY:[{pY}]\n}}')
                if i < len(data) - 1:
                    file.write(",\n")
            file.write("\n]}\n")

class QPointFH(QPointF):
    """docstring for QPointFH."""
    def __init__(self, x:int|float, y:int|float):
        super(QPointFH, self).__init__(x, y)
        
    def __init__(self, point:QPointF):
        super(QPointFH, self).__init__(point)
        
    def __hash__(self):
        return hash((self.x(), self.y()))
    
    def __eq__(self, other):
        return self.x() == other.x() and self.y() == other.y()

    
class PolyItem(QGraphicsPolygonItem):
    """docstring for PolyItem."""
    def __init__(self, parent:QGraphicsItem| None = None):
        super(PolyItem, self).__init__(parent)
        self._pen = QPen(Qt.NoPen)
        self.penColor = self._pen().color()
        self.penRgb = self.penColor.getRgbF()
        self.penA = self.penColor.alphaF()
        self._brush = QBrush(Qt.NoBrush)
        self.brushColor = self._brush().color()
        self.setAcceptHoverEvents(True)
    def __init__(self, polygon, parent:QGraphicsItem | None = None):
        super(PolyItem, self).__init__(polygon, parent)
    
    @property
    def pen(self):
        """The pen property."""
        return self._pen
    @pen.setter
    def pen(self, value: QPen):
        self._pen = value
    
    @property
    def brush(self):
        """The brush property."""
        return self._brush
    @brush.setter
    def brush(self, value: QBrush):
        self._brush = value

    @property
    def brushcolor(self):
        """The brushcolor property."""
        return self._brush.color()
    
    @brushcolor.setter
    def brushcolor(self, value:QColor):
        self._brush.setColor(value)
        return self._brush.color()
        
    
    def hoverEnterEvent(self, event):
        self.old = now = self.brushcolor
        r, g, b = now.getRgbF()
        a = now.alphaF()
        min, max = 50, 255
        while(self.isUnderMouse):
            while(a < max):
                self.brushcolor(QColor(r, g, b, a+20.0))
            while(a > min):
                self.brushcolor(QColor(r, g, b, a-20.0))
        # super().hoverEnterEvent(event)
    def hoverLeaveEvent(self, event):
        self.brushcolor = self.old
        # super().hoverLeaveEvent(event)


class ValueThread(QObject):
    """Потокобезопасный хранитель значения с сигналом PyQt для обновлений."""
    
    _signal = pyqtSignal(object)  # Declare the signal with 'object' type

    def __init__(self, value, *connectedFuncs : typing.Optional[typing.Callable]):
        super().__init__()
        self._value = value
        self._funcs = list(map(lambda func: self._signal.connect(func), connectedFuncs)) if connectedFuncs else []
    
    @property
    def value(self):
        """The value property."""
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self._signal.emit(self._value)  

    @property
    def signal(self):
        """The signal property."""
        return self._signal

    def connect(self, func: typing.Callable):
        """Connect a function to the signal."""
        if callable(func):
            self._signal.connect(func)
            self._funcs.append(func)
        else:
            raise ValueError("The provided function is not callable.")

    def clearConnections(self):
        self._signal.disconnect()
        self._funcs.clear()
    
    def removeConnection(self, function):
        self._signal.disconnect(function)
        self._funcs.remove(function)
