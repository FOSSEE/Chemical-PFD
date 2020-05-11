from PyQt5.QtCore import pyqtSignal, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QToolBar, QWidget, QHBoxLayout, QLineEdit, QToolButton

from .data import defaultToolbarItems, toolbarItems
from .funcs import grouper

class toolbar(QToolBar):
    toolbuttonClicked = pyqtSignal(dict)
    
    def __init__(self, parent = None):
        super(toolbar, self).__init__(parent)
        self.toolbarItems = defaultToolbarItems
        self.toolbarWidgets = []
        self.setFixedWidth = 200
        
        self.searchBox = QLineEdit(self)
        self.searchBox.textChanged.connect(self.searchQuery)
        self.addWidget(self.searchBox)
              
    def populateToolbar(self):
        # self.clearWidgets()
        
        for a, b, c in grouper(3, self.toolbarItems):
            widget = QWidget(self)
            layout = QHBoxLayout(widget)
            if a is not None:
                item = toolbarItems[a]
                button = toolbarButton(self, item)
                button.clicked.connect(lambda : self.toolbuttonClicked.emit(item))
                layout.addWidget(button)
            # layout.addItem(b)
            # layout.addItem(c)
            self.toolbarWidgets.append(widget)
            self.addWidget(widget)
            
    def clearWidgets(self):
        for i in self.toolbarWidgets():
            i.deleteLater()
            
    def searchQuery(self):
        # shorten toolbaritems list with search items
        # self.populateToolbar() # populate with toolbar items
        text = self.searchBox.toPlainText()
        if text == '':
            self.toolbarItems = defaultToolbarItems
        else:
            pass
            #implement shortlisting
        
class toolbarButton(QToolButton):
    
    def __init__(self, parent = None, item = None):
        super(toolbarButton, self).__init__(parent)
        self.setIcon(QIcon(f'../../icons/toolbar/{item["icon"]}'))
        self.setIconSize(QSize(25, 25))
        self.setText(f'item["name"]')
        self.setFixedSize(30, 30)