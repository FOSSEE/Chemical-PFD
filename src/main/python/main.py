import pickle
import sys

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QImage, QPainter, QPalette
from PyQt5.QtWidgets import (QComboBox, QFileDialog, QFormLayout,
                             QGraphicsScene, QGraphicsView, QGridLayout,
                             QHBoxLayout, QLabel, QMainWindow, QMenu, QMenuBar,
                             QPushButton, QTabWidget, QWidget, QMdiArea, QMessageBox)

from utils.canvas import canvas
from utils.fileWindow import fileWindow
from utils.sizes import ppiList, sheetDimensionList
from utils import dialogs


class appWindow(QMainWindow):
    """
    Application entry point, subclasses QMainWindow and implements the main widget,
    sets necessary window behaviour etc.
    """
    def __init__(self, parent=None):
        super(appWindow, self).__init__(parent)
        self.mainWidget = QWidget(self) #create new widget
        
        #create the menu bar
        titleMenu = self.menuBar() #fetch reference to current menu bar
        self.mainWidget.setObjectName("Main Widget")
        
        self.menuFile = titleMenu.addMenu('File') #File Menu
        self.menuFile.addAction("New", self.newProject)
        self.menuFile.addAction("Open", self.openProject)
        self.menuFile.addAction("Save", self.saveProject)
        
        self.menuGenerate = titleMenu.addMenu('Generate') #Generate menu
        self.menuGenerate.addAction("Image", self.saveImage)
        self.menuGenerate.addAction("Report", self.generateReport)
                
        # create new layout for the main widget
        mainLayout = QHBoxLayout(self.mainWidget)
        mainLayout.setObjectName("Main Layout")
        
        self.mdi = QMdiArea(self) #create area for files to be displayed
        self.mdi.setObjectName('mdi area')
        
        #create toolbar and add the toolbar plus mdi to layout
        self.createToolbar()
        mainLayout.addWidget(self.toolbar)
        mainLayout.addWidget(self.mdi)
        
        #declare main window layout
        self.mainWidget.setLayout(mainLayout)
        self.setCentralWidget(self.mainWidget)
        self.resize(1280, 720) #set collapse dim
        self.setWindowState(Qt.WindowMaximized) #launch maximized

    def createToolbar(self):
        #place holder for toolbar with fixed width, layout may change
        self.toolbar = QWidget(self.mainWidget)
        self.toolbar.setObjectName("Toolbar")
        self.toolbar.setFixedWidth(200)
        toolbarLayout = QFormLayout(self.toolbar)
        self.toolbar.setLayout(toolbarLayout)     
    
    def newProject(self):
        #call to create a new file inside mdi area
        project = fileWindow(self.mdi)
        project.setObjectName("New Project")
        self.mdi.addSubWindow(project)
        if not project.tabList: # important when unpickling a file instead
            project.newDiagram() #create a new tab in the new file
        project.show()
        project.resizeHandler()
    
    def openProject(self):
        #show the open file dialog to open a saved file, then unpickle it.
        name = QFileDialog.getOpenFileNames(self, 'Open File(s)', '', 'Process Flow Diagram (*pfd)')
        if name:
            for files in name[0]:
                with open(files,'rb') as file:
                    project = pickle.load(file)
                    self.mdi.addSubWindow(project)
                    project.show()             
    
    def saveProject(self):
        #pickle all files in mdi area
        for j, i in enumerate(self.mdi.activeFiles): #get list of all windows with atleast one tab
            if i.tabCount:
                name = QFileDialog.getSaveFileName(self, 'Save File', f'New Diagram {j}', 'Process Flow Diagram (*.pfd)')
                i.saveProject(name)
        else:
            return False
        return True
    
    def saveImage(self):
        #place holder for future implementaion
        pass
    
    def generateReport(self):
        #place holder for future implementaion        
        pass
    
    def resizeEvent(self, event):
        #overload resize to also handle resize on file windows inside
        if self.mdi.activeSubWindow():
            self.mdi.activeSubWindow().resizeHandler(self.mdi)
        super(appWindow, self).resizeEvent(event)
        
    def closeEvent(self, event):
        #save alert on window close
        if len(self.activeFiles) and not dialogs.saveEvent(self):
            event.ignore()            
        else:
            event.accept()            
    
    @property
    def activeFiles(self):
        return [i for i in self.mdi.subWindowList() if i.tabCount]
    
if __name__ == '__main__':
    app = ApplicationContext()       # 1. Instantiate ApplicationContext
    test = appWindow()
    test.show()
    exit_code = app.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)
