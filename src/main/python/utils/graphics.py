from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsProxyWidget, QGraphicsItem
from PyQt5 import QtWidgets

class customView(QGraphicsView):
    """
    Defines custom QGraphicsView with zoom features and drag-drop accept event, overriding wheel event
    """
    def __init__(self, scene = None, parent=None):
        if scene is not None: #overloaded constructor
            super(customView, self).__init__(scene, parent)
        else:
            super(customView, self).__init__(parent)
        self._zoom = 1
        self.setDragMode(True) #sets pannable using mouse
        self.setAcceptDrops(True) #sets ability to accept drops
    
    #following four functions are required to be overridden for drag-drop functionality
    def dragEnterEvent(self, QDragEnterEvent):
        #defines acceptable drop items
        if QDragEnterEvent.mimeData().hasText():
            QDragEnterEvent.acceptProposedAction()
        
    def dragMoveEvent(self, QDragMoveEvent):
        #defines acceptable drop items
        if QDragMoveEvent.mimeData().hasText():
            QDragMoveEvent.acceptProposedAction()
            
    def dragLeaveEvent(self, QDragLeaveEvent):
        #accept any drag leave event, avoid unnecessary logging
        QDragLeaveEvent.accept()
    
    def dropEvent(self, QDropEvent):
        #defines item drop, fetches text, creates corresponding QGraphicItem and adds it to scene
        if QDropEvent.mimeData().hasText():
            #QDropEvent.mimeData().text() defines intended drop item, the pos values define position
            graphic = getattr(QtWidgets, QDropEvent.mimeData().text())(QDropEvent.pos().x()-150, QDropEvent.pos().y()-150, 300, 300)
            graphic.setPen(QPen(Qt.black, 2))
            graphic.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
            self.scene().addItem(graphic) 
            QDropEvent.acceptProposedAction()
     
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
        
class customScene(QGraphicsScene):
    """
    re-implement QGraphicsScene for future functionality 
    hint: QUndoFramework
    """
    pass
        