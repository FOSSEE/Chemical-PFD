import pickle
import sys

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QImage, QPainter, QPalette
from PyQt5.QtWidgets import (QComboBox, QFileDialog, QFormLayout,
                             QGraphicsScene, QGraphicsView, QGridLayout,
                             QHBoxLayout, QLabel, QMainWindow, QMenu, QMenuBar,
                             QPushButton, QTabWidget, QWidget)

from utils.canvas import canvas
from utils.sizes import ppiList, sheetDimensionList


class appWindow(QMainWindow):
    def __init__(self, parent=None):
        super(appWindow, self).__init__(parent)      
        self.resize(1280, 720)
        self._defaultPPI = 72
        self._defaultCanvasSize = "A0"
        
        titleMenu = self.menuBar()
        self.mainWidget = QWidget(self)
        self.mainWidget.setObjectName("Main Widget")
        
        self.menuFile = titleMenu.addMenu('File') #File Menu
        self.menuFile.addAction("New", self.newDiagram)
        self.menuFile.addAction("Open", self.openDiagram)
        self.menuFile.addAction("Save", self.saveDiagram)
        self.menuGenerate = titleMenu.addMenu('Generate') #Generate menu
        self.menuGenerate.addAction("Image", self.saveImage)
        self.menuGenerate.addAction("Report", self.generateReport)
                
        mainLayout = QGridLayout(self.mainWidget)
        mainLayout.setObjectName("Main Layout")
        
        self.tabber = QTabWidget(self.mainWidget)
        self.tabber.setObjectName("Tab windows")
        self.tabber.setTabsClosable(True)    
        self.tabber.tabCloseRequested.connect(self.closeTab)
        self.tabber.currentChanged.connect(self.changeTab)
        # add close action to tabs
        self.createToolbar()
        mainLayout.addWidget(self.toolbar, 0, 0, -1, 1)
        mainLayout.addWidget(self.tabber, 0, 2, -1, 10)
        
        self.mainWidget.setLayout(mainLayout)
        self.setCentralWidget(self.mainWidget)
    
    def changeTab(self, currentIndex):
        activeTab = self.tabber.widget(currentIndex)
        self.sizeComboBox.setCurrentIndex(int(activeTab._canvasSize[1]))
        self.ppiComboBox.setCurrentIndex(ppiList.index(str(activeTab._ppi)))
        
    def closeTab(self, currentIndex):
        #todo add save alert
        self.tabber.widget(currentIndex).deleteLater()
        self.tabber.removeTab(currentIndex)   

    def createToolbar(self):
        self.toolbar = QWidget(self.mainWidget)
        self.toolbar.setObjectName("Toolbar")
        toolbarLayout = QFormLayout(self.toolbar)
        self.sizeComboBox = QComboBox()
        self.sizeComboBox.addItems(sheetDimensionList)
        self.sizeComboBox.activated[str].connect(self.setCanvasSize)
        sizeLabel = QLabel("Canvas Size")
        sizeLabel.setBuddy(self.sizeComboBox)
        toolbarLayout.setWidget(0, QFormLayout.LabelRole, sizeLabel)
        toolbarLayout.setWidget(0, QFormLayout.FieldRole, self.sizeComboBox)
        
        self.ppiComboBox = QComboBox()
        self.ppiComboBox.addItems(ppiList)
        self.ppiComboBox.activated[str].connect(self.setCanvasPPI)
        ppiLabel = QLabel("Canvas ppi")
        ppiLabel.setBuddy(self.ppiComboBox)
        toolbarLayout.setWidget(1, QFormLayout.LabelRole, ppiLabel)
        toolbarLayout.setWidget(1, QFormLayout.FieldRole, self.ppiComboBox)
        self.toolbar.setLayout(toolbarLayout)
    
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
        diagram = canvas(size = self.sizeComboBox.currentIndex(), ppi = self.ppiComboBox.currentIndex())
        diagram.setObjectName("New")
        self.tabber.addTab(diagram, "New")
    
    def openDiagram(self):
        pass
    
    def saveDiagram(self):
        name = QFileDialog.getSaveFileName(self, 'Save File', 'New Diagram', 'Process Flow Diagram (*.pfd)')
        with open(name[0],'w') as file:
            for i in range(self.tabber.count()):
                file.write(self.tabber.widget(i))
    
    def saveImage(self):
        # activeDiagram = QGraphicsScene()
        activeDiagram = self.tabber.currentWidget()
        activeDiagram.painter.addEllipse(10, 10, 100, 100)
    
    def generateReport(self):
        pass

if __name__ == '__main__':
    app = ApplicationContext()       # 1. Instantiate ApplicationContext
    test = appWindow()
    test.show()
    exit_code = app.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)
