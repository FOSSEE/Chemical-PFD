import pickle

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMdiSubWindow, QFileDialog, QMenu, QSizePolicy

from . import dialogs
from .canvas import canvas
from .tabs import customTabWidget

class fileWindow(QMdiSubWindow):
    """
    This defines a single file, inside the application, consisting of multiple tabs that contain
    canvases. Pre-Defined so that a file can be instantly created without defining the structure again.
    """
    fileCloseEvent = pyqtSignal(int)
    fileMinimized = pyqtSignal(QMdiSubWindow)
    def __init__(self, parent = None, title = 'New Project', size = 'A4', ppi = '72'):
        super(fileWindow, self).__init__(parent)
        
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.index = None
        #Uses a custom QTabWidget that houses a custom new Tab Button, used to house the seperate 
        # diagrams inside a file
        self.tabber = customTabWidget(self)
        self.tabber.setObjectName(title) #store title as object name for pickling
        self.tabber.tabCloseRequested.connect(self.closeTab) # Show save alert on tab close
        self.tabber.currentChanged.connect(self.changeTab) # placeholder just to detect tab change
        self.tabber.plusClicked.connect(self.newDiagram) #connect the new tab button to add a new tab
        # self.tabber.setContentsMargins(0, 1, 1, 1)
        #assign layout to widget
        self.setWidget(self.tabber)
        self.setWindowTitle(title)
        
        #This is done so that a right click menu is shown on right click
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)
        
        # self.windowStateChanged.connect(self.stateChange)
        
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlag(Qt.CustomizeWindowHint, True)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        
    def changeTab(self, currentIndex):
        #placeholder function to detect tab change
        self.resizeHandler()        
    
    def closeTab(self, currentIndex):
        #show save alert on tab close
        if dialogs.saveEvent(self):
            self.tabber.widget(currentIndex).deleteLater()
            self.tabber.removeTab(currentIndex)
        
    def newDiagram(self):
        # helper function to add a new tab on pressing new tab button, using the add tab method on QTabWidget
        diagram = canvas(self.tabber)
        diagram.setObjectName("New")
        index = self.tabber.addTab(diagram, "New")
        self.tabber.setCurrentIndex(index)

    def resizeHandler(self):
        # experimental resize Handler to handle resize on parent resize.
        parentRect = self.mdiArea().size()
        current = self.tabber.currentWidget()
        width, height = current.dimensions
        width = min(parentRect.width(), width + 100)
        height = min(parentRect.height(), height + 200)
        # width = parentRect.width()
        # height = parentRect.height()
        self.setFixedSize(width, height)
        self.tabber.resize(width, height)
        self.tabber.currentWidget().adjustView()
    
    def contextMenu(self, point):
        #function to display the right click menu at point of right click
        menu = QMenu("Context Menu", self)
        menu.addAction("Adjust Canvas", self.adjustCanvasDialog)
        menu.exec_(self.mapToGlobal(point))
        
    def adjustCanvasDialog(self):
        #helper function to the context menu dialog box
        currentTab = self.tabber.currentWidget()
        result = dialogs.paperDims(self, currentTab._canvasSize, currentTab._ppi, currentTab.objectName()).exec_()
        if result is not None:
            currentTab.canvasSize, currentTab.ppi = result
            return self.resizeHandler()
        else:
            return None
    
    # def stateChange(self, oldState, newState):
    #     if newState == Qt.WindowMinimized:
    #         print("a")
    #         self.setVisible(False)
    #     elif newState == Qt.WindowMaximized:
    #         print("b")
    #         parentRect = self.mdiArea().size()
    #         self.setFixedSize(parentRect.width(), parentRect.height())
    #         self.tabber.resize(parentRect.width(), parentRect.height())
    #         self.tabber.currentWidget().adjustView()
    #     else:
    #         if oldState == Qt.WindowMinimized or oldState == Qt.WindowMaximized:
    #             print("c")            
    #             self.resizeHandler()

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
            self.fileCloseEvent.emit(self.index)
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
