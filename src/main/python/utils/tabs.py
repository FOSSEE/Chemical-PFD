from PyQt5.QtWidgets import QTabBar, QPushButton, QTabWidget
from PyQt5.QtCore import pyqtSignal, QSize

class tabBarPlus(QTabBar):
    plusClicked = pyqtSignal()
    def __init__(self):
        super().__init__()

        self.plusButton = QPushButton("+", self)
        self.plusButton.setParent(self)
        self.setTabButton(0, QTabBar.RightSide, self.plusButton)
        self.plusButton.setFixedSize(20, 20)
        self.plusButton.clicked.connect(self.plusClicked.emit)
        # self.movePlusButton()

    def sizeHint(self):
        sizeHint = QTabBar.sizeHint(self) 
        width = sizeHint.width()
        height = sizeHint.height()
        return QSize(width+25, height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # self.movePlusButton()

    def tabLayoutChange(self):
        super().tabLayoutChange()
        # self.movePlusButton()

    def movePlusButton(self):
        size = sum([self.tabRect(i).width() for i in range(self.count())])
        h = self.geometry().top()
        w = self.width()
        if size > w:
            self.plusButton.move(w-54, h)
        else:
            self.plusButton.move(size, h)

class customTabWidget(QTabWidget):

    def __init__(self, parent=None):
        super(customTabWidget, self).__init__(parent)

        self.tab = tabBarPlus()
        self.setTabBar(self.tab)

        self.setMovable(True)
        self.setTabsClosable(True)

        # self.tab.tabMoved.connect(self.moveTab)
        # self.tabCloseRequested.connect(self.removeTab)