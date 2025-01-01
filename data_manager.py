import asyncio
from concurrent.futures import ThreadPoolExecutor
import os, re, orjson
import numpy as np
import typing
import random as r
from pathlib import Path
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsItem, QGraphicsPixmapItem, QGraphicsPolygonItem, QFileDialog, QMessageBox, QGraphicsEllipseItem
from PyQt5.QtGui import QColor, QPixmap, QPen, QBrush, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QPoint
from map_controller import LayerManager


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

class DataManager:
    """Класс для работы с файлами."""
    def __init__(self, scene:QGraphicsScene):
        # self.points = set()
        # self.provinces = np.array([])
        # self.background_tiles = np.array([])
        self.provinces = []
        self.background_tiles = []
        
        
        # self.background_tiles = np.append(self.background_tiles, DataManager.load_background())
        self.background_tiles.extend(DataManager.load_background())
        
        # addItem = lambda item: scene.addItem(item)
        
        # np.vectorize(addItem)(self.background_tiles)
        for tiled in self.background_tiles:
            tile:QGraphicsPixmapItem = tiled
            # tile.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
            scene.addItem(tile)

        # provs, points, pointsSet = DataManager.import_data()
        
        # self.provinces = np.append(self.provinces, DataManager.import_data()[0])
        # np.vectorize(addItem)(self.provinces)
        
        self.provinces.extend(DataManager.import_data()[0])
        # list().extend(pointsSet)
        
        for province in self.provinces:
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
    def load_data_from_folder(folder_path: str):
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
                    poly_item: QGraphicsPolygonItem = DataManager.create_polygon_item(cell)
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
    def create_polygon_item(province: dict):
        points = DataManager.read_points(province)
        polygon = QPolygonF(points)
        item:QGraphicsPolygonItem = QGraphicsPolygonItem(polygon)
        item.setPen(QPen(Qt.red))
        item.setFlag(QGraphicsItem.ItemIsSelectable,True)
        item.setBrush(QBrush(QColor(r.randint(100,255), r.randint(100,255), r.randint(100,255), 75)))
        return item
        # return {"points":points, "province":item}
    
    @staticmethod
    def read_points(province:dict):
        return [QPointF(x,y) for x, y in zip(province["pX"], province["pY"])]

    def read_file(file_path):
        """Чтение содержимого файла."""
        with open(file_path, "r", encoding="utf-8") as f:
            # print(f.read())
            res = f.read()
            return res
    
    @staticmethod
    def import_data():
        """Обработчик загрузки данных с использованием DataLoader."""
        folder_path = "F:\Program Files\Steam\steamapps\common\Age of History 3\mods\AOW\map\AOW 2\data\ProvincePoints"
        # folder_path = QFileDialog.getExistingDirectory(None, "Выберите папку с JSON-файлами провинций")
        if not folder_path:
            QMessageBox.warning(None, "Внимание", "Папка не выбрана!")
            return
        try:
            res = DataManager.load_data_from_folder(folder_path)
            return res
            
        except ValueError as e:
            QMessageBox.warning(None, "Ошибка", str(e))
        except FileNotFoundError as e:
            QMessageBox.warning(None, "Ошибка", str(e))
        except Exception as e:
            QMessageBox.critical(None, "Критическая ошибка", f"Не удалось загрузить данные: {e}")

    # @tpe(15) 
    @staticmethod
    def load_background():
        """Обработчик загрузки фона."""
        
        folder_path = "F:\Program Files\Steam\steamapps\common\Age of History 3\mods\AOW\map\AOW 2\\background\main"
        # folder_path = QFileDialog.getExistingDirectory(None, "Выберите папку с PNG-файлами фона")
        if not folder_path:
            QMessageBox.warning(None, "Внимание", "Папка не выбрана!")
            return

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
                    wX, wY = float(pixmap.width()) * x, float(pixmap.height()) * y
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
    
    

