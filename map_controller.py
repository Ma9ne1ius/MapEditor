from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, 
)
from PyQt5.QtGui import QPainter, QColor, QPen, QPolygonF, QPixmap
from PyQt5.QtCore import Qt, QPointF

class MapController:
    """Класс для управления данными карты."""
    def __init__(self):
        self.layers = {}
        self.visibility = {}

    def add_layer(self, name, items):
        self.layers[name] = items
        self.visibility[name] = True

    def toggle_visibility(self, name, visible):
        self.visibility[name] = visible
        for item in self.layers.get(name, []):
            item.setVisible(visible)

    def render_map(self):
        """Отрисовка карты с учетом видимости слоев."""
        self.scene.clear()
        if self.layers["background"]:
            self.draw_background()

        if self.layers["provinces"]:
            self.draw_provinces()

        if self.layers["connections"]:
            self.draw_connections()
    
    def draw_background(self):
        """Отрисовка фона карты."""
        self.scene.fill((30, 30, 30))  # Заливка основного фона
        try:    
            for tile in self.background_tiles:
                tileSurface = tile["tile"]
                weight, hight = tileSurface.get_size()
                
                x = tile["x"] * weight - self.controller.x * self.controller.zoom
                y = tile["y"] * hight - self.controller.y * self.controller.zoom
                scaled_tile = pygame.transform.scale(
                    tileSurface, (int(weight * self.controller.zoom), int(hight * self.controller.zoom))
                )
                if(x + self.screen.get_size()[0] * self.controller.zoom < 0 or y + self.screen.get_size()[1] * self.controller.zoom < 0):
                    continue
                if x > self.screen.get_size()[0] or y > self.screen.get_size()[1]:
                    continue
                self.background_surface.blit(scaled_tile, (x, y))
        finally:
            # self.lock.release()
            ...

    def draw_provinces(self):
        """Отрисовка провинций."""
        for province in self.data.get("provinces", []):
            points = [QPointF(p["x"], p["y"]) for p in province["points"]]
            self.scene.addPolygon(QPolygonF(points), QPen(Qt.red))

    def draw_connections(self):
        """Отрисовка связей между точками."""
        for conn in self.data.get("connections", []):
            p1 = QPointF(conn["start"]["x"], conn["start"]["y"])
            p2 = QPointF(conn["end"]["x"], conn["end"]["y"])
            self.scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), QPen(Qt.red))


    def render_background(self):
        # while True:
            # print(self.background_tiles)
            self.background_surface.fill((30, 30, 30))  # Заливка основного фона
            # self.lock.acquire()
            try:    
                for tile in self.background_tiles:
                    tileSurface = tile["tile"]
                    weight, hight = tileSurface.get_size()
                    # # Вычисление положения тайла
                    x = tile["x"] * weight - self.controller.x * self.controller.zoom
                    y = tile["y"] * hight - self.controller.y * self.controller.zoom
                    # scaled_tile = 
                    scaled_tile = pygame.transform.scale(
                        tileSurface, (int(weight * self.controller.zoom), int(hight * self.controller.zoom))
                    )
                    if(x + self.screen.get_size()[0] * self.controller.zoom < 0 or y + self.screen.get_size()[1] * self.controller.zoom < 0):
                        continue
                    if x > self.screen.get_size()[0] or y > self.screen.get_size()[1]:
                        continue
                    self.background_surface.blit(scaled_tile, (x, y))
            finally:
                # self.lock.release()
                ...



def render_provinces(self):
    # while True:
        self.province_surface.fill((0, 0, 0, 0))  # Заливка основного фона
        try:
            for province in self.province_data["Data"]:
                if "pX" in province and "pY" in province:
                    points = [
                        (
                            (x - self.controller.x) * self.controller.zoom,
                            (y - self.controller.y) * self.controller.zoom,
                        )
                        for x, y in zip(province["pX"], province["pY"])
                    ]
                    pygame.draw.polygon( self.province_surface, (255, 0, 0), points, 1)
        finally:
            ...

def to_screen(self):
    # while True:
        self.screen.blit(self.background_surface, (0, 0))  # Отображаем фон
        self.screen.blit(self.province_surface, (0, 0))  # Отображаем провинции
        self.screen.fill((30, 30, 30))  # Очистка экрана
        pygame.display.flip()

class LayerManager:
    def __init__(self):
        self.layers = {}
        self.visibility = {}

    def add_layer(self, name: str, items):
        self.layers[name] = items
        self.visibility[name] = True

    def toggle_visibility(self, name: str, visible: bool):
        self.visibility[name] = visible
        for item in self.layers.get(name, []):
            item.setVisible(visible)

