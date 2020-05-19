from PyQt5 import QtCore, QtWidgets
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer
from PyQt5.QtWidgets import QLineEdit, QGraphicsItem, QGraphicsEllipseItem, QGraphicsProxyWidget, QGraphicsPathItem, \
    QGraphicsSceneHoverEvent, QGraphicsColorizeEffect
from PyQt5.QtGui import QPen, QColor, QFont, QCursor, QPainterPath, QPainter, QDrag, QBrush, QImage
from PyQt5.QtCore import Qt, QRectF, QPointF, QSizeF, QEvent, QMimeData, QFile, QIODevice, QRect

from line import Line


class GripItem(QGraphicsPathItem):
    """
    Extends QGraphicsPathItem to create the structure of the Grabbable points for resizing shapes and connecting lines.
    Takes two parameters, reference item (On which the grip items are to appear) and the path of the item
    """

    def __init__(self, annotation_item, path, parent=None):
        """
        Extends PyQt5's QGraphicsPathItem to create the general structure of the Grabbable points for resizing shapes.
        """
        QGraphicsPathItem.__init__(self, parent)
        self.m_annotation_item = annotation_item
        # set path of item
        self.setPath(path)
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))

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

    def updatePath(self):
        """updates path of size grip item
        """
        if self._direction is Qt.Horizontal:
            self.height = self.m_annotation_item.boundingRect().height()
        else:
            self.width = self.m_annotation_item.boundingRect().width()
        path = QPainterPath()
        path.addRect(QRectF(0, 0, self.width, self.height))
        self.setPath(path)

    def updatePosition(self):
        """updates position of grip items
        """
        self.updatePath()
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
        # self.setPen(QPen(QColor("black"), 2))
        # self.setBrush(QColor("red"))
        if self._direction == Qt.Horizontal:
            self.setCursor(QCursor(Qt.SizeHorCursor))
        else:
            self.setCursor(QCursor(Qt.SizeVerCursor))
        super(SizeGripItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """
        reverts cursor to default on mouse leave
        """
        # self.setPen(QPen(Qt.transparent))
        # self.setBrush(Qt.transparent)
        self.setCursor(QCursor(Qt.ArrowCursor))
        super(SizeGripItem, self).hoverLeaveEvent(event)

    def itemChange(self, change, value):
        """
        Moves position of grip item on resize
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
        # used to remove grip item from scene
        if self.scene():
            self.scene().removeItem(self)


class LineGripItem(GripItem):
    """Extends grip items for connecting lines , with hover events and mouse events
    """
    circle = QPainterPath()
    circle.addEllipse(QRectF(-10, -10, 20, 20))

    def __init__(self, annotation_item, index, location, parent=None):
        self.path = LineGripItem.circle
        super(LineGripItem, self).__init__(annotation_item, path=self.path, parent=parent)
        self.m_index = index
        self.m_location = location
        self.connectedLines = []
        # stores current line which is in process
        self.tempLine = None
        # keep previous hovered item when line drawing in process
        self.previousHoveredItem = None
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setPen(QPen(QColor("black"), -1))

    def point(self, index):
        """
        yields a list of positions of grip items in a node item
        """
        x = self.m_annotation_item.boundingRect().width()
        y = self.m_annotation_item.boundingRect().height()
        if 0 <= index < 4:
            return [
                QPointF(x / 2, 0),
                QPointF(0, y / 2),
                QPointF(x / 2, y),
                QPointF(x, y / 2)
            ][index]

    def updatePosition(self):
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
        """Handle all mouse press for this item
        """
        if mouseEvent.button() != Qt.LeftButton:
            return
        # initialize a line and add on scene
        startPoint = endPoint = self.parentItem().mapToScene(self.pos())
        self.tempLine = Line(startPoint, endPoint)
        self.tempLine.setStartGripItem(self)
        self.scene().addItem(self.tempLine)
        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """Handle all mouse move for this item
        """
        #if line get started then update it's end point
        if self.tempLine:
            endPoint = mouseEvent.scenePos()
            self.tempLine.updateLine(endPoint=endPoint)

        item = self.scene().itemAt(mouseEvent.scenePos().x(), mouseEvent.scenePos().y(),
                                   self.m_annotation_item.transform())

        if self.previousHoveredItem and item != self.previousHoveredItem and \
                item not in self.previousHoveredItem.lineGripItems:
            self.previousHoveredItem.hideGripItem()
        super().mouseMoveEvent(mouseEvent)

        if type(item) == NodeItem:
            self.previousHoveredItem = item
            item.showGripItem()

    def mouseReleaseEvent(self, mouseEvent):
        """Handle all mouse release for this item"""
        super().mouseReleaseEvent(mouseEvent)
        # set final position of line
        if self.tempLine:
            item = self.scene().itemAt(mouseEvent.scenePos().x(), mouseEvent.scenePos().y(),
                                       self.transform())

            if type(item) == LineGripItem and item != self:
                self.tempLine.setEndGripItem(item)
                endPoint = item.parentItem().mapToScene(item.pos())
                self.tempLine.updateLine(endPoint=endPoint)
                self.connectedLines.append(self.tempLine)
                item.connectedLines.append(self.tempLine)



            elif self.tempLine and self.scene():
                self.scene().removeItem(self.tempLine)
        self.tempLine = None
        self.previousHoveredItem = None

    def removeConnectedLines(self):
        """removes all connected line to grip"""
        for line in self.connectedLines:
            line.removeFromCanvas()

    def show(self):
        """ shows line grip item
        """
        self.setPen(QPen(QColor("black"), 2))
        self.setBrush(QColor("red"))

    def hide(self):
        """ hides line grip item
        """
        if (self.parentItem().isSelected() or self.isSelected()) is False:
            self.setPen(QPen(Qt.transparent))
            self.setBrush(Qt.transparent)


class NodeItem(QGraphicsSvgItem):
    """
        Extends PyQt5's QGraphicsSvgItem to create the basic structure of shapes with given unit operation type
    """

    def __init__(self, unitOperationType, parent=None):
        QGraphicsSvgItem.__init__(self, parent)
        self.m_type = unitOperationType
        self.m_renderer = QSvgRenderer("svg/" + unitOperationType + ".svg")
        self.setSharedRenderer(self.m_renderer)
        # set initial size of item
        self.width = 100
        self.height = 150
        self.rect = QRectF(-self.width / 2, -self.height / 2, self.width, self.height)
        # set graphical settings for this item
        self.setFlags(QGraphicsSvgItem.ItemIsMovable |
                      QGraphicsSvgItem.ItemIsSelectable |
                      QGraphicsSvgItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setZValue(2)
        # grip items connected to this item
        self.lineGripItems = []
        self.sizeGripItems = []

    def boundingRect(self):
        """Overrides QGraphicsSvgItem's boundingRect() virtual public function and
        returns a valid bounding
        """
        return self.rect

    def paint(self, painter, option, widget):
        """
            Paints the contents of an item in local coordinates.
            :param painter: QPainter instance
            :param option: QStyleOptionGraphicsItem instance
            :param widget: QWidget instance
        """
        if not self.m_renderer:
            QGraphicsSvgItem.paint(self, painter, option, widget)
        self.m_renderer.render(painter, self.boundingRect())
        if self.isSelected():
            self.showGripItem()
        else:
            self.hideGripItem()

    def resize(self, index, p):
        """Move grip item with changing rect of node item
        """
        x = self.boundingRect().x()
        y = self.boundingRect().y()
        width = self.boundingRect().width()
        height = self.boundingRect().height()
        pos_new = self.sizeGripItems[index].pos()
        self.prepareGeometryChange()

        if index == 0 or index == 1:
            self.rect = QRectF(x + p.x() - pos_new.x(), y + p.y() - pos_new.y(), width - p.x() + pos_new.x(),
                               height - p.y() + pos_new.y())

        if index == 2 or index == 3:
            self.rect = QRectF(x, y, width + p.x() - pos_new.x(), height + p.y() - pos_new.y())

        self.updateSizeGripItem([index])
        self.updateLineGripItem()

    def addGripItem(self):
        """adds grip items
        """
        if self.scene():
            # add grip items for connecting lines
            for i, (location) in enumerate(
                    (
                            "top",
                            "left",
                            "bottom",
                            "right"
                    )
            ):
                item = LineGripItem(self, i, location, parent=self)
                self.scene().addItem(item)
                self.lineGripItems.append(item)
            # add grip for resize it
            for i, (direction) in enumerate(
                    (
                            Qt.Vertical,
                            Qt.Horizontal,
                            Qt.Vertical,
                            Qt.Horizontal,
                    )
            ):
                item = SizeGripItem(self, i, direction)
                self.scene().addItem(item)
                self.sizeGripItems.append(item)

    def updateLineGripItem(self, index_no_updates=None):
        """
        updates line grip items
        """
        # index_no_updates = index_no_updates or []
        for item in self.lineGripItems:
            item.updatePosition()

    def updateSizeGripItem(self, index_no_updates=None):
        """
        updates size grip items
        """
        index_no_updates = index_no_updates or []
        for i, item in zip(range(len(self.sizeGripItems)), self.sizeGripItems):
            if i not in index_no_updates:
                item.updatePosition()

    def itemChange(self, change, value):
        """Overloads and extends QGraphicsSvgItem to also update grip items
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
        self.hideGripItem()
        super(NodeItem, self).hoverLeaveEvent(event)

    def showGripItem(self):
        """shows grip items of svg item
        """
        for item in self.lineGripItems:
            item.setPen(QPen(QColor("black"), 2))
            item.setBrush(QColor("red"))
        for item in self.sizeGripItems:
            item.setPen(QPen(QColor("black"), 2))

    def hideGripItem(self):
        """hide grip items of svg item
        """
        for item in self.lineGripItems:
            if item.isSelected() is False:
                item.setPen(QPen(Qt.transparent))
                item.setBrush(Qt.transparent)
        for item in self.sizeGripItems:
            item.setPen(QPen(Qt.transparent))
            item.setBrush(Qt.transparent)
