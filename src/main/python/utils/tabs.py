from PyQt5.QtWidgets import QTabBar, QPushButton, QTabWidget
from PyQt5.QtCore import pyqtSignal, QSize

class tabBarPlus(QTabBar):
    """
    Just implemented to overload resize and layout change to emit a signal
    """
    layoutChanged = pyqtSignal()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.layoutChanged.emit()

    def tabLayoutChange(self):
        super().tabLayoutChange()
        self.layoutChanged.emit()


class customTabWidget(QTabWidget):
    """
    QTabWidget with a new tab button, also catches layoutChange signal by
    the tabBarPlus to dynamically move the button to the correct location
    """
    plusClicked = pyqtSignal()
    def __init__(self, parent=None):
        super(customTabWidget, self).__init__(parent)

        self.tab = tabBarPlus()
        self.setTabBar(self.tab) #set tabBar to our custom tabBarPlus
        
        self.plusButton = QPushButton('+', self) #create the new tab button
        #style the new tab button
        self.plusButton.setFlat(True)
        self.plusButton.setStyleSheet("""
        QPushButton{
            background: rgba(230, 230, 227, 0%);
            padding: 1px;
            border: 0px solid #E6E6E3;
            
        }
        QPushButton:hover{
            background: rgba(230, 230, 227, 60%);
        }""")
        
        #and parent it to the widget to add it at 0, 0
        self.plusButton.setFixedSize(35, 25) #set dimensions
        self.plusButton.clicked.connect(self.plusClicked.emit) #emit signal on click
        #set flags
        self.setMovable(True)
        self.setTabsClosable(True)

        self.tab.layoutChanged.connect(self.movePlusButton) #connect layout change
        # to dynamically move the button.
        
        #set custom stylesheet for the widget area
        self.setStyleSheet("""QTabWidget::pane { 
        margin: 0px,1px,1px,1px;
        border: 2px solid #E6E6E3;
        border-radius: 7px;
        padding: 1px;
        background-color: #E6E6E3;}""")
    
    def movePlusButton(self):
        #move the new tab button to correct location
        size = sum([self.tab.tabRect(i).width() for i in range(self.tab.count())])
        # calculate width of all tabs 
        h = max(self.tab.geometry().bottom() - self.plusButton.height(), 0) #align with bottom of tabbar
        w = self.tab.width()
        if size > w: #if all the tabs do not overflow the tab bar, add at the end
            self.plusButton.move(w-self.plusButton.width(), h)
        else:
            self.plusButton.move(size-3, h)