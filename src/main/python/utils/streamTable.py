from PyQt5.QtCore import Qt, QSize, QRect, QPoint, QAbstractTableModel, pyqtSignal, QModelIndex
from PyQt5.QtGui import QBrush, QPen, QColor, QCursor
from PyQt5.QtWidgets import QTableView, QMenu, QGraphicsRectItem, QInputDialog, QStyledItemDelegate, QHeaderView

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
        if role == Qt.TextAlignmentRole:
            return Qt.AlignHCenter
        if role == Qt.BackgroundColorRole:
            return Qt.white
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
    
    def deleteRow(self, row):
        self.beginRemoveRows(QModelIndex(), row, row)
        valName = self.header.pop(row)
        self.endRemoveRows()
        for i in self.list:
            i.values.pop(valName)
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
        header = verticalHeader(Qt.Vertical, self)
        self.setVerticalHeader(header)
        header.labelChangeRequested.connect(self.labelChange)
        
        self.setModel(self.model)
        self.borderThickness = defaultdict(lambda: False)
        self.model.updateEvent.connect(self.resizeHandler)
        
        self.setItemDelegateForRow(0, drawBorderDelegate(self))
        self.borderThickness[0] = True
        
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            point = event.pos()
            # col = self.getCol(point.x())
            index = self.indexAt(point)
            menu = QMenu("Context Menu", self)
            menu.addAction("Toggle bottom border thickness", lambda x=index.row(): self.changeRowBorder(x))
            menu.addAction("Insert Row to bottom", lambda x=index.row(): self.insertRowBottom(x))
            menu.addAction("Delete row", lambda x=index.row(): self.model.deleteRow(x))
            menu.exec_(self.mapToGlobal(point)+ QPoint(20, 25))
            event.accept()
        return super(streamTable, self).mousePressEvent(event)
    
    def changeRowBorder(self, row):
        if self.borderThickness[row]:
            self.borderThickness.pop(row)
            self.setItemDelegateForRow(row, QStyledItemDelegate(self))
        else:
            self.borderThickness[row] = True
            self.setItemDelegateForRow(row, drawBorderDelegate(self))
        self.verticalHeader().repaint()
    
    def labelChange(self, index):
        newName, bool = QInputDialog.getText(self, "Change Property Name", "Enter new name", 
                                             text = self.model.header[index])
        if bool:
            for i in self.model.list:
                i.values[newName] = i.values.pop(self.model.header[index])
            self.model.header[index] = newName
            self.repaint()

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
        h = 0
        for i in range(self.model.rowCount()):
            h += self.rowHeight(i)
        return QRect(0, 0, w, h)
    
    def __getstate__(self):
        return {
            "borderThickness": self.borderThickness,
            "header": self.model.header
        }
    
    def __setstate__(self, dict):
        for key, value in dict['borderThickness'].items():
            self.borderThickness[key] = value
        self.model.header = dict['header']
        self.repaint()

class drawBorderDelegate(QStyledItemDelegate):
    
    # def __init__(self, parent):
    #     super(drawBorderDelegate, self).__init__(parent)
    
    def paint(self, painter, option, index):
        rect = option.rect
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
    
class verticalHeader(QHeaderView):
    labelChangeRequested = pyqtSignal(int)
    
    def mouseDoubleClickEvent(self, event):
        index = self.logicalIndexAt(event.pos())
        self.labelChangeRequested.emit(index)
        return super().mouseDoubleClickEvent(event)
    
    def paintSection(self, painter, option, index):
        painter.save()
        super(verticalHeader, self).paintSection(painter, option, index)
        painter.restore()
        if self.parentWidget().borderThickness[index]:
            rect = option
            painter.drawLine(rect.bottomLeft(), rect.bottomRight())  
            painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))       