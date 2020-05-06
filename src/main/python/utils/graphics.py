from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsView

class customView(QGraphicsView):
    
    def __init__(self, scene = None, parent=None):
        if scene is not None:
            super(customView, self).__init__(scene, parent)
        else:
            super(customView, self).__init__(parent)
        self._zoom = 1
        self.setDragMode(True)
        
    def wheelEvent(self, QWheelEvent):
        if Qt.ControlModifier:
            if QWheelEvent.source() == Qt.MouseEventNotSynthesized:
                if self.zoom + QWheelEvent.angleDelta().y()/2880 > 0.1:
                    self.zoom += QWheelEvent.angleDelta().y()/2880
            else:
                if self.zoom + QWheelEvent.pixelDelta().y() > 0.1:
                    self.zoom += QWheelEvent.angleDelta().y()
            QWheelEvent.accept()
        else:
            return super().wheelEvent(self, QWheelEvent)
    
    @property
    def zoom(self):
        return self._zoom
    
    @zoom.setter
    def zoom(self, value):
        temp = self.zoom
        self._zoom = value
        self.scale(self.zoom / temp, self.zoom / temp)