import pickle

from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QFileDialog, QHBoxLayout,
                             QMdiSubWindow, QMenu, QPushButton, QSizePolicy,
                             QSplitter, QWidget, QStyle)

from . import dialogs
from .graphics import customView
from .canvas import canvas
from .tabs import customTabWidget


class fileWindow(QMdiSubWindow):
    """
    This defines a single file, inside the application, consisting of multiple tabs that contain
    canvases. Pre-Defined so that a file can be instantly created without defining the structure again.
    """
    fileCloseEvent = pyqtSignal(int)
    
    def __init__(self, parent = None, title = 'New Project', size = 'A4', ppi = '72'):
        super(fileWindow, self).__init__(parent)
        self._sideViewTab = None
        self.index = None        
                
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        #Uses a custom QTabWidget that houses a custom new Tab Button, used to house the seperate 
        # diagrams inside a file
        self.tabber = customTabWidget(self)
        self.tabber.setObjectName(title) #store title as object name for pickling
        self.tabber.tabCloseRequested.connect(self.closeTab) # Show save alert on tab close
        self.tabber.currentChanged.connect(self.changeTab) # placeholder just to detect tab change
        self.tabber.plusClicked.connect(self.newDiagram) #connect the new tab button to add a new tab
        
        #assign layout to widget
        self.mainWidget = QWidget(self)
        layout = QHBoxLayout(self.mainWidget)
        self.createSideViewArea() #create the side view objects
        layout.addWidget(self.tabber)
        layout.addWidget(self.splitter)
        layout.addWidget(self.sideView)
        self.mainWidget.setLayout(layout)
        self.setWidget(self.mainWidget)
        self.setWindowTitle(title)
        
        #This is done so that a right click menu is shown on right click
        self.tabber.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabber.customContextMenuRequested.connect(self.contextMenu)
        
        # self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlag(Qt.CustomizeWindowHint, True)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
    
    def createSideViewArea(self):
        #creates the side view widgets and sets them to invisible
        self.splitter = QSplitter(Qt.Vertical ,self)
        self.sideView = customView(parent = self)
        self.sideView.setInteractive(False)
        self.sideViewCloseButton = QPushButton('×', self.sideView)
        self.sideViewCloseButton.setFlat(True)
        self.sideViewCloseButton.setStyleSheet("""QPushButton{
            background: rgba(214, 54, 40, 50%);
            border: 1px groove white;
            border-radius: 2px;
            font-size: 18px;
            font-weight: Bold;
            padding: 1px 2px 3px 3px;
            color: rgba(255, 255, 255, 50%);
            }
            QPushButton:Hover{
                background: rgba(214, 54, 40, 90%);
                color: rgba(255, 255, 255, 90%);            
            }
        """)
        self.sideViewCloseButton.setFixedSize(20, 20)
        self.moveSideViewCloseButton()
        self.sideViewCloseButton.clicked.connect(lambda: setattr(self, 'sideViewTab', None))
        self.splitter.setVisible(False)
        self.sideView.setVisible(False)
        self.sideView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sideView.customContextMenuRequested.connect(self.sideViewContextMenu)
        
    def resizeHandler(self):
        # resize Handler to handle resize cases.
        parentRect = self.mdiArea().size()
        current = self.tabber.currentWidget()
        width, height = current.dimensions
        
        # if side view is visible, set width to maximum possible, else use minimum requirement
        if self.sideViewTab:
            width = parentRect.width()
            height = parentRect.height()
            self.moveSideViewCloseButton()
            
        else:
            width = min(parentRect.width(), width + 100)
            height = min(parentRect.height(), height + 200)
        
        if len(self.parent().parent().subWindowList()) > 1:
            height -= 20
        
        # set element dimensions  
        self.setFixedSize(width, height)
        self.tabber.resize(width, height)
        self.tabber.currentWidget().adjustView()
         
    def contextMenu(self, point):
        #function to display the right click menu at point of right click
        menu = QMenu("Context Menu", self)
        menu.addAction("Adjust Canvas", self.adjustCanvasDialog)
        menu.addAction("Remove Side View" if self.sideViewTab == self.tabber.currentWidget() else "View Side-By-Side",
                        self.sideViewMode)
        menu.addAction("Reset Zoom", lambda : setattr(self.tabber.currentWidget().view, 'zoom', 1))
        menu.exec_(self.tabber.mapToGlobal(point))
    
    def sideViewMode(self): 
        #helper context menu function to toggle side view    
        self.sideViewTab = self.tabber.currentWidget()
    
    def adjustCanvasDialog(self):
        #helper context menu function to the context menu dialog box
        currentTab = self.tabber.currentWidget()
        result = dialogs.paperDims(self, currentTab._canvasSize, currentTab._ppi, currentTab.objectName()).exec_()
        if result is not None:
            currentTab.canvasSize, currentTab.ppi = result
            return self.resizeHandler()
        else:
            return None
        
    def sideViewToggle(self):
        #Function checks if current side view tab is set, and toggles view as required
        if self.sideViewTab:
            self.splitter.setVisible(True)
            self.sideView.setVisible(True)
            self.sideView.setScene(self.tabber.currentWidget().painter)
            self.moveSideViewCloseButton()
            self.resizeHandler()
            return True
        else:           
            self.splitter.setVisible(False)
            self.sideView.setVisible(False)
            self.resizeHandler()            
            return False
        
    def moveSideViewCloseButton(self):
        # used to place side view close button at appropriate position
        self.sideViewCloseButton.move(5, 5)
    
    def sideViewContextMenu(self, point):
        # context menu for side view
        menu = QMenu("Context Menu", self.sideView)
        menu.addAction("Reset Zoom", lambda : setattr(self.sideView, 'zoom', 1))
        menu.addSection('Change Side View Tab')
        if self.tabCount > 5:
            # just show switch dialog box, if there are 6 or more tabs open
            menu.addAction("Show switch menu", self.sideViewSwitchTab)
        else:
            # enumerate all tabs from side view.
            for i in range(self.tabCount):
                j = self.tabber.widget(i)
                if j == self.sideViewTab: 
                    continue
                # evaluate i as index, weird lambda behaviour 
                #see https://stackoverflow.com/a/33984811/7799568
                menu.addAction(f'{i}. {j.objectName()}', lambda index=i: self.sideViewSwitchCMenu(index))
        menu.addAction("Remove side view", lambda : setattr(self, 'sideViewTab', None))
        menu.exec_(self.sideView.mapToGlobal(point))

    def sideViewSwitchCMenu(self, index):
        self.sideViewTab = self.tabber.widget(index)
        
    def sideViewSwitchTab(self):
        # displays a side view switch dialog box
        tabList = [f'{i}. {j.objectName()}' for i, j in enumerate(self.tabList)] #names and index of all tabs
        initial = self.tabList.index(self.sideViewTab) # current side view tab
        result = dialogs.sideViewSwitchDialog(self.tabber, tabList, initial).exec_() #call dialog box 
        if result != initial:
            self.sideViewTab = self.tabber.widget(result) if result<self.tabCount else None
    
    @property
    def sideViewTab(self):
        #returns current active if sideViewTab otherwise None
        return self._sideViewTab
    
    @property
    def tabList(self):
        #returns a list of tabs in the given window
        return [self.tabber.widget(i) for i in range(self.tabCount)]
    
    @property
    def tabCount(self):
        #returns the number of tabs in the given window only
        return self.tabber.count()
    
    @sideViewTab.setter
    def sideViewTab(self, tab):
        #setter for side view. Also toggles view as necessary
        self._sideViewTab = None if tab == self.sideViewTab else tab
        return self.sideViewToggle()
    
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
        
    def saveProject(self, name = None):
        # called by dialog.saveEvent, saves the current file
        name = QFileDialog.getSaveFileName(self, 'Save File', f'New Diagram', 'Process Flow Diagram (*.pfd)') if not name else name
        if name[0]:
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
            diagram = canvas(self.tabber, size = dict['canvasSize'], ppi = dict['ppi'], fileWindow = self)
            diagram.__setstate__(i)
            self.tabber.addTab(diagram, i['ObjectName'])
