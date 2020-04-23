import pickle

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import (QFileDialog, QGraphicsScene, QGraphicsView,
                             QHBoxLayout, QMainWindow, QMdiSubWindow,
                             QMessageBox, QTabWidget, QWidget, QMenuBar, QVBoxLayout)

from . import graphics
from .sizes import paperSizes, ppiList, sheetDimensionList


class canvas(QWidget):
    def __init__(self, parent=None, size= 4, ppi= 1):
        super(canvas, self).__init__(parent)
        
        self._ppi = ppiList[ppi]
        self._canvasSize = sheetDimensionList[size]
        
        self.painter = QGraphicsScene()
        self.painter.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])
        
        self.painter.setBackgroundBrush(QBrush(Qt.white))
        
        self.view = QGraphicsView(self.painter)
        self.view.setMinimumSize(595, 842)          
        self.view.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])        
        
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
    def __init__(self, parent = None, title = 'New Project'):
        super(fileWindow, self).__init__(parent)
        
        self.widget = QWidget(self)
        layout = QVBoxLayout(self.widget)
        
        self.tabber = QTabWidget(self.widget)
        self.tabber.setObjectName(title)
        self.tabber.setTabsClosable(True)    
        self.tabber.tabCloseRequested.connect(self.closeTab)
        self.tabber.currentChanged.connect(self.changeTab)
        layout.addWidget(self.tabber)
        
        titleMenu = QMenuBar(self)
        menuFile = titleMenu.addMenu('File') #File Menu
        menuFile.addAction("New", self.newDiagram)
        layout.setMenuBar(titleMenu)
        
        self.widget.setLayout(layout)
        self.setWidget(self.widget)
        self.setWindowTitle(title)

    def changeTab(self, currentIndex):
        pass
    
    def closeTab(self, currentIndex):
        if self.saveEvent():
            self.tabber.widget(currentIndex).deleteLater()
            self.tabber.removeTab(currentIndex)
        
    def newDiagram(self):
        diagram = canvas()
        diagram.setObjectName("New")
        self.tabber.addTab(diagram, "New")
    
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
            "tabs": [i.__getstate__() for i in self.tabList]
        }
    
    def __setstate__(self, dict):
        self.__init__(title = dict['ObjectName'])
        for i in dict['tabs']:
            diagram = canvas()
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
        if self.saveEvent():
            event.accept()
        else:
            event.ignore()
        # super(fileWindow, self).closeEvent(event)
    def saveEvent(self):
        alert = QMessageBox.question(self, self.objectName(), "All unsaved progress will be LOST!",
                                     QMessageBox.StandardButtons(QMessageBox.Save|QMessageBox.Ignore|QMessageBox.Cancel), QMessageBox.Save)
        if alert == QMessageBox.Cancel:
            return False
        else:
            if alert == QMessageBox.Save:
                if not self.saveProject():
                    return False
        return True          