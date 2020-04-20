from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QBrush, QColor, QImage, QPainter,
                         QPalette)
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, QGraphicsScene,
                             QGraphicsView, QGridLayout, QHBoxLayout, QLabel,
                             QMessageBox, QPushButton, QStyleFactory)
from utils.sizes import paperSizes
import sys
class appWindow(QDialog):
    def __init__(self, parent=None):
        super(appWindow, self).__init__(parent)
        
        self._ppi = 72
        self._canvasSize = "A0"
        self.resize(1280, 720)
           
        
        self.painter = QGraphicsScene(0, 0, *paperSizes[self.canvasSize][self.ppi])
        self.painter.setBackgroundBrush(QBrush(Qt.white))
        
        self.createToolbar()
        self.canvas = QGraphicsView(self.painter)
        mainLayout = QGridLayout()
        mainLayout.addLayout(self.topLayout, 0, 0, 1, -1)
        mainLayout.addWidget(self.canvas, 1, 0, -1, -1)
        self.setLayout(mainLayout)
        
    def createToolbar(self):
        self.topLayout = QHBoxLayout()
        sizeComboBox = QComboBox()
        sizeComboBox.addItems([f'A{i}' for i in range(5)])
        sizeComboBox.activated[str].connect(self.setCanvasSize)
        sizeLabel = QLabel("Canvas Size")
        sizeLabel.setBuddy(sizeComboBox)
        self.topLayout.addWidget(sizeLabel)
        self.topLayout.addWidget(sizeComboBox)
        
        ppiComboBox = QComboBox()
        ppiComboBox.addItems(["72", "96", "150", "300"])
        ppiComboBox.activated[str].connect(self.setCanvasPPI)
        ppiLabel = QLabel("Canvas ppi")
        ppiLabel.setBuddy(ppiComboBox)
        self.topLayout.addWidget(ppiLabel)
        self.topLayout.addWidget(ppiComboBox)
    
    def setCanvasSize(self, size):
        self.canvasSize = size
    
    def setCanvasPPI(self, ppi):  
        self.ppi = ppi
    
    @property
    def canvasSize(self):
        return self._canvasSize
    @property
    def ppi(self):
        return self._ppi
    
    @canvasSize.setter
    def canvasSize(self, size):
        self._canvasSize = size
        if self.painter:
            self.painter.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])
        print(*paperSizes[self.canvasSize][self.ppi]) 

    @ppi.setter
    def ppi(self, ppi):
        self._ppi = int(ppi)
        if self.painter:
            self.painter.setSceneRect(0, 0, *paperSizes[self.canvasSize][self.ppi])
        print(*paperSizes[self.canvasSize][self.ppi]) 
           
if __name__ == '__main__':
    app = ApplicationContext()       # 1. Instantiate ApplicationContext
    test = appWindow()
    test.show()
    exit_code = app.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)