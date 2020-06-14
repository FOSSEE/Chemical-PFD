from PyQt5.QtCore import Qt, QSize, QRectF, QPoint
from PyQt5.QtGui import QBrush, QPen, QColor
from PyQt5.QtWidgets import QTableWidget, QMenu, QGraphicsRectItem, QInputDialog, QStyledItemDelegate

from collections import defaultdict

class streamTable(QTableWidget):
    
    def __init__(self, int, int_, canvas=None, parent=None):
        super(streamTable, self).__init__(int, int_, parent=parent)
        self.canvas = canvas
        self.borderThickness = defaultdict(lambda: 1)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            point = event.pos()
            col = self.getCol(point.x())
            row = self.getRow(point.y())
            menu = QMenu("Context Menu", self)
            menu.addAction("Change bottom border thickness", lambda x=row: self.changeRowBorder(x))
            menu.addAction("Change right border thickness", lambda x=col: self.changeColBorder(x))
            menu.addAction("Insert Column to right", lambda x=col: self.insertColRight(col))
            menu.addAction("Insert Row to bottom", lambda x=row: self.insertRowBottom(row))
            menu.exec_(self.mapToGlobal(point)+ QPoint(20, 25))
            event.accept()
        return super(streamTable, self).mousePressEvent(event)
    
    def changeRowBorder(self, row):
        newWidth, bool = QInputDialog.getInt(self, "Change Horizontal Border Width", "Enter new Width in pixels", self.borderThickness[row], 0, 10, step=1)
        if bool:
            self.setItemDelegateForRow(row, drawBorderDelegate(self, newWidth, True))
    
    def changeColBorder(self, col):
        newWidth, bool = QInputDialog.getInt(self, "Change Vertical Border Width", "Enter new Width in pixels", self.borderThickness[-col], 0, 10, step=1)
        if bool:
            self.setItemDelegateForColumn(col, drawBorderDelegate(self, newWidth, False))
            
    def getRow(self, point):
        h = self.horizontalHeader().height()
        i = -1
        while (h < point):
            h += self.rowHeight(i)
            i += 1
        return i
    
    def getCol(self, point):
        w = self.verticalHeader().width()
        i = -1
        while (w < point):
            w += self.columnWidth(i)
            i += 1
        return i
    
    def insertRowBottom(self, row):
        self.insertRow(row + 1)
        self.resize(self.sizeHint())
        
    def insertColRight(self, col):
        self.insertColumn(col + 1)
        self.resize(self.sizeHint())
        
    def resizeHandler(self):
        self.resize(self.sizeHint())
        
    def sizeHint(self):
        w = self.verticalHeader().width() + 4
        for i in range(self.columnCount()):
            w += self.columnWidth(i)
        h = self.horizontalHeader().height() + 4
        for i in range(self.rowCount()):
            h += self.rowHeight(i)
        return QSize(w, h)
    
    def rect(self):
        w = self.verticalHeader().width() + 4
        for i in range(self.columnCount()):
            w += self.columnWidth(i)
        h = self.horizontalHeader().height() + 4
        for i in range(self.rowCount()):
            h += self.rowHeight(i)
        return QRectF(0, 0, w, h)
    
    def cellEntered(self, row, column):
        print(row, column)

class drawBorderDelegate(QStyledItemDelegate):
    def __init__(self, parent, width, bool1, bool2 = True):
        super(drawBorderDelegate, self).__init__(parent)
        self.horizontal = bool1
        self.bottom = bool2
        self.width = width
    
    def paint(self, painter, option, index):
        rect = option.rect
        if self.horizontal:
            painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        else:
            painter.drawLine(rect.topRight(), rect.bottomRight())
        painter.setPen(QPen(Qt.black, self.width, Qt.SolidLine))
        super(drawBorderDelegate, self).paint(painter, option, index)

class moveRect(QGraphicsRectItem):
    def __init__(self, *args):
        super(moveRect, self).__init__(*args)
        self.setBrush(QBrush(QColor(0, 0, 0, 120)))