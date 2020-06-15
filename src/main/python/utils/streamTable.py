from PyQt5.QtCore import Qt, QSize, QRect, QPoint, QAbstractTableModel, pyqtSignal, QModelIndex
from PyQt5.QtGui import QBrush, QPen, QColor
from PyQt5.QtWidgets import QTableView, QMenu, QGraphicsRectItem, QInputDialog, QStyledItemDelegate

from collections import defaultdict

class streamTableModel(QAbstractTableModel):
    updateEvent = pyqtSignal()
    
    def __init__(self, parent, list, header, *args):
        super(streamTableModel, self).__init__(parent, *args)
        self.list = list
        self.header = header
        
    def rowCount(self, parent=None):
        return len(self.list)
    
    def columnCount(self, parent=None):
        return len(self.list[0])
    
    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        return self.list[index.row()][index.column()]
    
    def setData(self, index, value, role):
        if not index.isValid():
            return False
        elif role != Qt.EditRole:
            return False
        self.list[index.row()][index.column()] = value
        return True 
    
    def insertColumn(self, int):
        self.beginInsertColumns(QModelIndex(), int, int)
        for item in self.list:
            item.insert(int, 0)
        self.header.insert(int, "newVal")
        self.endInsertColumns()
        self.updateEvent.emit()
    
    def insertRow(self, int=None, name="Name"):
        int = int if int else self.rowCount()+1
        self.beginInsertRows(QModelIndex(), int, int)
        self.list.insert(int, [name] + [0 for _ in range(self.columnCount()-1)])
        self.endInsertRows()
        self.updateEvent.emit()
        
    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None
    
    def flags(self, index):
        return (super(streamTableModel, self).flags(index) | Qt.ItemIsEditable)
        
class streamTable(QTableView):
    
    def __init__(self, itemLabels=[], canvas=None, parent=None):
        super(streamTable, self).__init__(parent=parent)
        self.canvas = canvas
        self.items = itemLabels
        list = []
        for i, item in enumerate(itemLabels):
            list.append([item.toPlainText()]+[0 for _ in range(5)])
        header = ["name", "val1", "val2", "val3", "val4", "val5"]
        self.model = streamTableModel(self, list, header)
        self.setShowGrid(False)
        self.verticalHeader().hide()
        self.setModel(self.model)
        self.borderThickness = defaultdict(lambda: 1)
        self.model.updateEvent.connect(self.refresh)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            point = event.pos()
            # col = self.getCol(point.x())
            index = self.indexAt(point)
            menu = QMenu("Context Menu", self)
            menu.addAction("Change bottom border thickness", lambda x=index.row(): self.changeRowBorder(x))
            menu.addAction("Change right border thickness", lambda x=index.column(): self.changeColBorder(x))
            menu.addAction("Insert Column to right", lambda x=index.column(): self.insertColRight(x))
            menu.addAction("Insert Row to bottom", lambda x=index.row(): self.insertRowBottom(x))
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
    
    def insertRowBottom(self, row):
        self.model.insertRow(row + 1)
        
    def insertColRight(self, col):
        self.model.insertColumn(col + 1)
    
    def refresh(self):
        self.resizeHandler()
        
    def resizeHandler(self):
        self.resize(self.sizeHint())
        
    def sizeHint(self):
        return self.rect().size()
    
    def rect(self):
        w = self.verticalHeader().width() + 4
        for i in range(self.model.columnCount()):
            w += self.columnWidth(i)
        h = self.horizontalHeader().height() + 4
        for i in range(self.model.rowCount()):
            h += self.rowHeight(i)
        return QRect(0, 0, w, h)
    
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
        super(moveRect, self).__init__(-10, -10, 10, 10)
        self.setBrush(QBrush(QColor(0, 0, 0, 120)))