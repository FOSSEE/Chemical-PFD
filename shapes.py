import random

from PyQt5 import QtCore
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer
from PyQt5.QtWidgets import QLineEdit, QGraphicsItem, QGraphicsEllipseItem, QGraphicsProxyWidget, QGraphicsPathItem
from PyQt5.QtGui import QPen, QColor, QFont, QCursor, QPainterPath, QPainter
from PyQt5.QtCore import Qt, QRectF, QPointF, QSizeF
from PyQt5.uic.properties import QtGui


class GripItem(QGraphicsPathItem):
    """
    Extends PyQt5's QGraphicsPathItem to create the general structure of the Grabbable points for resizing shapes.
    Takes two parameters, reference item (On which the grip items are to appear) and the grip index
    """
    circle = QPainterPath()
    circle.addEllipse(QRectF(-5, -5, 20, 20))

    def __init__(self, annotation_item, index):
        """
        Extends PyQt5's QGraphicsPathItem to create the general structure of the Grabbable points for resizing shapes.
        """
        super(GripItem, self).__init__()
        self.m_annotation_item = annotation_item
        self.m_index = index

        self.setPath(GripItem.circle)
        self.setPen(QPen(QColor(), -1))
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(11)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def hoverEnterEvent(self, event):
        """
        defines shape highlighting on Mouse Over
        """
        self.setPen(QPen(QColor("black"), 2))
        self.setBrush(QColor("red"))
        super(GripItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """
        defines shape highlighting on Mouse Leave
        """
        self.setPen(QPen(Qt.transparent))
        self.setBrush(Qt.transparent)
        super(GripItem, self).hoverLeaveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Automatically deselects grip item on mouse release
        """
        self.setSelected(False)
        super(GripItem, self).mouseReleaseEvent(event)

    def itemChange(self, change, value):
        """
        Calls movepoint from reference item, with the index of this grip item
        """
        if change == QGraphicsItem.ItemPositionChange and self.isEnabled():
            self.m_annotation_item.movePoint(self.m_index, value)
        return super(GripItem, self).itemChange(change, value)


class DirectionGripItem(GripItem):
    """
    Extends grip items for vertical and horizontal directions, with hover events and directional changes
    """

    def __init__(self, annotation_item, direction=Qt.Horizontal, parent=None):
        """
        Extends grip items for vertical and horizontal directions, with hover events and directional changes
        """
        super(DirectionGripItem, self).__init__(annotation_item, parent)
        self._direction = direction

    @property
    def direction(self):
        """
        property that returns the current intended resize direction of the grip item object
        """
        return self._direction

    def hoverEnterEvent(self, event):
        """
        Changes cursor to horizontal resize or vertical resize depending on the direction of the grip item on mouse enter
        """
        if self._direction == Qt.Horizontal:
            self.setCursor(QCursor(Qt.SizeHorCursor))
        else:
            self.setCursor(QCursor(Qt.SizeVerCursor))
        super(DirectionGripItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """
        reverts cursor to default on mouse leave
        """
        self.setCursor(QCursor(Qt.ArrowCursor))
        super(DirectionGripItem, self).hoverLeaveEvent(event)

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
            self.m_annotation_item.movePoint(self.m_index, p)
            return p
        return super(DirectionGripItem, self).itemChange(change, value)


class NodeItem(QGraphicsSvgItem):

    def __init__(self, unitOpType, parent=None):
        QGraphicsSvgItem.__init__(self, parent)
        self.type = unitOpType
        self.rect = QRectF(0, 0, 100, 100)
        self.renderer = QSvgRenderer("svg/" + "Column" + ".svg")
        self.setSharedRenderer(self.renderer)

        self.setZValue(1)
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsSvgItem.ItemIsMovable |
                      QGraphicsSvgItem.ItemIsSelectable |
                      QGraphicsSvgItem.ItemSendsGeometryChanges)

        self.gripItems = []

    # def shape(self):
    #     path = QtGui.QPainterPath()
    #     path.addRect(QRectF(-10 , -10 ,50 , 50 ))
    #     return path

    def boundingRect(self):
        return self.rect

    def paint(self, painter, options, widget):
        self.renderer.render(painter, self.boundingRect())

    def update_rect(self):
        """Update rect of node item
        """
        self.prepareGeometryChange()
        self.update(self.rect)

    def movePoint(self, i, p):
        """Move grip item with changing rect of node item
        """
        radiusOfGripItem = self.gripItems[i].boundingRect().width() / 2
        x = self.boundingRect().x()
        y = self.boundingRect().y()
        width = self.boundingRect().width()
        height = self.boundingRect().height()
        p_new = self.gripItems[i].pos()

        if i == 0 or i == 1:
            self.rect = QRectF(x + p.x() - p_new.x(), y + p.y() - p_new.y(), width - p.x() + p_new.x(),
                               height - p.y() + p_new.y())

        if i == 2 or i == 3:
            self.rect = QRectF(x, y, width + p.x() - p_new.x(), height + p.y() - p_new.y())

        self.update_rect()
        self.update_items_positions([i])

    def addGripItem(self):
        """adds grip items and the to parent
        """
        if self.scene() and not self.gripItems:
            for i, (direction) in enumerate(
                    (
                            Qt.Vertical,
                            Qt.Horizontal,
                            Qt.Vertical,
                            Qt.Horizontal,
                    )
            ):
                item = DirectionGripItem(self, direction, i)
                self.scene().addItem(item)
                self.gripItems.append(item)

    def update_items_positions(self, index_no_updates=None):
        """updates grip items
        """
        index_no_updates = index_no_updates or []
        for i, (item, direction) in enumerate(
                zip(
                    self.gripItems,
                    (
                            Qt.Vertical,
                            Qt.Horizontal,
                            Qt.Vertical,
                            Qt.Horizontal,
                    ),
                ),
        ):
            if i not in index_no_updates:
                itemToUpdate = self.gripItems[i]
                pos = self.mapToScene(self.point(i))
                x = self.boundingRect().x()
                y = self.boundingRect().y()
                pos.setX(pos.x() + x)
                pos.setY(pos.y() + y)
                itemToUpdate._direction = direction
                itemToUpdate.setEnabled(False)
                itemToUpdate.setPos(pos)
                itemToUpdate.setEnabled(True)

    def point(self, index):
        """
        yields a list of positions of grip items in a node item
        """
        radiusOfGripItem = self.gripItems[index].boundingRect().width() / 2
        x = self.boundingRect().width() - radiusOfGripItem
        y = self.boundingRect().height() - radiusOfGripItem
        if 0 <= index < 4:
            return [
                QPointF(x / 2, 0),
                QPointF(0, y / 2),
                QPointF(x / 2, y),
                QPointF(x, y / 2)
            ][index]

    def itemChange(self, change, value):
        """Overloads and extends QGraphicsSvgItem to also update gripitem
        """
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.update_items_positions()
            return
        if change == QGraphicsItem.ItemSceneHasChanged:
            self.addGripItem()
            self.update_items_positions()
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
        self.scene().removeItem(self)

    def mousePressEvent(self, event):
        # select object
        super(NodeItem, self).mousePressEvent(event)

    def hoverEnterEvent(self, event):
        """defines shape highlighting on Mouse Over
        """
        for item in self.gripItems:
            item.setPen(QPen(QColor("black"), 2))
            item.setBrush(QColor("red"))
            super(NodeItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """defines shape highlighting on Mouse Leave
        """
        for item in self.gripItems:
            item.setPen(QPen(Qt.transparent))
            item.setBrush(Qt.transparent)
            super(NodeItem, self).hoverLeaveEvent(event)
