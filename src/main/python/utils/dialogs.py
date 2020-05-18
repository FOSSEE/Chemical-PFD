from PyQt5.QtWidgets import QDialog, QPushButton, QFormLayout, QComboBox, QLabel, QMessageBox, QDialogButtonBox
from .data import sheetDimensionList, ppiList

class paperDims(QDialog):
    """
    Utility dialog box to adjust the current canvas's dimensions, might return just dimensions later
    so that sizes do not need to be imported in every other module. 
    """
    def __init__(self, parent=None, size='A4', ppi='72', name='Canvas Size'):
        super(paperDims, self).__init__(parent)
        
        #store initial values to show currently set value, also updated when changed. these are returned at EOL
        self.returnCanvasSize = size
        self.returnCanvasPPI = ppi
        
        self.setWindowTitle(name+" :Canvas Size") #Set Window Title
        #init layout
        dialogBoxLayout = QFormLayout(self)
        
        sizeComboBox = QComboBox() #combo box for paper sizes
        sizeComboBox.addItems(sheetDimensionList)
        sizeComboBox.setCurrentIndex(4)
        sizeComboBox.activated[str].connect(lambda size: setattr(self, "returnCanvasSize", size))
        sizeLabel = QLabel("Canvas Size")
        sizeLabel.setBuddy(sizeComboBox) # label for the above combo box
        sizeComboBox.setCurrentIndex(sheetDimensionList.index(self.returnCanvasSize)) #set index to current value of canvas
        dialogBoxLayout.setWidget(0, QFormLayout.LabelRole, sizeLabel)
        dialogBoxLayout.setWidget(0, QFormLayout.FieldRole, sizeComboBox)
        
        ppiComboBox = QComboBox() #combo box for ppis
        ppiComboBox.addItems(ppiList)
        ppiComboBox.activated[str].connect(lambda ppi: setattr(self, "returnCanvasPPI", ppi))
        ppiLabel = QLabel("Canvas ppi")
        ppiLabel.setBuddy(ppiComboBox) # label for the above combo box
        ppiComboBox.setCurrentIndex(ppiList.index(self.returnCanvasPPI)) #set index to current value of canvas
        dialogBoxLayout.setWidget(1, QFormLayout.LabelRole, ppiLabel)
        dialogBoxLayout.setWidget(1, QFormLayout.FieldRole, ppiComboBox)
        
        # add ok and cancel buttons
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        
        dialogBoxLayout.addWidget(buttonBox)
        self.setLayout(dialogBoxLayout)
        self.resize(300,100) #resize to a certain size
        
    def exec_(self):
        #overload exec_ to add return values and delete itself(currently being tested)
        super(paperDims, self).exec_()
        self.deleteLater() #remove from memory
        #if ok was pressed return value else return None
        return (self.returnCanvasSize, self.returnCanvasPPI) if self.result() else None

class sideViewSwitchDialog(QDialog):
    """
    Custom dialog box to show, all available tabs to set the side view to.
    Also has accept reject events. Structure is similar to paperDims dialog box.
    """
    def __init__(self, parent=None, tabList = None, initial = None):
        super(sideViewSwitchDialog, self).__init__(parent=parent)
        self.tabList = tabList
        self.returnVal = initial
        self.initial = initial
        
        dialogBoxLayout = QFormLayout(self)
        tabListComboBox = QComboBox()
        tabListComboBox.addItems(self.tabList)
        tabListComboBox.activated[str].connect(lambda x: setattr(self, 'returnVal', self.tabList.index(x)))
        tabLabel = QLabel("Change Side View")
        tabLabel.setBuddy(tabListComboBox) # label for the above combo box
        tabListComboBox.setCurrentIndex(self.returnVal)
        dialogBoxLayout.setWidget(1, QFormLayout.LabelRole, tabLabel)
        dialogBoxLayout.setWidget(1, QFormLayout.FieldRole, tabListComboBox)
        
        # add ok and cancel buttons
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        
        dialogBoxLayout.addWidget(buttonBox)
        self.setLayout(dialogBoxLayout)
        self.resize(300,100) #resize to a certain size
        
    def exec_(self):
        #overload exec_ to add return values and delete itself(currently being tested)
        super(sideViewSwitchDialog, self).exec_()
        self.deleteLater() #remove from memory
        #if ok was pressed return value else return None
        return self.returnVal if self.result() else self.initial

def saveEvent(parent = None):
    #utility function to generate a Qt alert window requesting the user to save the file, returns user intention on window close
    alert = QMessageBox.question(parent, parent.objectName(), "All unsaved progress will be LOST!",
                                    QMessageBox.StandardButtons(QMessageBox.Save|QMessageBox.Ignore|QMessageBox.Cancel), QMessageBox.Save)
    if alert == QMessageBox.Cancel:
        return False
    else:
        if alert == QMessageBox.Save:
            if not parent.saveProject(): #the parent's saveProject method is called which returns false if saving was cancelled by the user
                return False
    return True