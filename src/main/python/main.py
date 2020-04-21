from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtGui import (QBrush, QColor, QImage, QPainter,
                         QPalette)
from PyQt5.QtWidgets import (QWidget, QComboBox, QMainWindow, QGraphicsScene,
                             QGraphicsView, QGridLayout, QHBoxLayout, QLabel,
                             QPushButton, QMenuBar, QMenu, QFormLayout, QTabWidget)

from utils.canvas import canvas
import sys

class appWindow(QMainWindow):
    def __init__(self, parent=None):
        super(appWindow, self).__init__(parent)      
        self.resize(1280, 720)
        self._defaultPPI = 72
        self._defaultCanvasSize = "A0"
        
        titleMenu = self.menuBar()
        self.mainWidget = QWidget(self)
        
        self.menuFile = titleMenu.addMenu('File') #File Menu
        self.menuFile.addAction("new", self.newDiagram)
        self.menuGenerate = titleMenu.addMenu('Generate') #Generate menu
        self.menuGenerate.addAction("Image", self.saveImage)
        self.menuGenerate.addAction("Report", self.generateReport)
        
                
        mainLayout = QGridLayout(self.mainWidget)
        self.tabber = QTabWidget(self.mainWidget)
        self.tabber.setTabsClosable(True)    
        # QObject.connect(self.tabber, pyqtSignal(QTabWidget.tabCloseRequested(int)), self, pyqtSlot(QTabWidget.closetab(int)))
        # add close action to tabs
        self.createToolbar()
        mainLayout.addLayout(self.toolbar, 0, 0, -1, 1)
        mainLayout.addWidget(self.tabber, 0, 2, -1, 10)
        
        self.mainWidget.setLayout(mainLayout)
        self.setCentralWidget(self.mainWidget)
        
    def createToolbar(self):
        self.toolbar = QFormLayout(self.mainWidget)
        sizeComboBox = QComboBox()
        sizeComboBox.addItems([f'A{i}' for i in range(5)])
        # sizeComboBox.activated[str].connect(lambda: self.tabber.currentWidget().setCanvasSize)
        sizeComboBox.activated[str].connect(self.setCanvasSize)
        sizeLabel = QLabel("Canvas Size")
        sizeLabel.setBuddy(sizeComboBox)
        self.toolbar.setWidget(0, QFormLayout.LabelRole, sizeLabel)
        self.toolbar.setWidget(0, QFormLayout.FieldRole, sizeComboBox)
        
        ppiComboBox = QComboBox()
        ppiComboBox.addItems(["72", "96", "150", "300"])
        # ppiComboBox.activated[str].connect(lambda: self.tabber.currentWidget().setCanvasPPI)
        ppiComboBox.activated[str].connect(self.setCanvasPPI)
        ppiLabel = QLabel("Canvas ppi")
        ppiLabel.setBuddy(ppiComboBox)
        self.toolbar.setWidget(1, QFormLayout.LabelRole, ppiLabel)
        self.toolbar.setWidget(1, QFormLayout.FieldRole, ppiComboBox)
    
    def setCanvasSize(self, size):
        self._defaultCanvasSize = size
        activeCanvas = self.tabber.currentWidget()
        if activeCanvas:
            activeCanvas.canvasSize = size
    
    def setCanvasPPI(self, ppi):
        self._defaultPPI = ppi
        activeCanvas = self.tabber.currentWidget()
        if activeCanvas:
            activeCanvas.ppi = ppi
    
    def newDiagram(self):
        diagram = canvas(size = self._defaultCanvasSize, ppi = self._defaultPPI)
        self.tabber.addTab(diagram, "New")
    
    def saveImage(self):
        pass
    
    def generateReport(self):
        pass

if __name__ == '__main__':
    app = ApplicationContext()       # 1. Instantiate ApplicationContext
    test = appWindow()
    test.show()
    exit_code = app.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)