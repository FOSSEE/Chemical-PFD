from PyQt5.QtGui import QFont, QPen, QPainterPath, QPolygon, QBrush
from PyQt5.QtWidgets import QGraphicsLineItem, QLineEdit, QGraphicsProxyWidget, QGraphicsItem
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.uic.properties import QtCore


class Line(QGraphicsItem):
    def __init__(self, startPoint, endPoint, **args):
        QGraphicsItem.__init__(self, **args)
        self.startPoint = startPoint
        self.endPoint = endPoint
        self.startGripItem = None
        self.endGripItem = None
        self._selected = False

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        # self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

    def setStartGripItem(self, item):
        self.startGripItem = item

    def setEndGripItem(self, item):
        self.endGripItem = item

    def shape(self):
        x0, y0 = self.startPoint.x(), self.startPoint.y()
        x1, y1 = self.endPoint.x(), self.endPoint.y()
        path = QPainterPath(QPointF(x0, y0))
        path.lineTo((x0 + x1) / 2, y0)
        path.moveTo((x0 + x1) / 2, y0)
        path.lineTo((x0 + x1) / 2, y1)
        path.moveTo((x0 + x1) / 2, y1)
        path.lineTo(x1, y1)
        return path

    def boundingRect(self):
        x0, y0 = self.startPoint.x(), self.startPoint.y()
        x1, y1 = self.endPoint.x(), self.endPoint.y()
        return QRectF(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))

    def paint(self, painter, style, widget=None):
        # x0, y0 = self.startPoint.x(), self.startPoint.y()
        # x1, y1 = self.endPoint.x(), self.endPoint.y()
        # painter.drawLine(x0, y0, (x0 + x1) / 2, y0)
        # painter.drawLine((x0 + x1) / 2, y0, (x0 + x1) / 2, y1)
        # painter.drawLine((x0 + x1) / 2, y1, x1, y1)
        painter.drawPath(self.shape())

        if self.isSelected():
            self.showGripItem()
            self._selected= True
            pen = QPen(QBrush(Qt.red), 5)
            painter.setPen(pen)
            painter.drawPath(self.shape())
        elif self._selected:
            self.hideGripItem()
            self._selected = False

    def updateLine(self, startPoint=None, endPoint=None):

        """This function is used to update connecting line when it add on
           canvas and when it's grip item  moves
        :return:
        """
        self.prepareGeometryChange()
        if self.startGripItem and self.endGripItem:
            item = self.startGripItem
            self.startPoint = item.parentItem().mapToScene(item.pos())
            item = self.endGripItem
            self.endPoint = item.parentItem().mapToScene(item.pos())
        if startPoint:
            self.startPoint = startPoint
        if endPoint:
            self.endPoint = endPoint

        self.update(self.boundingRect())

    def removeFromCanvas(self):
        """This function is used to remove connecting line from canvas
        :return:
        """
        if self.scene():
            self.scene().removeItem(self)

    def mousePressEvent(self, event):
        print('line clicked', self)
        super(Line, self).mousePressEvent(event)

    def showGripItem(self):
        if self.startGripItem: self.startGripItem.show()
        if self.endGripItem: self.endGripItem.show()
        # if self.startGripItem: self.startGripItem.setVisible(True)
        # if self.endGripItem: self.endGripItem.setVisible(True)

    def hideGripItem(self):
        if self.startGripItem : self.startGripItem.hide()
        if self.endGripItem: self.endGripItem.hide()
        # if self.startGripItem: self.startGripItem.setVisible(False)
        # if self.endGripItem: self.endGripItem.setVisible(False)


