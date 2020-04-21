from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QWidget, QGraphicsScene, QGraphicsView, QHBoxLayout
from .sizes import paperSizes
class canvas(QWidget):
    def __init__(self, parent=None, size= "A0", ppi= 72):
        super(canvas, self).__init__(parent)
        
        self._ppi = ppi
        self._canvasSize = size
        self.resize(1280, 720)
           
        
        self.painter = QGraphicsScene(0, 0, *paperSizes[self.canvasSize][self.ppi])
        self.painter.setBackgroundBrush(QBrush(Qt.white))
        self.view = QGraphicsView(self.painter)
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.view)
        self.setLayout(self.layout)
        
    def setCanvasSize(self, size):
        self.canvasSize = size
    
    def setCanvasPPI(self, ppi):  
        self.ppi = ppi
    
    @property
    def canvasSize(self):
        return self._canvasSize
    @property
    def ppi(self):
        return self._ppi
    
    @canvasSize.setter
    def canvasSize(self, size):
        self._canvasSize = size
        if self.painter:
            self.painter.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])
        # print(*paperSizes[self.canvasSize][self.ppi]) 

    @ppi.setter
    def ppi(self, ppi):
        self._ppi = int(ppi)
        if self.painter:
            self.painter.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])
        # print(*paperSizes[self.canvasSize][self.ppi]) 