from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QFileDialog, QHBoxLayout,
                             QMdiSubWindow, QMenu, QPushButton, QSizePolicy,
                             QSplitter, QWidget, QStyle, QSizePolicy, QLabel)
from os import path, mkdir
from . import dialogs
from .graphics import CustomView
from .canvas import canvas
from .tabs import CustomTabWidget
from .undo import resizeCommand
from .app import dump, loads, JSON_Typer, version


class FileWindow(QMdiSubWindow):
    """
    This defines a single file, inside the application, consisting of multiple tabs that contain
    canvases. Pre-Defined so that a file can be instantly created without defining the structure again.
    """
    fileCloseEvent = pyqtSignal(int)
    tabChangeEvent = pyqtSignal()
    
    def __init__(self, parent = None, title = 'New Project', size = 'A0', ppi = '72'):
        super(FileWindow, self).__init__(parent)
        self._sideViewTab = None
        self.index = None
        self.projectFilePath = ""

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        #Uses a custom QTabWidget that houses a custom new Tab Button, used to house the seperate 
        # diagrams inside a file
        self.tabber = CustomTabWidget(self)
        self.tabber.setObjectName(title) #store title as object name for pickling
        self.tabber.tabCloseRequested.connect(self.closeTab) # Show save alert on tab close
        self.tabber.currentChanged.connect(self.changeTab) # placeholder just to detect tab change
        self.tabber.plusClicked.connect(self.newDiagram) #connect the new tab button to add a new tab
        
        #assign layout to widget
        self.mainWidget = QWidget(self)
        layout = QHBoxLayout(self.mainWidget)
        self.createSideViewArea() #create the side view objects
        
        # set size policies for window
        left = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        left.setHorizontalStretch(1)
        self.tabber.setSizePolicy(left)
        
        right = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        right.setHorizontalStretch(1)
        self.sideView.setSizePolicy(right)
        
        #build widget layout
        layout.addWidget(self.tabber)
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
        self.setWindowFlag(Qt.WindowCloseButtonHint, True)

        #creating label to indicate that the file is not saved
        self.label = QLabel('File not saved.', self)
        self.label.setGeometry(30, 50, 100, 20)

    def createSideViewArea(self):
        #creates the side view widgets and sets them to invisible
        self.sideView = CustomView(parent = self)
        self.sideView.setInteractive(False)
        self.sideViewCloseButton = QPushButton('×', self.sideView)
        self.sideViewCloseButton.setObjectName("sideViewCloseButton")
        self.sideViewCloseButton.setFlat(True)
        self.sideViewCloseButton.setFixedSize(20, 20)
        self.moveSideViewCloseButton()
        self.sideViewCloseButton.clicked.connect(lambda: setattr(self, 'sideViewTab', None))
        self.sideView.setVisible(False)
        self.sideView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sideView.customContextMenuRequested.connect(self.sideViewContextMenu)
        self.sideView.resize(self.width()//2 - self.sideView.frameWidth(), self.height())
        if(self.property('isEdited')):
            self.label.setHidden(True)
        
    def resizeHandler(self):
        # resize Handler to handle resize cases.
        parentRect = self.mdiArea().size()
        current = self.tabber.currentWidget()
        width, height = 0,0
        if(current):
            width,height=current.dimensions
        
        if self.sideViewTab:
            width2, height2 = self.sideViewTab.dimensions
            width = min(parentRect.width(), width + width2)
            height = min(parentRect.height(), height + height2)
        else:
            # width = min(parentRect.width(), width + 100)
            width = parentRect.width()
            # height = min(parentRect.height(), height + 150)
            height = parentRect.height()
        
        if len(self.parent().parent().subWindowList()) > 1:
            height -= 20
        
        # set element dimensions
        self.setFixedSize(width, height)
        if(current):
            current.adjustView()
         
    def contextMenu(self, point):
        #function to display the right click menu at point of right click
        menu = QMenu("Context Menu", self)
        menu.addAction("Adjust Canvas", self.adjustCanvasDialog)
        menu.addAction("Remove Side View" if self.sideViewTab == self.tabber.currentWidget() else "View Side-By-Side",
                        self.sideViewMode)
        menu.addAction("Reset Zoom", lambda : setattr(self.tabber.currentWidget().view, 'zoom', 1))
        if self.tabber.currentWidget().streamTable is None:
            menu.addAction("Add Stream Table", lambda x=self, pos=point: x.tabber.currentWidget().addStreamTable(pos))
        menu.exec_(self.tabber.mapToGlobal(point))
    
    def sideViewMode(self): 
        #helper context menu function to toggle side view    
        self.sideViewTab = self.tabber.currentWidget()
    
    def adjustCanvasDialog(self):
        #helper context menu function to the context menu dialog box
        currentTab = self.tabber.currentWidget()
        result = dialogs.paperDims(self, currentTab._canvasSize, currentTab._ppi, currentTab.objectName(), currentTab.landscape).exec_()
        if result is not None:
            currentTab.painter.undoStack.push(resizeCommand(result, currentTab, self))
        
    def sideViewToggle(self):
        #Function checks if current side view tab is set, and toggles view as required
        if self.sideViewTab:
            self.sideView.setVisible(True)
            self.sideView.setScene(self.tabber.currentWidget().painter)
            self.resizeHandler()
            return True
        else:
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
        # helper function to swtich side view tab
        self.sideViewTab = self.tabber.widget(index)
        
    def sideViewSwitchTab(self):
        # displays a side view switch dialog box
        tabList = [f'{i}. {j.objectName()}' for i, j in enumerate(self.tabList)] #names and index of all tabs
        initial = self.tabList.index(self.sideViewTab) # current side view tab
        result = dialogs.sideViewSwitchDialog(self.tabber, tabList, initial).exec_() #call dialog box 
        if result != initial:
            self.sideViewTab = self.tabber.widget(result) if result<self.tabCount else None

    def toggleLabel(self):
        e = self.property("isEdited")
        if(e):
            self.label.setHidden(False)
            self.label.show()
        else:
            self.label.setHidden(True)
    
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
    
    @property
    def isEdited(self):
        return self.isEdited
    
    @isEdited.setter
    def isEdited(self, val):
        self.isEdited = not(val) if val == self.isEdited else val
        return self.toggleLabel()
    
    def changeTab(self, currentIndex):
        #placeholder function to detect tab change
        self.resizeHandler()        
        self.tabChangeEvent.emit()
    
    def closeTab(self, currentIndex):
        #show save alert on tab close
        if(dialogs.saveEvent(self)):
            self.tabber.widget(currentIndex).deleteLater()
            self.tabber.removeTab(currentIndex)
        
    def newDiagram(self, objectName = "New"):
        # helper function to add a new tab on pressing new tab button, using the add tab method on QTabWidget
        diagram = canvas(self.tabber, parentMdiArea = self.mdiArea(), parentFileWindow = self)
        diagram.setObjectName(objectName)
        index = self.tabber.addTab(diagram, objectName)
        self.tabber.setCurrentIndex(index)
        return diagram
        
    def saveProject(self, name = None):
        # called by dialog.saveEvent, saves the current file
        if(self.projectFilePath):
            self.setObjectName(path.basename(self.projectFilePath).split(".")[0])
            self.setWindowTitle(self.objectName())
            with open(self.projectFilePath,'w') as file: 
                dump(self, file, indent=4, cls=JSON_Typer)
            self.setProperty("isEdited", False)
            self.label.setHidden(True)
            return True
        document_path = path.join(path.expanduser('~/Documents'),'PFDs')
        if(not path.exists(document_path)):
           mkdir(document_path)
        name = QFileDialog.getSaveFileName(self, 'Save File', f'{document_path}/Flow_Diagram.pfd', 'Process Flow Diagram (*.pfd)') if not name else name
        if name[0]:
            self.setObjectName(path.basename(name[0]).split(".")[0])
            self.setWindowTitle(self.objectName())
            with open(name[0],'w') as file: 
                dump(self, file, indent=4, cls=JSON_Typer)
            self.setProperty("isEdited", False)
            self.label.setHidden(True)
            return True
        else:
            return False

    def closeEvent(self, event):
        # handle save alert on file close, check if current file has no tabs aswell.
        print("function called with edit: ", self.property("isEdited"))
        if(self.property("isEdited")):
            if self.tabCount==0 or dialogs.saveEvent(self):
                event.accept()
                self.deleteLater()
                self.fileCloseEvent.emit(self.index)
            else:
                event.ignore()
        else:
            self.deleteLater()
            self.fileCloseEvent.emit(self.index)

    #following 2 methods are defined for correct serialization of the scene.
    def __getstate__(self) -> dict:
        return {
            "_classname_": self.__class__.__name__,
            "version": version,
            "ObjectName": self.objectName(),
            "tabs": [i.__getstate__() for i in self.tabList]
        }
    
    def __setstate__(self, dict):
        self.setObjectName(dict['ObjectName'])
        self.setWindowTitle(dict['ObjectName'])
        for i in dict['tabs']:
            diagram = self.newDiagram(i['ObjectName'])
            diagram.__setstate__(i)
