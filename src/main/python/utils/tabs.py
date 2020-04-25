from PyQt5.QtWidgets import QTabBar, QPushButton, QTabWidget
from PyQt5.QtCore import pyqtSignal, QSize

class tabBarPlus(QTabBar):
    layoutChanged = pyqtSignal()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.layoutChanged.emit()

    def tabLayoutChange(self):
        super().tabLayoutChange()
        self.layoutChanged.emit()


class customTabWidget(QTabWidget):
    plusClicked = pyqtSignal()
    def __init__(self, parent=None):
        super(customTabWidget, self).__init__(parent)

        self.tab = tabBarPlus()
        self.setTabBar(self.tab)
        
        self.plusButton = QPushButton('+', self)
        self.plusButton.setFixedSize(35, 25)
        self.plusButton.clicked.connect(self.plusClicked.emit)
        self.setMovable(True)
        self.setTabsClosable(True)

        self.tab.layoutChanged.connect(self.movePlusButton)
    
    def movePlusButton(self):
        size = sum([self.tab.tabRect(i).width() for i in range(self.tab.count())])
        h = max(self.tab.geometry().bottom() - 25, 0)
        w = self.tab.width()
        if size > w:
            self.plusButton.move(w-self.plusButton.width(), h)
        else:
            self.plusButton.move(size-3, h)