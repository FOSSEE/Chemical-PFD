from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsView

class customView(QGraphicsView):
    """
    Defines custom QGraphicsView with zoom features, overriding wheel event
    """
    def __init__(self, scene = None, parent=None):
        if scene is not None: #overloaded constructor
            super(customView, self).__init__(scene, parent)
        else:
            super(customView, self).__init__(parent)
        self._zoom = 1
        self.setDragMode(True)
        
    def wheelEvent(self, QWheelEvent):
        #overload wheelevent, to zoom if control is pressed, else scroll normally
        if Qt.ControlModifier: #check if control is pressed
            if QWheelEvent.source() == Qt.MouseEventNotSynthesized: #check if precision mouse(mac)
                # angle delta is 1/8th of a degree per scroll unit
                if self.zoom + QWheelEvent.angleDelta().y()/2880 > 0.1: # hit and trial value (2880)
                    self.zoom += QWheelEvent.angleDelta().y()/2880
            else:
                # precision delta is exactly equal to amount to scroll
                if self.zoom + QWheelEvent.pixelDelta().y() > 0.1:
                    self.zoom += QWheelEvent.angleDelta().y()
            QWheelEvent.accept() # accept event so that scrolling doesnt happen simultaneously
        else:
            return super().wheelEvent(self, QWheelEvent) # scroll if ctrl not pressed
    
    @property
    def zoom(self):
        # property for zoom
        return self._zoom
    
    @zoom.setter
    def zoom(self, value):
        # set scale according to zoom value being set
        temp = self.zoom
        self._zoom = value
        self.scale(self.zoom / temp, self.zoom / temp)