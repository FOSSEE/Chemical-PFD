from fbs_runtime.application_context.PyQt5 import ApplicationContext

from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QToolBar, QWidget, QGridLayout, QLineEdit, QToolButton, QScrollArea, QDockWidget, QVBoxLayout

from .data import defaultToolbarItems, toolbarItems
from .funcs import grouper
from .layout import flowLayout

resourceManager = ApplicationContext()

class toolbar(QToolBar):
    toolbuttonClicked = pyqtSignal(dict)
    
    def __init__(self, parent = None):
        super(toolbar, self).__init__(parent)
        self.toolbarItems = defaultToolbarItems
        # self.widget = QWidget(self)
        # self.layout = QVBoxLayout(self.widget)
        self.setAllowedAreas(Qt.LeftToolBarArea | Qt.RightToolBarArea)
        
        self.searchBox = QLineEdit(self)
        # self.searchBox = QLineEdit(self.widget)
        self.searchBox.textChanged.connect(self.searchQuery)
        self.addWidget(self.searchBox)
        # self.layout.addWidget(self.searchBox)
        
        self.addSeparator()
        self.diagArea = QScrollArea(self)
        self.addWidget(self.diagArea)
        # self.layout.addWidget(self.diagArea)
        self.diagAreaWidget = QWidget()
        self.diagAreaWidget.setFixedWidth(200)
        # self.setWidget(self.widget)
              
    def populateToolbar(self):
        # layout = QGridLayout(self.diagAreaWidget)
        # n = self.width() // 45
        # for i, items in enumerate(grouper(n, self.toolbarItems)):
        #     for j, item in enumerate(items):
        #         if item is not None:
        #             item = toolbarItems[item]
        #             button = toolbarButton(self, item)
        #             button.clicked.connect(lambda : self.toolbuttonClicked.emit(item))
        #             layout.addWidget(button, i, j, 1, 1, alignment=Qt.AlignHCenter)
        layout = flowLayout(self.diagAreaWidget)
        for item in self.toolbarItems:
            obj = toolbarItems[item]
            button = toolbarButton(self, obj)
            button.clicked.connect(lambda : self.toolbuttonClicked.emit(obj))
            layout.addWidget(button)
        self.diagArea.setWidget(self.diagAreaWidget)
            
    def searchQuery(self):
        # shorten toolbaritems list with search items
        # self.populateToolbar() # populate with toolbar items
        text = self.searchBox.toPlainText()
        if text == '':
            self.toolbarItems = defaultToolbarItems
        else:
            pass
            #implement shortlisting
    
    def resize(self):
        pass
    
    def resizeEvent(self, event):
        self.resize()
        self.setFixedWidth(.11*self.parentWidget().width())
        self.diagAreaWidget.setFixedWidth(.11*self.parentWidget().width() - 30)
        self.diagArea.setFixedHeight(.7*self.parentWidget().height())
        return super(toolbar, self).resizeEvent(event)

class toolbarButton(QToolButton):
    
    def __init__(self, parent = None, item = None):
        super(toolbarButton, self).__init__(parent)
        self.setIcon(QIcon(resourceManager.get_resource(f'toolbar/{item["icon"]}')))
        self.setIconSize(QSize(40, 40))
        self.setText(f'item["name"]')
        self.setFixedSize(30, 30)
    