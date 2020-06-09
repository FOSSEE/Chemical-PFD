from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QBrush, QPalette
from PyQt5.QtWidgets import (QFileDialog, QApplication, QHBoxLayout, QMenu,
                             QTabWidget, QWidget, QSpacerItem, QStyle)

from . import dialogs
from .graphics import customView, customScene
from .data import paperSizes, ppiList, sheetDimensionList
from .app import dumps, loads, JSON_Typer, shapeGrips, lines

import shapes

class canvas(QWidget):
    """
    Defines the work area for a single sheet. Contains a QGraphicScene along with necessary properties
    for context menu and dialogs.
    """
        
    def __init__(self, parent=None, size= 'A4', ppi= '72' , parentMdiArea = None, parentFileWindow = None):
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
        self.painter.setSceneRect(0, 0, *paperSizes[self._canvasSize][self._ppi])
        self.parentMdiArea = parentMdiArea
        self.parentFileWindow = parentFileWindow

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
            "symbols": [i for i in self.painter.items() if isinstance(i, shapes.NodeItem)],
            "lines": sorted([i for i in self.painter.items() if isinstance(i, shapes.Line)], key = lambda x: 1 if x.refLine else 0),
            # "lineLabels": [i.__getstate__() for i in self.painter.items() if isinstance(i, shapes.LineLabel)],
            # "itemLabels": [i.__getstate__() for i in self.painter.items() if isinstance(i, shapes.itemLabel)]
        }
    
    def __setstate__(self, dict):
        self._ppi = dict['ppi']
        self._canvasSize = dict['canvasSize']
        self.setObjectName(dict['ObjectName'])
        
        for item in dict['symbols']:
            graphic = getattr(shapes, item['_classname_'])()
            graphic.__setstate__(dict = item)
            self.painter.addItem(graphic)
            graphic.setPos(*item['pos'])
            for gripitem in item['lineGripItems']:
                shapeGrips[gripitem[0]] = (graphic, gripitem[1])
        
        for item in dict['lines']:
            line = shapes.Line(QPointF(*item['startPoint']), QPointF(*item['endPoint']))
            lines[item['id']] = line
            line.__setstate__(dict = item)
            graphic, index = shapeGrips[item['startGripItem']]
            line.setStartGripItem = graphic.lineGripItems[index]
            graphic.lineGripItems[index].line = line
            if item['endGripItem']:
                graphic, index = shapeGrips[item['endGripItem']]
                line.setEndGripItem = graphic.lineGripItems[index]
                graphic.lineGripItems[index].line = line
            else:
                line.refLine = lines[item['refLine']]
                line.refIndex = item['refIndex']
            self.painter.addItem(line)
            # line.addGrabber()
        
        shapeGrips.clear()
        lines.clear()
        self.painter.advance()
        
        # for item in dict['lineLabels']:
        #     pass
        # for item in dict['itemLabels']:
        #     pass

 