import asyncio
from concurrent.futures import ThreadPoolExecutor
import data_manager
import os, re, orjson
import numpy as np
import typing
import random as r
import traceback
from pathlib import Path
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem, QGraphicsPixmapItem, QGraphicsPolygonItem, QFileDialog, QMessageBox, QGraphicsEllipseItem, QGraphicsView
from PySide6.QtGui import QColor, QPixmap, QPen, QBrush, QPolygon, QPolygonF
from PySide6.QtCore import Qt, QPointF, QPoint, Signal, QObject, QRectF, QRect, QSize, QVariantAnimation, QAbstractAnimation


def data_folder_path_load(file_name:str):
    data_folder_path = QFileDialog.getExistingDirectory(None, "")

    path = os.path.join('', file_name)
    if not data_folder_path:
        QMessageBox.warning(None, "Внимание", "Папка не выбрана! Будет выбран последний путь.")
        
        with open(path, "r", encoding="utf-8") as file:
            res: str = file.read()
            res = res.split("\n")[0].strip()
        data_folder_path = res if res else QMessageBox.warning(None, "Внимание", "...")
        if not res:
            return []
    else:
        with open(path, "w+", encoding="utf-8") as file:
            file.write(data_folder_path)
    return data_folder_path

class DataManager:
    """Класс для работы с файлами."""
    def __init__(self, scene:QGraphicsScene):
        self.provinces = []
        self.background_tiles = []
        self.scene = scene
        self.pixoffset = 1
        
        self.load_data()

        # for tile in self.tiles:
        #     scene.addItem(tile)
        list(map(lambda tile: scene.addItem(tile), self.tiles))
        provinces = self.data [0] if self.data else []
        # for province in province:
        #     scene.addItem(province)
        list(map(lambda province: scene.addItem(province), provinces))

    def load_data(self):
        data_folder = data_folder_path_load("lastprov.txt")
        background_folder = data_folder_path_load("lastback.txt")
        self.tiles = DataManager.load_background(background_folder, self.pixoffset)
        self.data = DataManager.import_data(data_folder, self.pixoffset)
            
    
    
    

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
                    poly_item: QGraphicsPolygonItem = DataManager.create_provence_item(cell, pixoffset)
                    # provinces = np.append(provinces, poly_item)
                    provinces.append(poly_item)
            except Exception as e:
                errors.append(traceback.format_exc())
        print(errors[0]) if errors else None
        return provinces, points, pointsSet
        
    @staticmethod
    def create_point_item(position:QPointF):
        item: QGraphicsEllipseItem = QGraphicsEllipseItem(position.x() - 0.5, position.y() - 0.5, 1, 1)
        item.setPen(QPen(QColor(255, 0, 0)))
        item.setBrush(QBrush(QColor(255, 0, 0)))
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
    def create_provence_item(province: dict, pixoffset: int):
        points = DataManager.read_points(province, pixoffset)
        polygon = MEPolygonF(points)
        item:ProvenceItem = ProvenceItem(polygon)
        item.setZValue(1)
        return item
        # return {"points":points, "province":item}
    
    @staticmethod
    def read_points(province:dict, pixoffset: int):
        return [MEPointF(x + pixoffset, y + pixoffset) for x, y in zip(province["pX"], province["pY"])]

    def read_file(file_path):
        """Чтение содержимого файла."""
        with open(file_path, "r", encoding="utf-8") as f:
            # print(f.read())
            res: str = f.read()
            return res
    
    @staticmethod
    def import_data(folder_path:str, pixoffset:int):
        """Обработчик загрузки данных с использованием DataLoader."""
        
        # with open("fordev.txt", "r", encoding="utf-8") as f:
        #     res: str = f.read()
        #     res = res.split("\n")[1].strip()
        # folder_path = res
        
        data_folder_path = folder_path
                
        try:
            res = DataManager.load_data_from_folder(data_folder_path, pixoffset)
            return res
        except ValueError as e:
            QMessageBox.warning(None, "Ошибка", str(e))
        except FileNotFoundError as e:
            QMessageBox.warning(None, "Ошибка", str(e))
        except Exception as e:
            QMessageBox.critical(None, "Критическая ошибка", f"Не удалось загрузить данные: {traceback.format_exc()}")
        return[]

    # @tpe(15) 
    @staticmethod
    def load_background(folder_path:str, pixoffset: int):
        """Обработчик загрузки фона."""
        
        # with open("fordev.txt", "r", encoding="utf-8") as f:
        #     res: str = f.read()
        #     res = res.split("\n")[0].strip()
        # folder_path = res
        
                
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
                    tile.setZValue(-1)
                    # background_tiles = np.append(background_tiles, tile)
                    background_tiles.append(tile)

            except ValueError as e:
                QMessageBox.warning(None, "Ошибка", str(e))
            except FileNotFoundError as e:
                QMessageBox.warning(None, "Ошибка", str(e))
            except Exception as e:
                QMessageBox.critical(None, "Критическая ошибка", f"Не удалось загрузить фон: {traceback.format_exc()}")
        
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
            QMessageBox.critical(None, "Критическая ошибка", f"Не удалось загрузить данные: {traceback.format_exc()}")
            # raise e
    
    def exportProviense(self, floder_path: str, pixoffset: int):
        provinces = [
                    {
                        "pX": [point.x() - pixoffset for point in item.polygon()],
                        "pY": [point.y() - pixoffset for point in item.polygon()]
                    }
                    for item in filter(lambda item: isinstance(item, ProvenceItem), self.scene.items())
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
    

class MEPointF(QPointF):
    """docstring for MEPointF."""
    
    def __init__(self, *args):
        if len(args) == 2 and all(isinstance(i, int|float) for i in args):
            super().__init__(*args)
        elif len(args) == 1 and isinstance(args[0], QPointF):
            super().__init__(args[0])
        elif len(args) == 1 and isinstance(args[0], QPoint):
            super().__init__(args[0])
        elif not args or args[0] is None:
            super().__init__()
        
        else:
            raise TypeError("Invalid argument type for MEPointF")
        
    def __hash__(self):
        return hash((self.x(), self.y()))
    
    def __eq__(self, other):
        return self.x() == other.x() and self.y() == other.y()

class MEPolygonF(QPolygonF):
    """MapEditor.MEPolygonF"""

    def __init__(self, a=None):
        """
        Инициализирует объект MEPolygonF.

        Параметры:
        
        a: Переменное количество аргументов, которые могут быть:
            - None: Инициализирует пустой полигон.
            - MEPolygonF: Инициализирует полигон на основе другого объекта MEPolygonF.
            - typing.Iterable: Инициализирует полигон на основе итерации точек.
            - QRectF: Инициализирует полигон на основе прямоугольника.
            - MEPolygon: Инициализирует полигон на основе объекта MEPolygon.

        Исключения:
        TypeError: Если переданы аргументы неподдерживаемого типа.

        Описание:
        - Если аргументы не переданы, инициализирует пустой полигон.
        - Если передан объект MEPolygonF, инициализирует полигон на основе другого объекта MEPolygonF.
        - Если передана итерация, инициализирует полигон с указанными точками.
        - Если передан объект QRectF, инициализирует полигон на основе прямоугольника.
        - Если передан объект MEPolygon, инициализирует полигон на основе объекта MEPolygon.
        """
        if a is None:
            super().__init__()
        elif isinstance(a, QPolygonF):
            super().__init__(a)
        elif isinstance(a, QRectF) or isinstance(a, QRect):
            super().__init__(a)
        elif isinstance(a, QPolygon) or isinstance(a, typing.Sequence) and all(isinstance(point, QPoint) for point in a):
            super().__init__(a)
        elif isinstance(a, typing.Sequence) and all(isinstance(point, QPointF) for point in a):
            super().__init__(a)
        else:
            raise TypeError("Invalid argument type for MEPolygonF")

    def replace(self, index: int, point: QPointF):
        points = self.toList()
        points[index] = point
        self.clear()
        self.append(points)

    def index(self, point: QPointF | QPoint, isStrictly: bool = True) -> int:
        points:list = self.toList()
        return points.index(point) if (point in points) & isStrictly else points.index(min(list(map(lambda point1: point1 - point, points)), key=lambda point: point.manhattanLength()))
    # min([QPoint(r.randint(0, 100), r.randint(0, 100)) for i in range(100)], key=lambda point: point.x() + point.y())
    def isEmpty(self):
        return self.size() == 0

    def isClosed(self):
        return self.first() == self.last()
    
    def __repr__(self):
        return f"MEPolygonF({[f'{point.x(), point.y()}' for point in self]})"

class MEPolygon(QPolygon):
    """MapEditor.MEPolygon"""

    def __init__(self, a=None):
        """
        Инициализирует объект MEPolygon.

        Параметры:
        
        a: Переменное количество аргументов, которые могут быть:
            - None: Инициализирует пустой полигон.
            - typing.Iterable: Инициализирует полигон на основе итерации точек.
            - QRect: Инициализирует полигон на основе прямоугольника.
            - MEPolygonF: Инициализирует полигон на основе объекта MEPolygonF.
            - MEPolygon: Инициализирует полигон на основе другого объекта MEPolygon.

        Исключения:
        TypeError: Если переданы аргументы неподдерживаемого типа.

        Описание:
        - Если аргументы не переданы, инициализирует пустой полигон.
        - Если передана итерация, инициализирует полигон с указанными точками.
        - Если передан объект QRect, инициализирует полигон на основе прямоугольника.
        - Если передан объект MEPolygonF, инициализирует полигон на основе объекта MEPolygonF.
        - Если передан объект MEPolygon, инициализирует полигон на основе другого объекта MEPolygon.
        """
        
        if a is None:
            super().__init__()
        elif isinstance(a, typing.Iterable):
            super().__init__(list(a))
        elif isinstance(a, QRect):
            super().__init__(a)
        elif isinstance(a, QPolygonF):
            super().__init__(a.toPolygon())
        elif isinstance(a, QPolygon):
            super().__init__(a)
        else:
            raise TypeError("Invalid argument type for MEPolygon")
        
    def replace(self, index:int, point:QPoint):
        points:list = self.toList()
        points.insert(index, point)
        self = MEPolygon(points)

    def index(self, point: QPoint) -> int:
        points:list = self.toList()
        return points.index(point)
    
    def isEmpty(self):
        return self.count() == 0

    def isClosed(self):
        return self.first() == self.last()

    def __repr__(self):
        return f"MEPolygonF({[f'{point.x(), point.y()}' for point in self]})"
    
class MERect(QRect):
    """docstring for MERect."""
    
    def __init__(self, *a):
        """
        Параметры:
        
        *a: Переменное количество аргументов, которые могут быть:
            - Четыре целых числа (x, y, width, height)
            - Два объекта QPoint (верхний левый угол и нижний правый угол)
            - Объект QPoint и объект QSize (верхний левый угол и размер)
            - Объект QRect (другой прямоугольник)
        
        Исключения:
        TypeError: Если переданы аргументы неподдерживаемого типа или количества.

        Описание:
        - Если аргументы не переданы, инициализирует пустой прямоугольник.
        - Если переданы четыре целых числа, инициализирует прямоугольник с указанными координатами и размерами.
        - Если переданы два объекта QPoint, инициализирует прямоугольник с указанными углами.
        - Если переданы объект QPoint и объект QSize, инициализирует прямоугольник с указанным углом и размером.
        - Если передан объект QRect, инициализирует прямоугольник на основе другого прямоугольника.
        """
        
        if a is None:
            super().__init__()
        elif all(isinstance(i, int) for i in a) and len(a) == 4:
            super().__init__(a[0], a[1], a[2], a[3])
        elif isinstance(a[0], QPoint) and isinstance(a[1], QSize):
            super().__init__(a[0], a[1])
        elif all(isinstance(i, QPoint) for i in a) and len(a) == 2:
            super().__init__(a[0], a[1])
        elif isinstance(a[0], QRect):
            super().__init__(a[0])
        else:
            raise TypeError("Invalid argument type for MERect")
        

    
class ProvenceItem(QGraphicsPolygonItem):
    """MapEditor.ProvenceItem"""
    
    def __init__(self, a:QPolygon|QPolygonF=None, parent:QGraphicsItem=None):
        if a is None:
            super().__init__(parent)
        elif isinstance(a, QPolygonF|QPolygon):
            super().__init__(a, parent)
        else:
            raise TypeError("Invalid argument type for ProvenceItem")
        
        self.setPen(QPen(QColor(255, 0, 0)))
        self.setFlag(QGraphicsItem.ItemIsSelectable,True)
        self.setBrush(QBrush(QColor(r.randint(100,255), r.randint(100,255), r.randint(100,255), 75)))
        
            
    def __repr__(self):
        return f"ProvenceItem({self.Polygon.__repr__()})"
    
    @property
    def Polygon(self):
        """The polygon property."""
        return MEPolygonF(self.polygon())
    @Polygon.setter
    def Polygon(self, value: QPolygonF | QPolygon):
        self.setPolygon(value)    

class MEPolygonItem(QGraphicsPolygonItem):
    """MapEditor.MEPolygonItem"""
    
    def __init__(self, a:QPolygon|QPolygonF=None, parent:QGraphicsItem=None):
        if a is None:
            super().__init__(parent)
        elif isinstance(a, QPolygonF|QPolygon):
            super().__init__(a, parent)
        else:
            raise TypeError("Invalid argument type for MEPolygonItem")
    
    # def moveTo(self, *next_pos:QPoint|QPointF|float|int, duration:int=250):
    #     if len(next_pos) == 1 and isinstance(next_pos[0], QPoint|QPointF):
    #         next_pos = next_pos[0]
    #     elif len(next_pos) == 2 and all(isinstance(i, int|float) for i in next_pos):
    #         next_pos = MEPointF(*next_pos)
    #     else:
    #         raise TypeError("Invalid argument type for moveTo")
            
    #     self._animation = QVariantAnimation(
    #         duration = duration,
    #         valueChanged = self.setPos,
    #         startValue = self.pos(),
    #         endValue = next_pos)
    #     self._animation.start(QAbstractAnimation.DeleteWhenStopped)
        
    def __repr__(self):
        return f"MEPolygonItem({self.Polygon.__repr__()})"
    
    @property
    def Polygon(self):
        """The polygon property."""
        return MEPolygonF(self.polygon())
    @Polygon.setter
    def Polygon(self, value: QPolygonF | QPolygon):
        self.setPolygon(value)
    
    
class valuethread(QObject):
    """Потокобезопасный хранитель значения с сигналом PyQt для обновлений."""
    
    _signal = Signal(object)  # Declare the signal with 'object' type

    def __init__(self, value = None, *connectedFuncs : typing.Optional[typing.Callable]):
        super().__init__()
        self._value = value
        self._funcs = list(map(lambda func: self._signal.connect(func), filter(lambda func: callable(func), connectedFuncs))) if connectedFuncs else []
    
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

