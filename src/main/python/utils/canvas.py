from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QBrush, QPalette
from PyQt5.QtWidgets import (QFileDialog, QApplication, QHBoxLayout, QMenu,
                             QTabWidget, QWidget, QSpacerItem, QStyle, QGraphicsProxyWidget)

from . import dialogs
from .graphics import customView, customScene
from .data import paperSizes, ppiList, sheetDimensionList
from .app import shapeGrips, lines
from .streamTable import streamTable, moveRect

import shapes

class canvas(customView):
    """
    Defines the work area for a single sheet. Contains a QGraphicScene along with necessary properties
    for context menu and dialogs.
    """
        
    def __init__(self, parent=None, size= 'A0', ppi= '72' , parentMdiArea = None, parentFileWindow = None, landscape=True):
        super(canvas, self).__init__(parent=parent)
        
        #Store values for the canvas dimensions for ease of access, these are here just to be
        # manipulated by the setters and getters
        self._ppi = ppi
        self._canvasSize = size
        self._landscape = landscape
        self.streamTable = None
        #Create area for the graphic items to be placed, this is just here right now for the future
        # when we will draw items on this, this might be changed if QGraphicScene is subclassed.
        
        #set layout and background color
        self.painter = customScene()
        self.painter.labelAdded.connect(self.updateStreamTable)  
        self.painter.setBackgroundBrush(QBrush(Qt.white)) #set white background
        self.setScene(self.painter)
        
        #set initial paper size for the scene
        self.painter.setSceneRect(0, 0, *paperSizes[self._canvasSize][self._ppi])
        self.parentMdiArea = parentMdiArea
        self.parentFileWindow = parentFileWindow
        self.customContextMenuRequested.connect(self.sideViewContextMenu)
    
    def addStreamTable(self, pos=QPointF(0, 0), table=None):
        self.streamTable = table if table else streamTable(self.labelItems, canvas=self)
        
        self.streamTableRect = moveRect()
        self.streamTableRect.setFlags(moveRect.ItemIsMovable |
                                      moveRect.ItemIsSelectable)
        self.streamTableProxy = QGraphicsProxyWidget(self.streamTableRect)
        self.streamTableProxy.setWidget(self.streamTable)
        self.painter.addItem(self.streamTableRect)
        self.streamTableRect.setPos(pos)
        
    def updateStreamTable(self, item):
        if self.streamTable:
            self.streamTable.model.insertRow(item = item)
        
    def sideViewContextMenu(self, pos):
        self.parentFileWindow.sideViewContextMenu(self.mapTo(self.parentFileWindow, pos))
        
    def resizeView(self, w, h):
        #helper function to resize canvas
        self.painter.setSceneRect(0, 0, w, h)
        
    def adjustView(self):
        #utitily to adjust current diagram view
        width, height = self.dimensions
        frameWidth = self.frameWidth()
        #update view size
        self.setSceneRect(0, 0, width - frameWidth*2, height)
            
    def resizeEvent(self, event):
        #overloaded function to also view size on window update
        # self.adjustView()
        pass
   
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
    def labelItems(self):
        for i in self.items:
            if isinstance(i, (shapes.ItemLabel, shapes.LineLabel)):
                yield i
    @property
    def canvasSize(self):
        return self._canvasSize
    
    @property
    def ppi(self):
        return self._ppi
    
    @property
    def landscape(self):
        return self._landscape
    
    @canvasSize.setter
    def canvasSize(self, size):
        self._canvasSize = size
        if self.painter:
            self.resizeView(*(sorted(paperSizes[self.canvasSize][self.ppi], reverse = self.landscape)))

    @ppi.setter
    def ppi(self, ppi):
        self._ppi = ppi
        if self.painter:
            self.resizeView(*(sorted(paperSizes[self.canvasSize][self.ppi], reverse = self.landscape)))
    
    @landscape.setter
    def landscape(self, bool):
        self._landscape = bool
        if self.painter:
            self.resizeView(*(sorted(paperSizes[self.canvasSize][self.ppi], reverse = self.landscape)))

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
            "landscape": self.landscape
        }
    
    def __setstate__(self, dict):
        self._ppi = dict['ppi']
        self._canvasSize = dict['canvasSize']
        self.landscape = dict['landscape']
        self.setObjectName(dict['ObjectName'])
        
        for item in dict['symbols']:
            graphic = getattr(shapes, item['_classname_'])()
            graphic.__setstate__(dict = item)
            self.painter.addItem(graphic)
            graphic.setPos(*item['pos'])
            graphic.updateLineGripItem()
            graphic.updateSizeGripItem()
            for gripitem in item['lineGripItems']:
                shapeGrips[gripitem[0]] = (graphic, gripitem[1])
            if item['label']:
                graphicLabel = shapes.ItemLabel(pos = QPointF(*item['label']['pos']), parent = graphic)
                graphicLabel.__setstate__(item['label'])
                self.painter.addItem(graphicLabel)
        
        for item in dict['lines']:
            line = shapes.Line(QPointF(*item['startPoint']), QPointF(*item['endPoint']))
            lines[item['id']] = line
            line.__setstate__(dict = item)
            self.painter.addItem(line)
            graphic, index = shapeGrips[item['startGripItem']]
            line.startGripItem = graphic.lineGripItems[index]
            graphic.lineGripItems[index].line = line
            if item['endGripItem']:                
                graphic, index = shapeGrips[item['endGripItem']]
                line.endGripItem = graphic.lineGripItems[index]
                graphic.lineGripItems[index].line = line
            else:
                line.refLine = lines[item['refLine']]
                lines[item['refLine']].midLines.append(line)
                line.refIndex = item['refIndex']
            for label in item['label']:
                labelItem = shapes.LineLabel(QPointF(*label['pos']), line)
                line.label.append(labelItem)
                labelItem.__setstate__(label)
                self.painter.addItem(labelItem)
            line.updateLine()
            line.addGrabber()
            
        shapeGrips.clear()
        lines.clear()
        self.painter.advance()
        
        

 