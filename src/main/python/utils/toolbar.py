from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import QSize, Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QIcon, QDrag
from PyQt5.QtWidgets import (QBoxLayout, QDockWidget, QGridLayout, QLineEdit,
                             QScrollArea, QToolButton, QWidget, QApplication)
from re import search, IGNORECASE

from .data import toolbarItems
from .funcs import grouper
from .layout import flowLayout

resourceManager = ApplicationContext() #Used to load images, mainly toolbar icons

class toolbar(QDockWidget):
    """
    Defines the right side toolbar, using QDockWidget. 
    """
    toolbuttonClicked = pyqtSignal(dict) #signal for any object button pressed 
    
    def __init__(self, parent = None):
        super(toolbar, self).__init__(parent)
        self.toolbarButtonDict = dict() #initializes empty dict to store toolbar buttons
        self.toolbarItems(toolbarItems.keys()) #creates all necessary buttons
        
        self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        #mainly used to disable closeability of QDockWidget
        
        #declare main widget and layout
        self.widget = QWidget(self)
        self.layout = QBoxLayout(QBoxLayout.TopToBottom, self.widget)
        self.setAllowedAreas(Qt.AllDockWidgetAreas)
        
        self.searchBox = QLineEdit(self.widget) #search box to search through componenets
        
        #connect signal to filter slot, add searchbar to toolbar
        self.searchBox.textChanged.connect(self.searchQuery)
        self.layout.addWidget(self.searchBox, alignment=Qt.AlignHCenter)
        
        #create a scrollable area to house all buttons
        self.diagArea = QScrollArea(self)
        self.layout.addWidget(self.diagArea)
        self.diagAreaWidget = QWidget(self.diagArea) #inner widget for scroll area
        #custom layout for inner widget
        self.diagAreaLayout = flowLayout(self.diagAreaWidget)
        
        # self.diagArea.setWidget() #set inner widget to scroll area
        self.setWidget(self.widget) #set main widget to dockwidget
    
    def clearLayout(self):
        # used to clear all items from toolbar, by parenting it to the toolbar instead
        # this works because changing parents moves widgets to be the child of the new
        # parent, setting it to none, would have qt delete them to free memory
        for i in reversed(range(self.diagAreaLayout.count())): 
            # since changing parent would effect indexing, its important to go in reverse
            self.diagAreaLayout.itemAt(i).widget().setParent(self)
            
    def populateToolbar(self, list):
        #called everytime the button box needs to be updated(incase of a filter)
        self.clearLayout() #clears layout
        for item in list:
            self.diagAreaLayout.addWidget(self.toolbarButtonDict[item])
            
    def searchQuery(self):
        # shorten toolbaritems list with search items
        # self.populateToolbar() # populate with toolbar items
        text = self.searchBox.text() #get text
        if text == '':
            self.populateToolbar(self.toolbarItemList) # restore everything on empty string
        else:
            # use regex to search filter through button list and add the remainder to toolbar
            self.populateToolbar(filter(lambda x: search(text, x, IGNORECASE), self.toolbarItemList))

    def resize(self):
        # called when main window resizes, overloading resizeEvent caused issues.
        parent = self.parentWidget() #used to get parent dimensions
        self.layout.setDirection(QBoxLayout.TopToBottom) # here so that a horizontal toolbar can be implemented later
        self.setFixedWidth(.12*parent.width()) #12% of parent width
        self.setFixedHeight(self.height()) #span available height
        width = .12*parent.width()  #12% of parent width
        self.diagAreaWidget.setFixedWidth(width) #set inner widget width
        # the following line, sets the required height for the current width, so that blank space doesnt occur
        self.diagAreaWidget.setFixedHeight(self.diagAreaLayout.heightForWidth(width))

    def toolbarItems(self, items):
        #helper functions to create required buttons
        for item in items:
            obj = toolbarItems[item]
            button = toolbarButton(self, obj)
            button.clicked.connect(lambda : self.toolbuttonClicked.emit(obj))
            self.toolbarButtonDict[item] = button
            
    @property
    def toolbarItemList(self):
        #generator to iterate over all buttons
        for i in self.toolbarButtonDict.keys():
            yield  i
            
class toolbarButton(QToolButton):
    """
    Custom buttons for components that implements drag and drop functionality
    item -> dict from toolbarItems dict, had 4 properties, name, object, icon and default arguments.
    """
    def __init__(self, parent = None, item = None):
        super(toolbarButton, self).__init__(parent)
        #uses fbs resource manager to get icons
        self.setIcon(QIcon(resourceManager.get_resource(f'toolbar/{item["icon"]}')))
        self.setIconSize(QSize(40, 40)) #unecessary but left for future references
        self.dragStartPosition = None #intialize value for drag event
        self.itemObject = item['object'] #refer current item object, to handle drag mime
        self.setText(item["name"]) #button text
        self.setToolTip(item["name"]) #button tooltip

    def mousePressEvent(self, event):
        #check if button was pressed or there was a drag intent
        super(toolbarButton, self).mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.dragStartPosition = event.pos() #set dragstart position
    
    def mouseMoveEvent(self, event):
        #handles drag
        if not (event.buttons() and Qt.LeftButton):
            return #ignore if left click is not held
        if (event.pos() - self.dragStartPosition).manhattanLength() < QApplication.startDragDistance():
            return #check if mouse was dragged enough, manhattan length is a rough and quick method in qt
        
        drag = QDrag(self) #create drag object
        mimeData = QMimeData() #create drag mime
        mimeData.setText(self.itemObject) # set mime value for view to accept
        drag.setMimeData(mimeData) # attach mime to drag
        drag.exec(Qt.CopyAction) #execute drag
        
    def sizeHint(self):
        #defines button size
        return self.minimumSizeHint()
    
    def minimumSizeHint(self):
        #defines button size
        return QSize(30, 30)