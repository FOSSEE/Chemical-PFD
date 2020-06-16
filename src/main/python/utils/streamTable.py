from PyQt5.QtCore import Qt, QSize, QRect, QPoint, QAbstractTableModel, pyqtSignal, QModelIndex
from PyQt5.QtGui import QBrush, QPen, QColor, QCursor
from PyQt5.QtWidgets import QTableView, QMenu, QGraphicsRectItem, QInputDialog, QStyledItemDelegate

from collections import defaultdict

class streamTableModel(QAbstractTableModel):
    updateEvent = pyqtSignal()
    
    def __init__(self, parent, list, header, *args):
        super(streamTableModel, self).__init__(parent, *args)
        self.list = list
        self.header = header
        
    def columnCount(self, parent=None):
        return len(self.list)
    
    def rowCount(self, parent=None):
        return len(self.header)
    
    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        if index.row() == 0:
            return self.list[index.column()].toPlainText()
        else:
            return self.list[index.column()].values[self.header[index.row()]]
    
    def setData(self, index, value, role):
        if not index.isValid():
            return False
        elif role != Qt.EditRole:
            return False
        if index.row() == 0:
            self.list[index.column()].setPlainText(value)
        else:
            self.list[index.column()].values[self.header[index.row()]] = value
        return True 
    
    def insertColumn(self, int=None, item=None):
        int = int if int else self.rowCount()+1
        self.beginInsertColumns(QModelIndex(), int, int)
        self.list.insert(int, item)
        self.endInsertColumns()
        self.updateEvent.emit()
    
    def insertRow(self, int=None, name="newVal"):
        self.beginInsertRows(QModelIndex(), int, int)
        self.header.insert(int, name)
        self.endInsertRows()
        self.updateEvent.emit()
        
    def headerData(self, col, orientation, role):
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return self.header[col]
        return None
    
    def flags(self, index):
        return (super(streamTableModel, self).flags(index) | Qt.ItemIsEditable)
        
class streamTable(QTableView):
    
    def __init__(self, itemLabels=[], canvas=None, parent=None):
        super(streamTable, self).__init__(parent=parent)
        self.canvas = canvas
        for i in itemLabels:
            i.nameChanged.connect(self.repaint)
        header = ["name", "val1", "val2", "val3", "val4", "val5"]
        self.model = streamTableModel(self, itemLabels, header)
        self.setShowGrid(False)
        self.horizontalHeader().hide()
        self.setModel(self.model)
        self.borderThickness = defaultdict(lambda: False)
        self.model.updateEvent.connect(self.resizeHandler)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            point = event.pos()
            # col = self.getCol(point.x())
            index = self.indexAt(point)
            menu = QMenu("Context Menu", self)
            menu.addAction("Change bottom border thickness", lambda x=index.row(): self.changeRowBorder(x))
            menu.addAction("Insert Row to bottom", lambda x=index.row(): self.insertRowBottom(x))
            menu.exec_(self.mapToGlobal(point)+ QPoint(20, 25))
            event.accept()
        return super(streamTable, self).mousePressEvent(event)
    
    # def mouseDoubleClickEvent(self, event):
    #     pos = event.pos()
    #     if pos.x() < self.verticalHeader().width():
    #         index = self.rowAt(pos.y())
    #         newName, bool = QInputDialog.getText(self, "Change Property Name", "Enter new name",
    #                                    text = self.model.header[index])
    #         if bool:
    #             for i in self.model.list:
    #                 i.values[newName] = i.values.pop(self.model.header[index])
    #             self.repaint()
    #     return super().mouseDoubleClickEvent(event)
    
    def changeRowBorder(self, row):
        if self.borderThickness[row]:
            self.borderThickness[row] = False
            self.setItemDelegateForRow(row, QStyledItemDelegate(self))
        else:
            self.borderThickness[row] = True
            self.setItemDelegateForRow(row, drawBorderDelegate(self))
    
    # def changeColBorder(self, col):
    #     newWidth, bool = QInputDialog.getInt(self, "Change Vertical Border Width", "Enter new Width in pixels", self.borderThickness[-col], 0, 10, step=1)
    #     if bool:
    #         self.setItemDelegateForColumn(col, drawBorderDelegate(self, newWidth, False))

    def insertRowBottom(self, row):
        name, bool = QInputDialog.getText(self, "New Property", "Enter name", 
                                             text = "newVal")
        if bool:
            self.model.insertRow(row + 1, name)
            self.repaint()
        
    def resizeHandler(self):
        self.resize(self.sizeHint())
        
    def sizeHint(self):
        return self.rect().size()
    
    def rect(self):
        w = self.verticalHeader().width() + 4
        for i in range(self.model.columnCount()):
            w += self.columnWidth(i)
        h = 4
        for i in range(self.model.rowCount()):
            h += self.rowHeight(i)
        return QRect(0, 0, w, h)

class drawBorderDelegate(QStyledItemDelegate):
    
    # def __init__(self, parent):
    #     super(drawBorderDelegate, self).__init__(parent)
    
    def paint(self, painter, option, index):
        rect = option.rect
        # if self.horizontal:
            # painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        # else:
        #     painter.drawLine(rect.topRight(), rect.bottomRight())
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        super(drawBorderDelegate, self).paint(painter, option, index)

class moveRect(QGraphicsRectItem):
    
    def __init__(self, sideLength = 15, *args):
        super(moveRect, self).__init__(-sideLength, -sideLength, sideLength, sideLength)
        self.setBrush(Qt.transparent)
        self.setPen(QPen(Qt.transparent))
        self.setCursor(QCursor(Qt.SizeAllCursor))
        self.setAcceptHoverEvents(True)
        
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(0, 0, 0, 120)))
        return super(moveRect, self).hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(0, 0, 0, 0)))
        return super(moveRect, self).hoverLeaveEvent(event)