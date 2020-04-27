import pickle

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QPalette
from PyQt5.QtWidgets import (QFileDialog, QFormLayout,
                             QGraphicsScene, QGraphicsView, QHBoxLayout,
                             QMdiSubWindow, QMenu,
                             QTabWidget, QWidget, QSpacerItem)

from . import graphics, dialogs
from .sizes import paperSizes, ppiList, sheetDimensionList
from .tabs import customTabWidget

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
        self.painter = QGraphicsScene()        
        self.painter.setBackgroundBrush(QBrush(Qt.white)) #set white background
        
        self.view = QGraphicsView(self.painter) #create a viewport for the canvas board
        
        self.layout = QHBoxLayout(self) #create the layout of the canvas, the canvas could just subclass QGView instead
        self.layout.addWidget(self.view, stretch = 1, alignment= Qt.AlignLeft)
        self.spacer = QSpacerItem(1, self.height()) #Horizonatal spacer to force view to not expand to fill widget
        self.layout.addSpacerItem(self.spacer)

        #set layout and background color
        self.setPalette(self.palette)
        self.setLayout(self.layout)        
        
        #This is done so that a right click menu is shown on right click
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)
        
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

    @property
    def dimensions(self):
        #returns the dimension of the current scene
        return self.painter.sceneRect().width(), self.painter.sceneRect().height()
    
    def resizeView(self, w=None, h=None):
        #resize canvas to appropriate size.
        if w is None and h is None:
            w, h = paperSizes[self.canvasSize][self.ppi]
        self.painter.setSceneRect(0, 0, w, h)
        self.view.setSceneRect(0, 0, w, h)            
        w = min(self.width() - 5, w)
        h = self.height() - 5
        self.view.setFixedWidth(w)
        self.view.setFixedHeight(h)
        
    def contextMenu(self, point):
        #function to display the right click menu at point of right click
        menu = QMenu("Context Menu", self)
        menu.addAction("Adjust Canvas", self.adjustCanvasDialog)
        menu.exec_(self.mapToGlobal(point))
        
    def adjustCanvasDialog(self):
        #helper function to the context menu dialog box
        self.canvasSize, self.ppi = dialogs.paperDims(self, self._canvasSize, self._ppi, self.objectName()).exec_()

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

class fileWindow(QMdiSubWindow):
    """
    This defines a single file, inside the application, consisting of multiple tabs that contain
    canvases. Pre-Defined so that a file can be instantly created without defining the structure again.
    """
    def __init__(self, parent = None, title = 'New Project', size = 'A4', ppi = '72'):
        super(fileWindow, self).__init__(parent)
        
        #Uses a custom QTabWidget that houses a custom new Tab Button, used to house the seperate 
        # diagrams inside a file
        self.tabber = customTabWidget(self)
        self.tabber.setObjectName(title) #store title as object name for pickling
        self.tabber.tabCloseRequested.connect(self.closeTab) # Show save alert on tab close
        self.tabber.currentChanged.connect(self.changeTab) # placeholder just to detect tab change
        self.tabber.plusClicked.connect(self.newDiagram) #connect the new tab button to add a new tab
        
        #assign layout to widget
        self.setWidget(self.tabber)
        self.setWindowTitle(title)     

    def changeTab(self, currentIndex):
        #placeholder function to detect tab change
        pass
    
    def closeTab(self, currentIndex):
        #show save alert on tab close
        if dialogs.saveEvent(self):
            self.tabber.widget(currentIndex).deleteLater()
            self.tabber.removeTab(currentIndex)
        
    def newDiagram(self):
        # helper function to add a new tab on pressing new tab button, using the add tab method on QTabWidget
        diagram = canvas(self.tabber)
        diagram.setObjectName("New")
        self.tabber.addTab(diagram, "New")
        diagram.resizeView()
    
    def resizeHandler(self, parent = None):
        # experimental resize Handler to handle resize on parent resize.
        parentRect = parent.rect() if parent else self.parent().rect()
        self.resize(parentRect.width(), parentRect.height())
        self.setMaximumHeight(parentRect.height())
        self.tabber.setMaximumHeight(parentRect.height())
        for i in self.tabList:
            i.setMaximumHeight(parentRect.height())
        self.tabber.currentWidget().resizeView()
    
    @property
    def tabList(self):
        #returns a list of tabs in the given window
        return [self.tabber.widget(i) for i in range(self.tabCount)]
    
    @property
    def tabCount(self):
        #returns the number of tabs in the given window only
        return self.tabber.count()
    
    def saveProject(self, name = None):
        # called by dialog.saveEvent, saves the current file
        name = QFileDialog.getSaveFileName(self, 'Save File', f'New Diagram', 'Process Flow Diagram (*.pfd)') if not name else name
        if name:
            with open(name[0],'wb') as file:
                pickle.dump(self, file)
            return True
        else:
            return False

    def closeEvent(self, event):
        # handle save alert on file close, check if current file has no tabs aswell.
        if self.tabCount==0 or dialogs.saveEvent(self):
            event.accept()
            self.deleteLater()
        else:
            event.ignore()

    #following 2 methods are defined for correct pickling of the scene. may be changed to json or xml later so as
    # to not have a binary file.
    def __getstate__(self) -> dict:
        return {
            "_classname_": self.__class__.__name__,
            "ObjectName": self.objectName(),
            "ppi": self._ppi,
            "canvasSize": self._canvasSize,
            "tabs": [i.__getstate__() for i in self.tabList]
        }
    
    def __setstate__(self, dict):
        self.__init__(title = dict['ObjectName'])
        for i in dict['tabs']:
            diagram = canvas(self.tabber, size = dict['canvasSize'], ppi = dict['ppi'])
            diagram.__setstate__(i)
            self.tabber.addTab(diagram, i['ObjectName'])
    
   