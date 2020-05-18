import random

from PyQt5 import QtCore
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer
from PyQt5.QtWidgets import QLineEdit, QGraphicsItem, QGraphicsEllipseItem, QGraphicsProxyWidget, QGraphicsPathItem, \
    QGraphicsSceneHoverEvent, QGraphicsColorizeEffect
from PyQt5.QtGui import QPen, QColor, QFont, QCursor, QPainterPath, QPainter, QDrag, QBrush, QImage
from PyQt5.QtCore import Qt, QRectF, QPointF, QSizeF, QEvent, QMimeData, QFile, QIODevice, QRect
from PyQt5.QtXml import QDomDocument
from PyQt5.uic.properties import QtGui, QtWidgets
from xml.dom import minidom
import re

from line import Line
from svghandler import SvgHandler


class GripItem(QGraphicsPathItem):
    """
    Extends PyQt5's QGraphicsPathItem to create the general structure of the Grabbable points for resizing shapes.
    Takes two parameters, reference item (On which the grip items are to appear) and the grip index
    """
    def __init__(self, annotation_item, path, parent=None):
        """
        Extends PyQt5's QGraphicsPathItem to create the general structure of the Grabbable points for resizing shapes.
        """
        QGraphicsPathItem.__init__(self, parent)
        self.m_annotation_item = annotation_item
        # self.m_index = index

        self.setPath(path)

        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        # self.setVisible(False)

    # def hoverEnterEvent(self, event):
    #     """
    #     defines shape highlighting on Mouse Over
    #     """
    #     self.setPen(QPen(QColor("black"), 2))
    #     self.setBrush(QColor("red"))
    #     super(GripItem, self).hoverEnterEvent(event)
    #
    # def hoverLeaveEvent(self, event):
    #     """
    #     defines shape highlighting on Mouse Leave
    #     """
    #     self.setPen(QPen(Qt.transparent))
    #     self.setBrush(Qt.transparent)
    #     super(GripItem, self).hoverLeaveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Automatically deselects grip item on mouse release
        """
        self.setSelected(False)
        super(GripItem, self).mouseReleaseEvent(event)

    # def itemChange(self, change, value):
    #     """
    #     Calls movepoint from reference item, with the index of this grip item
    #     """
    #     if change == QGraphicsItem.ItemPositionChange and self.isEnabled():
    #         self.m_annotation_item.movePoint(self.m_index, value)
    #     return super(GripItem, self).itemChange(change, value)


class SizeGripItem(GripItem):
    """
    Extends grip items for vertical and horizontal directions, with hover events and directional changes
    """

    def __init__(self, annotation_item, index, direction=Qt.Horizontal, parent=None):
        self.width = self.height = 0
        if direction is Qt.Horizontal:
            self.height = annotation_item.boundingRect().height()
        else:
            self.width = annotation_item.boundingRect().width()

        path = QPainterPath()
        path.addRect(QRectF(0, 0, self.width, self.height))
        super(SizeGripItem, self).__init__(annotation_item, path=path, parent=parent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setPen(QPen(QColor("black"), -1))
        self.setZValue(2)
        self._direction = direction
        self.m_index = index

    @property
    def direction(self):
        """
        property that returns the current intended resize direction of the grip item object
        """
        return self._direction

    def update_path(self):
        if self._direction is Qt.Horizontal:
            self.height = self.m_annotation_item.boundingRect().height()
        else:
            self.width = self.m_annotation_item.boundingRect().width()
        path = QPainterPath()
        path.addRect(QRectF(0, 0, self.width, self.height))
        self.setPath(path)

    def update_position(self):
        """updates grip items
        """
        self.update_path()
        pos = self.m_annotation_item.mapToScene(self.point(self.m_index))
        x = self.m_annotation_item.boundingRect().x()
        y = self.m_annotation_item.boundingRect().y()
        pos.setX(pos.x() + x)
        pos.setY(pos.y() + y)
        self.setEnabled(False)
        self.setPos(pos)
        self.setEnabled(True)

    def point(self, index):
        """
        yields a list of positions of grip items in a node item
        """
        x = self.m_annotation_item.boundingRect().width()
        y = self.m_annotation_item.boundingRect().height()
        if 0 <= index < 4:
            return [
                QPointF(0, 0),
                QPointF(0, 0),
                QPointF(0, y),
                QPointF(x, 0)
            ][index]

    def hoverEnterEvent(self, event):
        """
        Changes cursor to horizontal resize or vertical resize depending on the direction of the grip item on mouse enter
        """
        self.setPen(QPen(QColor("black"), 2))
        self.setBrush(QColor("red"))
        # self.setVisible(True)
        if self._direction == Qt.Horizontal:
            self.setCursor(QCursor(Qt.SizeHorCursor))
        else:
            self.setCursor(QCursor(Qt.SizeVerCursor))
        super(SizeGripItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """
        reverts cursor to default on mouse leave
        """
        # self.setVisible(False)
        self.setPen(QPen(Qt.transparent))
        self.setBrush(Qt.transparent)
        self.setCursor(QCursor(Qt.ArrowCursor))
        super(SizeGripItem, self).hoverLeaveEvent(event)

    def itemChange(self, change, value):
        """
        Moves position of grip item on resize or reference circle's position change
        """

        if change == QGraphicsItem.ItemPositionChange and self.isEnabled():
            p = QPointF(self.pos())
            if self.direction == Qt.Horizontal:
                p.setX(value.x())
            elif self.direction == Qt.Vertical:
                p.setY(value.y())
            self.m_annotation_item.resize(self.m_index, p)
            return p
        return super(SizeGripItem, self).itemChange(change, value)

    def removeFromCanvas(self):
        if self.scene():
            self.scene().removeItem(self)


class LineGripItem(GripItem):
    circle = QPainterPath()
    circle.addEllipse(QRectF(-10, -10, 20, 20))
    def __init__(self, annotation_item, index, parent=None):
        """
        Extends grip items for connecting lines , with hover events and mouse events
        """
        self.path = LineGripItem.circle
        super(LineGripItem, self).__init__(annotation_item,path=self.path, parent=parent)
        self.m_index = index
        self.connectedLines = []
        self.tempLine = None
        self.previousHoveredItem = None
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        # self.setZValue(2)
        self.setPen(QPen(QColor("black"), -1))
        # self.setBrush(QColor("red"))
        # self.setVisible(False)

    def point(self, index):
        """
        yields a list of positions of grip items in a node item
        """
        radiusOfGripItem = self.boundingRect().width() / 2
        x = self.m_annotation_item.boundingRect().width()
        y = self.m_annotation_item.boundingRect().height()
        if 0 <= index < 4:
            return [
                QPointF(x / 2, 0),
                QPointF(0, y / 2),
                QPointF(x / 2, y),
                QPointF(x, y / 2)
            ][index]

    def update_position(self):
        # print('updating grip item ', self.m_index)
        pos = self.point(self.m_index)
        x = self.m_annotation_item.boundingRect().x()
        y = self.m_annotation_item.boundingRect().y()
        pos.setX(pos.x() + x)
        pos.setY(pos.y() + y)
        self.setEnabled(False)
        self.setPos(pos)
        self.setEnabled(True)
        for line in self.connectedLines:
            line.updateLine()

    def mousePressEvent(self, mouseEvent):
        if mouseEvent.button() != Qt.LeftButton:
            return
        radiusOfGripItem = self.boundingRect().width() / 2
        startPoint = endPoint = self.parentItem().mapToScene(self.pos())

        self.tempLine = Line(startPoint, endPoint)
        self.scene().addItem(self.tempLine)
        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        if self.tempLine:
            endPoint = mouseEvent.scenePos()
            self.tempLine.updateLine(endPoint=endPoint)
        super().mouseMoveEvent(mouseEvent)
        item = self.scene().itemAt(mouseEvent.scenePos().x(), mouseEvent.scenePos().y(),
                                   self.m_annotation_item.transform())
        # print(self.m_annotation_item.transform())

        if self.previousHoveredItem and item != self.previousHoveredItem and \
                item not in self.previousHoveredItem.lineGripItems:
            self.previousHoveredItem.hideGripItem()

        if type(item) == NodeItem:
            self.previousHoveredItem = item
            item.showGripItem()

    def mouseReleaseEvent(self, mouseEvent):
        if self.tempLine:
            item = self.scene().itemAt(mouseEvent.scenePos().x(), mouseEvent.scenePos().y(),
                                       self.transform())
            if type(item) == LineGripItem:
                endPoint = item.parentItem().mapToScene(item.pos())
                self.tempLine.updateLine(endPoint=endPoint)
                self.connectedLines.append(self.tempLine)
                item.connectedLines.append(self.tempLine)
                self.tempLine.setStartGripItem(self)
                self.tempLine.setEndGripItem(item)

            else:
                self.scene().removeItem(self.tempLine)
        super().mouseReleaseEvent(mouseEvent)
        self.tempLine = None
        self.previousHoveredItem = None

    def removeConnectedLines(self):
        for line in self.connectedLines:
            line.removeFromCanvas()

    def show(self):
        self.setPen(QPen(QColor("black"), 2))
        self.setBrush(QColor("red"))

    def hide(self):
        if (self.parentItem().isSelected() or self.isSelected()) is False:
            self.setPen(QPen(Qt.transparent))
            self.setBrush(Qt.transparent)


class NodeItem(QGraphicsSvgItem):

    def __init__(self, unitOpType, parent=None):
        QGraphicsSvgItem.__init__(self, parent)
        self.m_renderer = QSvgRenderer()
        self.type = unitOpType


        self.file = QFile("svg/" + "Boiler" + ".svg")
        if not self.file.open(QIODevice.ReadOnly):
            print("Cannot open the file")
            exit(-1)
        self.svghandler = SvgHandler(self.file)
        self.updateRenderer()
        self.rect = QRectF(0,0,300,400)
        # self.rect=QRectF(0,0,self.m_renderer.defaultSize().width(),self.m_renderer.defaultSize().height())
        # self.rect = self.m_renderer.viewBoxF()
        # self.changeColour("red")
        # self.changeStrokeWidth(4)

        self.setZValue(2)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.setFlags(QGraphicsSvgItem.ItemIsMovable |
                      QGraphicsSvgItem.ItemIsSelectable |
                      QGraphicsSvgItem.ItemSendsGeometryChanges)

        self.lineGripItems = []
        self.sizeGripItems = []
        self.ds=  0.70875001
        self.cs = 0.70875001
        self.dw=self.m_renderer.defaultSize().width()
        self.dh=self.m_renderer.defaultSize().height()
        self.vdw = self.m_renderer.viewBoxF().width()
        self.vdh=self.m_renderer.viewBoxF().height()


    def changeStrokeWidth(self,value):
        self.svghandler.setStrokeWidth(value)
        self.updateRenderer()

    def changeColour(self,value):
        self.svghandler.setColor(value)
        self.updateRenderer()
        """graphics effect can also used to change colour of an svg image
        """
        # self._effect = QGraphicsColorizeEffect()
        # self._effect.setColor(Qt.red)
        # self._effect.setStrength(1)
        # self.setGraphicsEffect(self._effect)

    def updateRenderer(self):
        byteArray = self.svghandler.doc.toByteArray()
        self.m_renderer.load(byteArray)
        self.setSharedRenderer(self.m_renderer)

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        if not self.m_renderer:
            QGraphicsSvgItem.paint(self, painter, option, widget)
        self.m_renderer.render(painter, self.boundingRect())

    def update_rect(self):
        """Update rect of node item
        """
        self.prepareGeometryChange()
        self.update(self.rect)

    def resize(self, i, p):
        """Move grip item with changing rect of node item
        """
        x = self.boundingRect().x()
        y = self.boundingRect().y()
        width = self.boundingRect().width()
        height = self.boundingRect().height()
        p_new = self.sizeGripItems[i].pos()
        self.prepareGeometryChange()

        if i == 0 or i == 1:
            self.rect = QRectF(x + p.x() - p_new.x(), y + p.y() - p_new.y(), width - p.x() + p_new.x(),
                               height - p.y() + p_new.y())

        if i == 2 or i == 3:
            self.rect = QRectF(x, y, width + p.x() - p_new.x(), height + p.y() - p_new.y())

        self.cs = self.ds*(self.boundingRect().width()/self.vdw)
        # self.cs =self.s
        print(self.boundingRect())
        print(self.cs)
        offset = (self.cs-self.ds)
        offset = offset*(self.vdw/self.boundingRect().width())
        # self.m_renderer.setViewBox(QRectF(offset/2.0,0,self.vdw-offset,self.vdh))

        # self.update_rect()
        self.updateSizeGripItem([i])
        self.updateLineGripItem()

    def addGripItem(self):
        """adds grip items
        """
        if self.scene() and not self.lineGripItems:
            for i, (direction) in enumerate(
                    (
                            Qt.Vertical,
                            Qt.Horizontal,
                            Qt.Vertical,
                            Qt.Horizontal,
                    )
            ):
                item = LineGripItem(self, i)
                item.setParentItem(self)
                self.scene().addItem(item)
                self.lineGripItems.append(item)
                item = SizeGripItem(self, i, direction)
                self.scene().addItem(item)
                self.sizeGripItems.append(item)

    def updateLineGripItem(self, index_no_updates=None):
        # index_no_updates = index_no_updates or []
        for item in self.lineGripItems:
            item.update_position()

    def updateSizeGripItem(self, index_no_updates=None):
        """updates grip items
        """
        index_no_updates = index_no_updates or []
        for i, item in zip(range(len(self.sizeGripItems)), self.sizeGripItems):
            if i not in index_no_updates:
                item.update_position()

    def itemChange(self, change, value):
        """Overloads and extends QGraphicsSvgItem to also update gripitem
        """
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.updateLineGripItem()
            self.updateSizeGripItem()
            return
        if change == QGraphicsItem.ItemSceneHasChanged:
            self.addGripItem()
            self.updateLineGripItem()
            self.updateSizeGripItem()
            return
        return super(NodeItem, self).itemChange(change, value)

    def addOnCanvas(self, scene):
        """This function is used to add Node Item on canvas
        :return:
        """
        scene.addItem(self)

    def removeFromCanvas(self):
        """This function is used to remove item from canvas
        :return:
        """
        for item in self.lineGripItems:
            item.removeConnectedLines()
        for item in self.sizeGripItems:
            item.removeFromCanvas()
        self.scene().removeItem(self)

    def hoverEnterEvent(self, event):
        """defines shape highlighting on Mouse Over
        """
        self.showGripItem()
        super(NodeItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """defines shape highlighting on Mouse Leave
        """
        # if self.isSelected() is False:
        self.hideGripItem()
        super(NodeItem, self).hoverLeaveEvent(event)

    def showGripItem(self):
        for item in self.lineGripItems:
            item.setPen(QPen(QColor("black"), 2))
            item.setBrush(QColor("red"))
        for item in self.sizeGripItems:
            item.setPen(QPen(QColor("black"), 2))
            # item.setBrush(QColor("red"))

    def hideGripItem(self):
        for item in self.lineGripItems:
            if item.isSelected() is False:
                item.setPen(QPen(Qt.transparent))
                item.setBrush(Qt.transparent)
        for item in self.sizeGripItems:
            item.setPen(QPen(Qt.transparent))
            item.setBrush(Qt.transparent)

