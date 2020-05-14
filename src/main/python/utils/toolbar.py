from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import QSize, Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QIcon, QDrag
from PyQt5.QtWidgets import (QBoxLayout, QDockWidget, QGridLayout, QLineEdit,
                             QScrollArea, QToolButton, QWidget, QApplication)

from .data import defaultToolbarItems, toolbarItems
from .funcs import grouper
from .layout import flowLayout

resourceManager = ApplicationContext()

class toolbar(QDockWidget):
    toolbuttonClicked = pyqtSignal(dict)
    
    def __init__(self, parent = None):
        super(toolbar, self).__init__(parent)
        self.toolbarButtonDict = dict()
        self.toolbarItems(defaultToolbarItems)
        self.diagAreaLayout = None
        
        self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        
        self.widget = QWidget(self)
        self.layout = QBoxLayout(QBoxLayout.TopToBottom, self.widget)
        self.setAllowedAreas(Qt.AllDockWidgetAreas)
        
        self.searchBox = QLineEdit(self.widget)
        
        self.searchBox.textChanged.connect(self.searchQuery)
        self.layout.addWidget(self.searchBox, alignment=Qt.AlignHCenter)
        
        self.diagArea = QScrollArea(self)
        self.layout.addWidget(self.diagArea)
        self.diagAreaWidget = QWidget()

        self.setWidget(self.widget)
              
    def populateToolbar(self, list):
        if self.diagAreaLayout:
            self.diagAreaLayout.deleteLater()
        self.diagAreaLayout = flowLayout(self.diagAreaWidget)
        for item in list:
            self.diagAreaLayout.addWidget(self.toolbarButtonDict[item])
        self.diagArea.setWidget(self.diagAreaWidget)
            
    def searchQuery(self):
        # shorten toolbaritems list with search items
        # self.populateToolbar() # populate with toolbar items
        text = self.searchBox.text()
        if text == '':
            self.populateToolbar(self.toolbarItemList)
        else:
            pass
            #implement shortlisting

    def resize(self):
        parent = self.parentWidget()
        # print(self.orientation())
        if parent.dockWidgetArea in [Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea] and not self.isFloating():
            self.layout.setDirection(QBoxLayout.LeftToRight)
            self.setFixedHeight(.12*parent.height())
            self.setFixedWidth(parent.width())
            self.diagAreaWidget.setFixedHeight(.12*parent.height() - 45)
        else:
            self.layout.setDirection(QBoxLayout.TopToBottom)
            self.setFixedWidth(.12*parent.width())
            self.setFixedHeight(self.height())
            self.diagAreaWidget.setFixedWidth(.12*parent.width() - 45)
    
    def resizeEvent(self, event):
        parent = self.parentWidget()
        self.layout.setDirection(QBoxLayout.TopToBottom)
        self.setFixedWidth(.12*parent.width())
        self.setFixedHeight(self.height())
        width = .12*parent.width() - 45
        self.diagAreaWidget.setFixedWidth(width)
        self.diagAreaWidget.setFixedHeight(self.diagAreaLayout.heightForWidth(width))
        return super(toolbar, self).resizeEvent(event)

    # @property
    # def toolbarItems(self):
    #     return self._toolbarItems
    
    # @toolbarItems.setter
    def toolbarItems(self, items):
        for item in items:
            obj = toolbarItems[item]
            button = toolbarButton(self, obj)
            button.clicked.connect(lambda : self.toolbuttonClicked.emit(obj))
            self.toolbarButtonDict[item] = button
            
    @property
    def toolbarItemList(self):
        return self.toolbarButtonDict.keys()
            
class toolbarButton(QToolButton):
    
    def __init__(self, parent = None, item = None):
        super(toolbarButton, self).__init__(parent)
        self.setIcon(QIcon(resourceManager.get_resource(f'toolbar/{item["icon"]}')))
        self.setIconSize(QSize(40, 40))
        self.dragStartPosition = 0
        self.itemObject = item['object']
        self.setText(item["name"])
        self.setToolTip(item["name"])

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # if event.wasHeld:
            self.dragStartPosition = event.pos()
            # else:
            #     # super(toolbarButton, self).mousePressEvent(event)
            #     self.clicked.emit()
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() and Qt.LeftButton):
            return
        if (event.pos() - self.dragStartPosition).manhattanLength() < QApplication.startDragDistance():
            return
        
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setText(self.itemObject)
        drag.setMimeData(mimeData)
        drag.exec(Qt.CopyAction)
        
    def sizeHint(self):
        return self.minimumSizeHint()
    
    def minimumSizeHint(self):
        return QSize(30, 30)