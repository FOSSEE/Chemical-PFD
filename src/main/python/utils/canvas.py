import pickle

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QPalette
from PyQt5.QtWidgets import (QFileDialog, QApplication, QHBoxLayout, QMenu,
                             QTabWidget, QWidget, QSpacerItem, QStyle)

from . import dialogs
from .graphics import customView, customScene
from .data import paperSizes, ppiList, sheetDimensionList

class canvas(QWidget):
    """
    Defines the work area for a single sheet. Contains a QGraphicScene along with necessary properties
    for context menu and dialogs.
    """
        
    def __init__(self, parent=None, size= 'A4', ppi= '72'):
        super(canvas, self).__init__(parent)
        
        #Store values for the canvas dimensions for ease of access, these are here just to be
        # manipulated by the setters and getters
        self._ppi = ppi
        self._canvasSize = size
        # self.setFixedSize(parent.size())
        #Create area for the graphic items to be placed, this is just here right now for the future
        # when we will draw items on this, this might be changed if QGraphicScene is subclassed.
        
        #set layout and background color
        self.painter = customScene()        
        self.painter.setBackgroundBrush(QBrush(Qt.white)) #set white background
        
        self.view = customView(self.painter, self) #create a viewport for the canvas board
        
        self.layout = QHBoxLayout(self) #create the layout of the canvas, the canvas could just subclass QGView instead
        self.layout.addWidget(self.view, alignment=Qt.AlignCenter)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        #set initial paper size for the scene
        self.painter.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])
        
        #set pointers to necessary parents for ease of reference
        self.parentMdiArea = self.parent().parentWidget().parentWidget().parentWidget().parentWidget()
        self.parentFileWindow = self.parent().parentWidget().parentWidget()

    def resizeView(self, w, h):
        #helper function to resize canvas
        self.painter.setSceneRect(0, 0, w, h)

    def adjustView(self):
        #utitily to adjust current diagram view
        width, height = self.dimensions
        frameWidth = self.view.frameWidth()
        #update view size
        self.view.setSceneRect(0, 0, width - frameWidth*2, height)
        
        # use the available mdi area, also add padding
        prect = self.parentMdiArea.rect()
        width = width + 20
        height = height + 60

        # add scrollbar size to width and height if they are visible, avoids clipping
        if self.view.verticalScrollBar().isVisible():
            width += self.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        if self.view.horizontalScrollBar().isVisible():
            height += self.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        
        #if view is visible use half of available width
        factor = 2 if self.parentFileWindow.sideViewTab is not None else 1
        #use minimum width required to fit the view
        width = min((prect.width() - 40)//factor, width) 
        height = min(prect.height() - 80, height)
        #set view dims
        self.view.setFixedWidth(width)
        self.view.setFixedHeight(height)
        
    def resizeEvent(self, event):
        #overloaded function to also view size on window update
        self.adjustView()
   
    def setCanvasSize(self, size):
        """
        extended setter for dialog box
        """
        self.canvasSize = size
    
    def setCanvasPPI(self, ppi):
        """
        extended setter for dialog box
        """
        self.ppi = ppi
    
    @property
    def dimensions(self):
        #returns the dimension of the current scene
        return self.painter.sceneRect().width(), self.painter.sceneRect().height()
    @property
    def items(self):
        # generator to filter out certain items
        for i in self.painter.items():
            yield i
    
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
            self.resizeView(*paperSizes[self.canvasSize][self.ppi])

    @ppi.setter
    def ppi(self, ppi):
        self._ppi = ppi
        if self.painter:
            self.resizeView(*paperSizes[self.canvasSize][self.ppi])
        
    #following 2 methods are defined for correct pickling of the scene. may be changed to json or xml later so as
    # to not have a binary file.
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
            graphic.__setstate__(item)
            self.painter.addItem(graphic)

 