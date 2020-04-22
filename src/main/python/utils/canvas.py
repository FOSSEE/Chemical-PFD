from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QHBoxLayout, QWidget

from . import graphics
from .sizes import paperSizes, ppiList, sheetDimensionList


class canvas(QWidget):
    def __init__(self, parent=None, size= 0, ppi= 1):
        super(canvas, self).__init__(parent)
        
        self._ppi = ppiList[ppi]
        self._canvasSize = sheetDimensionList[size]        
        self.painter = QGraphicsScene(0, 0, *paperSizes[self.canvasSize][self.ppi])
        self.painter.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])
        self.setMaximumSize(*paperSizes[self.canvasSize][self.ppi])
        self.resize(*paperSizes[self.canvasSize][self.ppi])
        self.painter.setBackgroundBrush(QBrush(Qt.white))
        self.view = QGraphicsView(self.painter)
        self.view.setMaximumSize(794, 1123)
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
            self.setMaximumSize(*paperSizes[self.canvasSize][self.ppi])
            self.resize(*paperSizes[self.canvasSize][self.ppi])


    @ppi.setter
    def ppi(self, ppi):
        self._ppi = ppi
        if self.painter:
            self.painter.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])
            self.setMaximumSize(*paperSizes[self.canvasSize][self.ppi])
            self.resize(*paperSizes[self.canvasSize][self.ppi])

    @property
    def dimensions(self):
        return self.painter.sceneRect().width(), self.painter.sceneRect().height()
    
    def __getstate__(self) -> dict:
        return {
            "_classname_": self.__class__.__name__,
            "ppi": self._ppi,
            "canvasSize": self._canvasSize,
            "ObjectName": self.objectName(),
            "items": [i.__getState__() for i in self.painter.items()]
        }
    
    def __setstate__(self, dict):
        self.__init__()
        self._ppi = dict['ppi']
        self._canvasSize = dict['canvasSize']
        self.setObjectName(dict['ObjectName'])
        for item in dict['items']:
            graphic = getattr(graphics, dict['_classname_'])
            graphic.setstate(item)
            self.painter.addItem(graphic)
