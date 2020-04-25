from PyQt5.QtWidgets import QDialog, QPushButton, QFormLayout, QComboBox, QLabel, QMessageBox
from .sizes import sheetDimensionList, ppiList

class paperDims(QDialog):
    def __init__(self, parent=None, size='A4', ppi='72', name='Canvas Size'):
        super(paperDims, self).__init__(parent)
        
        self._canvasSize = size
        self._ppi = ppi
        
        self.setWindowTitle(name+":Canvas Size")
        dialogBoxLayout = QFormLayout(self)
        sizeComboBox = QComboBox()
        sizeComboBox.addItems(sheetDimensionList)
        sizeComboBox.setCurrentIndex(4)
        sizeComboBox.activated[str].connect(self.setCanvasSize)
        sizeLabel = QLabel("Canvas Size")
        sizeLabel.setBuddy(sizeComboBox)
        sizeComboBox.setCurrentIndex(sheetDimensionList.index(self._canvasSize))
        dialogBoxLayout.setWidget(0, QFormLayout.LabelRole, sizeLabel)
        dialogBoxLayout.setWidget(0, QFormLayout.FieldRole, sizeComboBox)
        
        ppiComboBox = QComboBox()
        ppiComboBox.addItems(ppiList)
        ppiComboBox.activated[str].connect(self.setCanvasPPI)
        ppiLabel = QLabel("Canvas ppi")
        ppiLabel.setBuddy(ppiComboBox)
        ppiComboBox.setCurrentIndex(ppiList.index(self._ppi))
        dialogBoxLayout.setWidget(1, QFormLayout.LabelRole, ppiLabel)
        dialogBoxLayout.setWidget(1, QFormLayout.FieldRole, ppiComboBox)
        self.setLayout(dialogBoxLayout)
        self.resize(400,300)
    
    def setCanvasSize(self, size):
        self._canvasSize = size
    
    def setCanvasPPI(self, ppi):
        self._ppi = ppi
        
    def exec_(self):
        super(paperDims, self).exec_()
        return self._canvasSize, self._ppi

def saveEvent(parent = None):
    alert = QMessageBox.question(parent, parent.objectName(), "All unsaved progress will be LOST!",
                                    QMessageBox.StandardButtons(QMessageBox.Save|QMessageBox.Ignore|QMessageBox.Cancel), QMessageBox.Save)
    if alert == QMessageBox.Cancel:
        return False
    else:
        if alert == QMessageBox.Save:
            if not parent.saveProject():
                return False
    return True