import sys

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QSize, QPoint
from PyQt5.QtGui import QBrush, QColor, QImage, QPainter, QPalette, QPen, QKeySequence
from PyQt5.QtWidgets import (QComboBox, QFileDialog, QFormLayout, QVBoxLayout,
                             QHBoxLayout, QLabel, QMainWindow, QMenu,
                             QPushButton, QWidget, QMdiArea, QSplitter, QGraphicsItem)

from utils.canvas import canvas
from utils.fileWindow import FileWindow
from utils.data import ppiList, sheetDimensionList
from utils import dialogs
from utils.toolbar import toolbar
from utils.app import app, settings, load

import shapes

class appWindow(QMainWindow):
    """
    Application entry point, subclasses QMainWindow and implements the main widget,
    sets necessary window behaviour etc.
    """
    def __init__(self, parent=None):
        super(appWindow, self).__init__(parent)
        
        #create the menu bar
        self.createMenuBar()
        
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
        self.setCentralWidget(self.mdi)
        # self.resize(1280, 720) #set collapse dim
        self.mdi.subWindowActivated.connect(self.tabSwitched)
        self.readSettings()
    
    def createMenuBar(self):
        # Fetches a reference to the menu bar in the main window, and adds actions to it.

        titleMenu = self.menuBar() #fetch reference to current menu bar
        
        self.menuFile = titleMenu.addMenu('File') #File Menu
        newAction = self.menuFile.addAction("New", self.newProject)
        openAction = self.menuFile.addAction("Open", self.openProject)
        saveAction = self.menuFile.addAction("Save", self.saveProject)
        
        newAction.setShortcut(QKeySequence.New)
        openAction.setShortcut(QKeySequence.Open)
        saveAction.setShortcut(QKeySequence.Save)
        
        self.menuEdit = titleMenu.addMenu('Edit')
        undoAction = self.undo = self.menuEdit.addAction("Undo", lambda x=self: x.activeScene.painter.undoAction.trigger())
        redoAction = self.redo = self.menuEdit.addAction("Redo", lambda x=self: x.activeScene.painter.redoAction.trigger())
        
        undoAction.setShortcut(QKeySequence.Undo)
        redoAction.setShortcut(QKeySequence.Redo)
        
        self.menuEdit.addAction("Show Undo Stack", lambda x=self: x.activeScene.painter.createUndoView(self) )
        self.menuEdit.addSeparator()
        self.menuEdit.addAction("Add new symbols", self.addSymbolWindow)
        
        self.menuGenerate = titleMenu.addMenu('Generate') #Generate menu
        imageAction = self.menuGenerate.addAction("Image", self.saveImage)
        reportAction = self.menuGenerate.addAction("Report", self.generateReport)
        
        imageAction.setShortcut(QKeySequence("Ctrl+P"))
        reportAction.setShortcut(QKeySequence("Ctrl+R"))
            
    def createToolbar(self):
        #place holder for toolbar with fixed width, layout may change
        self.toolbar = toolbar(self)
        self.toolbar.setObjectName("Toolbar")
        # self.addToolBar(Qt.LeftToolBarArea, self.toolbar)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.toolbar)
        self.toolbar.toolbuttonClicked.connect(self.toolButtonClicked)
        self.toolbar.populateToolbar()
        
    def toolButtonClicked(self, object):
        # To add the corresponding symbol for the clicked button to active scene.
        if self.mdi.currentSubWindow():
            currentDiagram = self.mdi.currentSubWindow().tabber.currentWidget().painter
            if currentDiagram:
                graphic = getattr(shapes, object['object'])(*map(lambda x: int(x) if x.isdigit() else x, object['args']))
                graphic.setPos(50, 50)
                currentDiagram.addItemPlus(graphic) 
    
    def addSymbolWindow(self):
        # Opens the add symbol window when requested
        from utils.custom import ShapeDialog
        ShapeDialog(self).exec()
        
    def newProject(self):
        #call to create a new file inside mdi area
        project = FileWindow(self.mdi)
        project.setObjectName("New Project")
        self.mdi.addSubWindow(project)
        if not project.tabList: # important when unpickling a file instead
            project.newDiagram() #create a new tab in the new file
        project.fileCloseEvent.connect(self.fileClosed) #closed file signal to switch to sub window view
        if self.count > 1: #switch to tab view if needed
            self.mdi.setViewMode(QMdiArea.TabbedView)
        project.show()
                
    def openProject(self):
        #show the open file dialog to open a saved file, then unpickle it.
        name = QFileDialog.getOpenFileNames(self, 'Open File(s)', '', 'Process Flow Diagram (*pfd)')
        if name:
            for files in name[0]:
                with open(files,'r') as file:
                    projectData = load(file)
                    project = FileWindow(self.mdi)
                    self.mdi.addSubWindow(project)
                    #create blank window and set its state
                    project.__setstate__(projectData)
                    project.resizeHandler()
                    project.fileCloseEvent.connect(self.fileClosed)
                    project.show()
        if self.count > 1:
            # self.tabSpace.setVisible(True)
            self.mdi.setViewMode(QMdiArea.TabbedView)
            
    def saveProject(self):
        #serialize all files in mdi area
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
        if window and window.tabCount:
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
        self.writeSettings()  
    
    def fileClosed(self, index):
        #checks if the file tab menu needs to be removed
        if self.count <= 2 :
            self.mdi.setViewMode(QMdiArea.SubWindowView)
    
    def writeSettings(self):
        # write window state on window close
        settings.beginGroup("MainWindow")
        settings.setValue("maximized", self.isMaximized())
        if not self.isMaximized():
            settings.setValue("size", self.size())
            settings.setValue("pos", self.pos())
        settings.endGroup()
    
    def readSettings(self):
        # read window state when app launches
        settings.beginGroup("MainWindow")
        self.resize(settings.value("size", QSize(1280, 720)))
        self.move(settings.value("pos", QPoint(320, 124)))
        if settings.value("maximized", False, type=bool):
            self.showMaximized()
        settings.endGroup()
      
    #useful one liner properties for getting data
    @property   
    def activeFiles(self):
        return [i for i in self.mdi.subWindowList() if i.tabCount]
    
    @property
    def count(self):
        return len(self.mdi.subWindowList())
    
    @property
    def activeScene(self):
        return self.mdi.currentSubWindow().tabber.currentWidget()

    #Key input handler
    def keyPressEvent(self, event):
        #overload key press event for custom keyboard shortcuts
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_A:
                #todo implement selectAll
                for item in self.mdi.activeSubWindow().tabber.currentWidget().items:
                    item.setSelected(True)
            
            #todo copy, paste, undo redo
            else:
                return
            event.accept()
        elif event.key() == Qt.Key_Q:
            if self.mdi.activeSubWindow() and self.mdi.activeSubWindow().tabber.currentWidget():
                for item in self.mdi.activeSubWindow().tabber.currentWidget().painter.selectedItems():
                    item.rotation -= 1
                    
        elif event.key() == Qt.Key_E:
            if self.mdi.activeSubWindow() and self.mdi.activeSubWindow().tabber.currentWidget():
                for item in self.mdi.activeSubWindow().tabber.currentWidget().painter.selectedItems():
                    item.rotation += 1
                        
if __name__ == '__main__':      # 1. Instantiate ApplicationContext
    main = appWindow()
    main.show()
    exit_code = app.app.exec_()      # 2. Invoke app.app.exec_()
    sys.exit(exit_code)
