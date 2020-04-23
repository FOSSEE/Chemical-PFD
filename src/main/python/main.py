import pickle
import sys

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QImage, QPainter, QPalette
from PyQt5.QtWidgets import (QComboBox, QFileDialog, QFormLayout,
                             QGraphicsScene, QGraphicsView, QGridLayout,
                             QHBoxLayout, QLabel, QMainWindow, QMenu, QMenuBar,
                             QPushButton, QTabWidget, QWidget, QMdiArea, QMessageBox)

from utils.canvas import canvas, fileWindow
from utils.sizes import ppiList, sheetDimensionList


class appWindow(QMainWindow):
    def __init__(self, parent=None):
        super(appWindow, self).__init__(parent)      
        self.resize(1280, 720)
        # self.setWindowState(Qt.WindowMaximized)
        self._defaultPPI = 72
        self._defaultCanvasSize = "A4"
        
        titleMenu = self.menuBar()
        self.mainWidget = QWidget(self)
        self.mainWidget.setObjectName("Main Widget")
        
        self.menuFile = titleMenu.addMenu('File') #File Menu
        self.menuFile.addAction("New", self.newProject)
        self.menuFile.addAction("Open", self.openProject)
        self.menuFile.addAction("Save", self.saveProject)
        self.menuGenerate = titleMenu.addMenu('Generate') #Generate menu
        self.menuGenerate.addAction("Image", self.saveImage)
        self.menuGenerate.addAction("Report", self.generateReport)
                
        # mainLayout = QGridLayout(self.mainWidget)
        mainLayout = QHBoxLayout(self.mainWidget)
        mainLayout.setObjectName("Main Layout")
        
        #ImpsaveProject
        self.mdi = QMdiArea(self)
        # add close action to tabs
        
        self.createToolbar()
        mainLayout.addWidget(self.toolbar)
        mainLayout.addWidget(self.mdi)
        #declare main window layout
        self.mainWidget.setLayout(mainLayout)
        self.setCentralWidget(self.mainWidget)

    def createToolbar(self):
        self.toolbar = QWidget(self.mainWidget)
        self.toolbar.setObjectName("Toolbar")
        self.toolbar.setFixedWidth(200)
        toolbarLayout = QFormLayout(self.toolbar)
        self.sizeComboBox = QComboBox()
        self.sizeComboBox.addItems(sheetDimensionList)
        self.sizeComboBox.setCurrentIndex(4)
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
        activeCanvas = self.mdi.currentSubWindow()
        activeCanvas._defaultCanvasSize = size
        if activeCanvas:
            activeCanvas.canvasSize = size
            # self.tabber.resize(*activeCanvas.dimensions)
            print(activeCanvas.dimensions)
    
    def setCanvasPPI(self, ppi):
        self._defaultPPI = ppi
        activeCanvas = self.mdi.currentSubWindow()
        activeCanvas._defaultPPI = ppi        
        if activeCanvas:
            activeCanvas.ppi = ppi
            # self.tabber.resize(*activeCanvas.dimensions)            
    
    def newProject(self):
        project = fileWindow(self.mdi, size = self._defaultCanvasSize, ppi = self._defaultPPI)
        project.setObjectName("New Project")
        self.mdi.addSubWindow(project)
        if not project.tabList:
            project.newDiagram()
        project.show()
        project.resizeHandler(self.mdi)
    
    def openProject(self):
        name = QFileDialog.getOpenFileNames(self, 'Open File(s)', '', 'Process Flow Diagram (*pfd)')
        if name:
            for files in name[0]:
                with open(files,'rb') as file:
                    project = pickle.load(file)
                    self.mdi.addSubWindow(project)
                    project.show()
                    project.resizeHandler(self.mdi)
                    
    
    def saveProject(self):
        for j, i in enumerate(self.mdi.subWindowList()):
            if i.tabCount:
                name = QFileDialog.getSaveFileName(self, 'Save File', f'New Diagram {j}', 'Process Flow Diagram (*.pfd)')
                i.saveProject(name)
    
    def saveImage(self):
        pass
    
    def generateReport(self):
        pass
    
    def resizeEvent(self, event):
        self.mdi.activeSubWindow().resizeHandler(self.mdi)
        super(appWindow, self).resizeEvent(event)
        
    def closeEvent(self, event):
        if self.saveEvent():
            event.accept()
        else:
            event.ignore()

    def saveEvent(self, event):
        alert = QMessageBox.question(self, self.objectName(), "All unsaved progress will be LOST!",
                                     QMessageBox.StandardButtons(QMessageBox.Save|QMessageBox.Ignore|QMessageBox.Cancel), QMessageBox.Save)
        if alert == QMessageBox.Cancel:
            return False
        else:
            if alert == QMessageBox.Save:
                if not self.saveProject():
                    return False
        return True

if __name__ == '__main__':
    app = ApplicationContext()       # 1. Instantiate ApplicationContext
    test = appWindow()
    test.show()
    exit_code = app.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)
