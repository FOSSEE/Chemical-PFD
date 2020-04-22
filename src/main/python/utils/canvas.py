from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QWidget, QGraphicsScene, QGraphicsView, QHBoxLayout
from .sizes import paperSizes, sheetDimensionList, ppiList
class canvas(QWidget):
    def __init__(self, parent=None, size= 0, ppi= 1):
        super(canvas, self).__init__(parent)
        
        self._ppi = ppiList[ppi]
        self._canvasSize = sheetDimensionList[size]
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

    @ppi.setter
    def ppi(self, ppi):
        self._ppi = ppi
        if self.painter:
            self.painter.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])