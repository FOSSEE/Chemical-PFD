import pickle

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import (QComboBox, QDialog, QFileDialog, QFormLayout,
                             QGraphicsScene, QGraphicsView, QHBoxLayout,
                             QLabel, QMainWindow, QMdiSubWindow, QMenu,
                             QMessageBox, QTabWidget, QWidget)

from . import graphics, dialogs
from .sizes import paperSizes, ppiList, sheetDimensionList
from .tabs import customTabWidget

class canvas(QWidget):
    def __init__(self, parent=None, size= 'A4', ppi= '72'):
        super(canvas, self).__init__(parent)
        
        self._ppi = ppi
        self._canvasSize = size
        
        self.painter = QGraphicsScene()
        self.painter.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])
        
        self.painter.setBackgroundBrush(QBrush(Qt.white))
        
        self.view = QGraphicsView(self.painter)
        self.view.setMinimumSize(595, 842)          
        self.view.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])        
        
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.view)  
        self.setLayout(self.layout)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)
        
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
            self.view.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])

    @ppi.setter
    def ppi(self, ppi):
        self._ppi = ppi
        if self.painter:
            self.painter.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])
            self.view.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])

    @property
    def dimensions(self):
        return self.painter.sceneRect().width(), self.painter.sceneRect().height()
    
    def contextMenu(self, point):
        menu = QMenu("Context Menu", self)
        menu.addAction("Adjust Canvas", self.adjustCanvasDialog)
        menu.exec_(self.mapToGlobal(point))
        
    def adjustCanvasDialog(self):
        self.canvasSize, self.ppi = dialogs.paperDims(self, self._canvasSize, self._ppi, self.objectName).exec_()

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
    def __init__(self, parent = None, title = 'New Project', size = 'A4', ppi = '72'):
        super(fileWindow, self).__init__(parent)
        
        self.tabber = customTabWidget(self)
        self.tabber.setObjectName(title)
        self.tabber.tabCloseRequested.connect(self.closeTab)
        self.tabber.currentChanged.connect(self.changeTab)
        self.tabber.plusClicked.connect(self.newDiagram)
        
        self.setWidget(self.tabber)
        self.setWindowTitle(title)
        
    @property
    def canvasSize(self):
        return self._canvasSize
    @property
    def ppi(self):
        return self._ppi
    
    @canvasSize.setter
    def canvasSize(self, size):
        self._canvasSize = sheetDimensionList.index(size)
        if self.tabCount:
            activeTab = self.tabber.currentWidget()
            activeTab.canvasSize = size
    
    @ppi.setter
    def ppi(self, ppi):
        self._ppi = ppiList.index(ppi)
        if self.tabCount:
            activeTab = self.tabber.currentWidget()
            activeTab.ppi = ppi
            

    def changeTab(self, currentIndex):
        pass
    
    def closeTab(self, currentIndex):
        if dialogs.saveEvent(self):
            self.tabber.widget(currentIndex).deleteLater()
            self.tabber.removeTab(currentIndex)
        
    def newDiagram(self):
        diagram = canvas(self.tabber)
        diagram.setObjectName("New")
        self.tabber.addTab(diagram, "New")
    
    def resizeHandler(self, parent = None):
        parentRect = parent.rect() if parent else self.parent().rect()
        self.resize(parentRect.width(), parentRect.height())
        self.setMaximumHeight(parentRect.height())
        self.tabber.setMaximumHeight(parentRect.height())
        for i in self.tabList:
            i.setMaximumHeight(parentRect.height())
    
    @property
    def tabList(self):
        return [self.tabber.widget(i) for i in range(self.tabCount)]
    
    @property
    def tabCount(self):
        return self.tabber.count()
    
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
    
    def saveProject(self, name = None):
        name = QFileDialog.getSaveFileName(self, 'Save File', f'New Diagram', 'Process Flow Diagram (*.pfd)') if not name else name
        if name:
            with open(name[0],'wb') as file:
                pickle.dump(self, file)
            return True
        else:
            return False

    def closeEvent(self, event):
        if self.tabCount==0 or dialogs.saveEvent(self):
            event.accept()
            self.deleteLater()
        else:
            event.ignore()
