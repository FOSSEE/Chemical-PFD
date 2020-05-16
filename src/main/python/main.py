import pickle
import sys

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QImage, QPainter, QPalette, QPen
from PyQt5.QtWidgets import (QComboBox, QFileDialog, QFormLayout, QVBoxLayout,
                             QHBoxLayout, QLabel, QMainWindow, QMenu,
                             QPushButton, QWidget, QMdiArea, QSplitter, QGraphicsItem)
from PyQt5 import QtWidgets

from utils.canvas import canvas
from utils.fileWindow import fileWindow
from utils.data import ppiList, sheetDimensionList
from utils import dialogs
from utils.toolbar import toolbar

class appWindow(QMainWindow):
    """
    Application entry point, subclasses QMainWindow and implements the main widget,
    sets necessary window behaviour etc.
    """
    def __init__(self, parent=None):
        super(appWindow, self).__init__(parent)
        
        #create the menu bar
        titleMenu = self.menuBar() #fetch reference to current menu bar
        # self.mainWidget.setObjectName("Main Widget")
        
        self.menuFile = titleMenu.addMenu('File') #File Menu
        self.menuFile.addAction("New", self.newProject)
        self.menuFile.addAction("Open", self.openProject)
        self.menuFile.addAction("Save", self.saveProject)
        
        self.menuGenerate = titleMenu.addMenu('Generate') #Generate menu
        self.menuGenerate.addAction("Image", self.saveImage)
        self.menuGenerate.addAction("Report", self.generateReport)
        
        self.mdi = QMdiArea(self) #create area for files to be displayed
        self.mdi.setObjectName('mdi area')
        
        #create toolbar and add the toolbar plus mdi to layout
        self.createToolbar()
        
        #set flags so that window doesnt look weird
        self.mdi.setOption(QMdiArea.DontMaximizeSubWindowOnActivation, True) 
        self.mdi.setTabsClosable(True)
        self.mdi.setTabsMovable(True)
        self.mdi.setDocumentMode(False)
        
        #declare main window layout
        # self.mainWidget.setLayout(mainLayout)
        self.setCentralWidget(self.mdi)
        self.resize(1280, 720) #set collapse dim
        self.mdi.subWindowActivated.connect(self.tabSwitched)
        
                
    def createToolbar(self):
        #place holder for toolbar with fixed width, layout may change
        self.toolbar = toolbar(self)
        self.toolbar.setObjectName("Toolbar")
        # self.addToolBar(Qt.LeftToolBarArea, self.toolbar)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.toolbar)
        self.toolbar.toolbuttonClicked.connect(self.toolButtonClicked)
        self.toolbar.populateToolbar(self.toolbar.toolbarItemList)
        
    def toolButtonClicked(self, object):
        currentDiagram = self.mdi.currentSubWindow().tabber.currentWidget().painter
        if currentDiagram:
            graphic = getattr(QtWidgets, object['object'])(*object['args'])
            graphic.setPen(QPen(Qt.black, 2))
            graphic.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
            currentDiagram.addItem(graphic) 

    def newProject(self):
        #call to create a new file inside mdi area
        project = fileWindow(self.mdi)
        project.setObjectName("New Project")
        self.mdi.addSubWindow(project)
        if not project.tabList: # important when unpickling a file instead
            project.newDiagram() #create a new tab in the new file
        project.resizeHandler()
        project.fileCloseEvent.connect(self.fileClosed) #closed file signal to switch to sub window view
        if self.count > 1: #switch to tab view if needed
            self.mdi.setViewMode(QMdiArea.TabbedView)
        project.show()
                
    def openProject(self):
        #show the open file dialog to open a saved file, then unpickle it.
        name = QFileDialog.getOpenFileNames(self, 'Open File(s)', '', 'Process Flow Diagram (*pfd)')
        if name:
            for files in name[0]:
                with open(files,'rb') as file:
                    project = pickle.load(file)
                    self.mdi.addSubWindow(project)
                    project.show()
                    project.resizeHandler()
                    project.fileCloseEvent.connect(self.fileClosed)                    
        if self.count > 1:
            # self.tabSpace.setVisible(True)
            self.mdi.setViewMode(QMdiArea.TabbedView)
            
    def saveProject(self):
        #pickle all files in mdi area
        for j, i in enumerate(self.activeFiles): #get list of all windows with atleast one tab
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
    
    def tabSwitched(self, window):
        #handle window switched edge case
        if window:
            window.resizeHandler()
                
    def resizeEvent(self, event):
        #overload resize to also handle resize on file windows inside
        for i in self.mdi.subWindowList():
            i.resizeHandler()
        self.toolbar.resize()
        super(appWindow, self).resizeEvent(event)
        
    def closeEvent(self, event):
        #save alert on window close
        if len(self.activeFiles) and not dialogs.saveEvent(self):
            event.ignore()            
        else:
            event.accept()            
    
    def fileClosed(self, index):
        #checks if the file tab menu needs to be removed
        if self.count <= 2 :
            self.mdi.setViewMode(QMdiArea.SubWindowView)
            
    @property
    def activeFiles(self):
        return [i for i in self.mdi.subWindowList() if i.tabCount]
    
    @property
    def count(self):
        return len(self.mdi.subWindowList())
    
    #Key input handler
    def keyPressEvent(self, event):
        #overload key press event for custom keyboard shortcuts
        if event.modifiers() and Qt.ControlModifier:
            if event.key() == Qt.Key_N:
                self.newProject()
                
            elif event.key() == Qt.Key_S:
                self.saveProject()
                
            elif event.key() == Qt.Key_O:
                self.openProject()
                
            elif event.key() == Qt.Key_W:
                self.close()
                
            elif event.key() == Qt.Key_P:
                if Qt.AltModifier:
                    self.saveImage()
                else:
                    self.generateReport()
            
            elif event.key() == Qt.Key_A:
                #todo implement selectAll
                for item in self.mdi.activeSubWindow().tabber.currentWidget().items:
                    item.setSelected(True)
                    
            #todo copy, paste, undo redo
            
            
        elif event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            for item in self.mdi.activeSubWindow().tabber.currentWidget().painter.selectedItems():
                item.setEnabled(False)
                #donot delete, to manage undo redo
        
        event.accept()
        
if __name__ == '__main__':
    app = ApplicationContext()       # 1. Instantiate ApplicationContext
    main = appWindow()
    main.show()
    exit_code = app.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)
