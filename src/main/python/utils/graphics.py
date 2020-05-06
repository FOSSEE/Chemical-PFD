from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsView
class customView(QGraphicsView):
    
    def __init__(self, scene, parent=None):
        super(customView, self).__init__(scene, parent)
        self.zoom = 1
        
    def wheelEvent(self, QWheelEvent):
        if Qt.ControlModifier:
            self.zoom += QWheelEvent.angleDelta().y()/2880
            self.scale(self.zoom, self.zoom)
            QWheelEvent.accept()
        else:
            return super().wheelEvent(self, QWheelEvent)