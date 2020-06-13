from PyQt5.QtCore import Qt, QSize, QRectF, QPoint
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QTableWidget, QMenu, QGraphicsRectItem

class streamTable(QTableWidget):
    
    def __init__(self, int, int_, canvas=None, parent=None):
        super(streamTable, self).__init__(int, int_, parent=parent)
        self.canvas = canvas
    
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            point = event.pos()
            menu = QMenu("Context Menu", self)
            menu.addAction("Insert Column to right", lambda x=point: self.insertColRight(x.x()))
            menu.addAction("Insert Row to bottom", lambda x=point: self.insertRowBottom(x.y()))
            menu.exec_(self.mapToGlobal(point)+ QPoint(20, 25))
            event.accept()
        return super(streamTable, self).mousePressEvent(event)
    
    # def mouseDoubleClickEvent(self):
    #     return super(streamTable, self).mouseDoubleClickEvent()
    
    def insertRowBottom(self, point):
        h = self.horizontalHeader().height()
        i = 0
        while (h < point):
            h += self.rowHeight(i)
            i += 1
        self.insertRow(i + 1)
        self.resize(self.sizeHint())
        
    def insertColRight(self, point):
        w = self.verticalHeader().width()
        i = 0
        while (w < point):
            w += self.columnWidth(i)
            i += 1
        self.insertColumn(i + 1)
        self.resize(self.sizeHint())
        
    def resizeHandler(self):
        self.resize(self.sizeHint())
        # self.canvas.streamTableRect.setRect(streamTable.rect().adjusted(-10, -10, 10, 10))
        
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

class moveRect(QGraphicsRectItem):
    def __init__(self, *args):
        super(moveRect, self).__init__(*args)
        self.setBrush(QBrush(QColor(0, 0, 0, 120)))