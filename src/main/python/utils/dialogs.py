from PyQt5.QtWidgets import QDialog, QPushButton, QFormLayout, QComboBox, QLabel, QMessageBox
from .sizes import sheetDimensionList, ppiList

class paperDims(QDialog):
    """
    Utility dialog box to adjust the current canvas's dimensions, might return just dimensions later
    so that sizes do not need to be imported in every other module. 
    """
    def __init__(self, parent=None, size='A4', ppi='72', name='Canvas Size'):
        super(paperDims, self).__init__(parent)
        
        #store initial values to show currently set value, also updated when changed. these are returned at EOL
        self._canvasSize = size
        self._ppi = ppi
        
        self.setWindowTitle(name+" :Canvas Size") #Set Window Title
        #init layout
        dialogBoxLayout = QFormLayout(self)
        
        sizeComboBox = QComboBox() #combo box for paper sizes
        sizeComboBox.addItems(sheetDimensionList)
        sizeComboBox.setCurrentIndex(4)
        sizeComboBox.activated[str].connect(self.setCanvasSize)
        sizeLabel = QLabel("Canvas Size")
        sizeLabel.setBuddy(sizeComboBox) # label for the above combo box
        sizeComboBox.setCurrentIndex(sheetDimensionList.index(self._canvasSize)) #set index to current value of canvas
        dialogBoxLayout.setWidget(0, QFormLayout.LabelRole, sizeLabel)
        dialogBoxLayout.setWidget(0, QFormLayout.FieldRole, sizeComboBox)
        
        ppiComboBox = QComboBox() #combo box for ppis
        ppiComboBox.addItems(ppiList)
        ppiComboBox.activated[str].connect(self.setCanvasPPI)
        ppiLabel = QLabel("Canvas ppi")
        ppiLabel.setBuddy(ppiComboBox) # label for the above combo box
        ppiComboBox.setCurrentIndex(ppiList.index(self._ppi)) #set index to current value of canvas
        dialogBoxLayout.setWidget(1, QFormLayout.LabelRole, ppiLabel)
        dialogBoxLayout.setWidget(1, QFormLayout.FieldRole, ppiComboBox)
        self.setLayout(dialogBoxLayout)
        self.resize(300,100) #resize to a certain size
        
        #todo add ok or cancel buttons
    
    def setCanvasSize(self, size):
        #for standard combo box behaviour
        self._canvasSize = size
    
    def setCanvasPPI(self, ppi):
        #for standard combo box behaviour        
        self._ppi = ppi
        
    def exec_(self):
        #overload exec_ to add return values and delete itself(currently being tested)
        super(paperDims, self).exec_()
        # self.deleteLater()
        return self._canvasSize, self._ppi

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