from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import (QEvent, QFile, QIODevice, QMimeData, QPointF, QRect,
                          QRectF, QSizeF, Qt)
from PyQt5.QtGui import (QBrush, QColor, QCursor, QDrag, QFont, QImage,
                         QPainter, QPainterPath, QPen, QTransform, QTextCursor, QPainterPathStroker)
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer
from PyQt5.QtWidgets import (QGraphicsColorizeEffect, QGraphicsEllipseItem,
                             QGraphicsItem, QGraphicsPathItem,
                             QGraphicsProxyWidget, QGraphicsSceneHoverEvent,
                             QLineEdit, QMenu, QGraphicsTextItem)

from .line import Line, findIndex
from utils.app import fileImporter


class ItemLabel(QGraphicsTextItem):
    def __init__(self, pos, parent=None):
        super().__init__(parent=parent)
        self.setPlainText("abc")
        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setPos(self.parentItem().boundingRect().bottomLeft())

    def mouseDoubleClickEvent(self, event):
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.setFocus()
        super(ItemLabel, self).mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        super(ItemLabel, self).focusOutEvent(event)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

    def __getstate__(self):
        return {
            "text": self.toPlainText(),
            "pos": (self.pos().x(), self.pos().y())
        }

    def __setstate__(self, dict):
        self.setPlainText(dict['text'])
        self.setPos(*dict['pos'])


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
        path.addRect(QRectF(-self.width / 2, -self.height / 2, self.width, self.height))
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

    def paint(self, painter, option, widget):
        if self.isSelected() and not self.parentItem().isSelected():
            self.parentItem().setSelected(True)
            self.parentItem().setFlag(QGraphicsSvgItem.ItemIsMovable, False)
        super().paint(painter, option, widget)

    def updatePath(self):
        """updates path of size grip item
        """
        if self._direction is Qt.Horizontal:
            self.height = self.parentItem().boundingRect().height()
        else:
            self.width = self.parentItem().boundingRect().width()
        path = QPainterPath()
        path.addRect(QRectF(-self.width / 2, -self.height / 2, self.width, self.height))
        self.setPath(path)

    def updatePosition(self):
        """updates position of grip items
        """
        self.updatePath()
        pos = self.point(self.m_index)
        self.setEnabled(False)
        self.setPos(pos)
        self.setEnabled(True)

    def point(self, index):
        """
        yields a list of positions of grip items in a node item
        """
        width = self.parentItem().boundingRect().width()
        height = self.parentItem().boundingRect().height()
        if 0 <= index < 4:
            return [
                QPointF(0, -height / 2),
                QPointF(-width / 2, 0),
                QPointF(0, height / 2),
                QPointF(width / 2, 0)
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
            # Find change in positions
            movement = p - self.pos()
            # Set transform to oppose change in transformation due to parent
            transform = QTransform()
            transform.translate(-movement.x() / 2, -movement.y() / 2)
            self.setTransform(transform, True)
            self.parentItem().resize(self.m_index, movement)
            return p
        return super(SizeGripItem, self).itemChange(change, value)

    def mouseReleaseEvent(self, event):
        super(SizeGripItem, self).mouseReleaseEvent(event)
        # Reset transform and update position
        self.resetTransform()
        self.updatePosition()
        # Make parent item move able
        self.parentItem().setFlag(QGraphicsSvgItem.ItemIsMovable, True)
        # If needed to reset transform of parent set it's position accordingly
        # self.parentItem().setPos(self.parentItem().x() + self.parentItem().transform().dx(), self.parentItem().y() + self.parentItem().transform().dy())
        # self.parentItem().resetTransform()


class LineGripItem(GripItem):
    """Extends grip items for connecting lines , with hover events and mouse events
    """
    circle = QPainterPath()
    circle.addEllipse(QRectF(-5, -5, 10, 10))

    def __init__(self, annotation_item, index, grip, parent=None):
        path = LineGripItem.circle

        super(LineGripItem, self).__init__(annotation_item, path=path, parent=parent)
        self.m_index = index
        self.m_location = grip[2]
        self.line = None
        # stores current line which is in process
        self.tempLine = None
        # keep previous hovered item when line drawing in process
        self.previousHoveredItem = None
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setPen(QPen(QColor("black"), -1))
        self.grip = grip

    def shape(self):
        qp = QPainterPathStroker()
        qp.setWidth(8)
        path = qp.createStroke(self.path())
        return path

    def paint(self, painter,option, widget):
        painter.setPen(self.pen())
        painter.drawPath(self.shape())
        painter.setBrush(self.brush())
        if len(self.grip) ==4:
            painter.save()
            pen =self.pen()
            pen.setWidth(-1)
            painter.setPen(pen)
            painter.drawPath(self.path())
            painter.restore()
        else:
            painter.drawPath(self.path())

    def itemChange(self, change, value):
        """
        Moves position of grip item on resize
        """
        if change == QGraphicsItem.ItemSceneHasChanged and not self.scene():
            if self.line and self.line.scene():
                self.line.scene().removeItem(self.line)
        return super(LineGripItem, self).itemChange(change, value)

    def point(self, index):
        """
        yields a list of positions of grip items in a node item
        """
        width = self.parentItem().boundingRect().width()
        height = self.parentItem().boundingRect().height()
        if 0 <= index < 4:
            return [
                QPointF(0, -height / 2),
                QPointF(-width / 2, 0),
                QPointF(0, height / 2),
                QPointF(width / 2, 0)
            ][index]

    def updatePosition(self):
        width = self.parentItem().boundingRect().width()
        height = self.parentItem().boundingRect().height()
        if len(self.grip) == 4:
            rect_width = rect_height = 4
            if self.grip[2] in ["left","right"]:
                rect_height = (self.grip[3]*height)/100
            else:
                rect_width = (self.grip[3]*width)/100
            path = QPainterPath()
            path.addRect(QRectF(-rect_width / 2, -rect_height / 2, rect_width, rect_height))
            self.setPath(path)

        x = (self.grip[0] * width) / 100
        y = (self.grip[1] * height) / 100
        x -= width / 2
        y -= height / 2
        y = -y
        self.setEnabled(False)
        self.setPos(QPointF(x, y))
        self.setEnabled(True)
        if self.line:
            self.line.updateLine()

    def mousePressEvent(self, mouseEvent):
        """Handle all mouse press for this item
        """
        if mouseEvent.button() != Qt.LeftButton:
            return
        # initialize a line and add on scene
        if not self.line:
            startPoint = endPoint = self.parentItem().mapToScene(self.pos())
            self.tempLine = Line(startPoint, endPoint)
            self.scene().addItem(self.tempLine)
        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """Handle all mouse move for this item
        """
        # if line get started then update it's end point
        if self.tempLine:
            endPoint = mouseEvent.scenePos()
            self.tempLine.updateLine(endPoint=endPoint)

        item = self.scene().itemAt(mouseEvent.scenePos().x(), mouseEvent.scenePos().y(),
                                   QTransform())

        if self.previousHoveredItem and item != self.previousHoveredItem and \
                item not in self.previousHoveredItem.lineGripItems:
            self.previousHoveredItem.hideGripItem()
        super().mouseMoveEvent(mouseEvent)

        if isinstance(item, NodeItem):
            self.previousHoveredItem = item
            item.showGripItem()

    def mouseReleaseEvent(self, mouseEvent):
        """Handle all mouse release for this item"""
        super().mouseReleaseEvent(mouseEvent)
        # set final position of line
        if self.tempLine:
            items = self.scene().items(QPointF(mouseEvent.scenePos().x(), mouseEvent.scenePos().y()))
            for item in items:
                if type(item) == LineGripItem and item != self:
                    if item.line:
                        break
                    self.tempLine.setStartGripItem(self)
                    self.tempLine.setEndGripItem(item)
                    endPoint = item.parentItem().mapToScene(item.pos())
                    self.tempLine.updateLine(endPoint=endPoint)
                    self.line = self.tempLine
                    item.line = self.tempLine
                    break
                elif type(item) == Line and item != self.tempLine:
                    self.tempLine.setStartGripItem(self)
                    endPoint = mouseEvent.scenePos()
                    self.tempLine.refLine = item
                    self.tempLine.refIndex = findIndex(item, endPoint)
                    self.tempLine.updateLine(endPoint=endPoint)
                    item.midLines.append(self.tempLine)
                    self.line = self.tempLine
                    break
            self.scene().removeItem(self.tempLine)
            if self.line:
                self.scene().addItemPlus(self.line)

        self.tempLine = None
        self.previousHoveredItem = None

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

    # set a common renderer for all svg
    # renderer = QSvgRenderer(fileImporter(f'svg/ellipse.svg'))

    def __init__(self, unitOperationType=None, parent=None):
        QGraphicsSvgItem.__init__(self, parent)
        self.m_type = str(unitOperationType)
        self.id = None
        self.m_renderer = QSvgRenderer(fileImporter(f'{unitOperationType}.svg'))
        self.setSharedRenderer(self.m_renderer)
        # set initial size of item
        self.width = self.m_renderer.defaultSize().width()
        self.height = self.m_renderer.defaultSize().height()
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
        self.label = None

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
        elif self.id:
            self.m_renderer.render(painter, self.id, self.boundingRect())
        else:
            self.m_renderer.render(painter, self.boundingRect())
        if self.isSelected():
            self.showGripItem()

    def resize(self, index, movement):
        """Move grip item with changing rect of node item
        """
        self.prepareGeometryChange()
        if index in [0, 1]:
            self.width -= movement.x()
            self.height -= movement.y()
        else:
            self.width += movement.x()
            self.height += movement.y()

        self.rect = QRectF(-self.width / 2, -self.height / 2, self.width, self.height)
        transform = QTransform()
        transform.translate(movement.x() / 2, movement.y() / 2)
        self.setTransform(transform, True)
        self.updateSizeGripItem([index])

    def addGripItem(self):
        """adds grip items
        """
        if self.scene():
            # add grip for resize it
            for i, (direction) in enumerate(
                    (
                            Qt.Vertical,
                            Qt.Horizontal,
                            Qt.Vertical,
                            Qt.Horizontal,
                    )
            ):
                item = SizeGripItem(self, i, direction, parent=self)
                self.sizeGripItems.append(item)
            # add grip items for connecting lines
            for i in range(len(self.grips)):
                grip = self.grips[i]
                item = LineGripItem(self, i, grip, parent=self)
                self.lineGripItems.append(item)

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
        for i, item in enumerate(self.sizeGripItems):
            if i not in index_no_updates:
                item.updatePosition()

    def itemChange(self, change, value):
        """Overloads and extends QGraphicsSvgItem to also update grip items
        """
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if value is True:
                self.showGripItem()
            else:
                self.hideGripItem()
            return
        if change == QGraphicsItem.ItemTransformHasChanged:
            self.updateLineGripItem()
            return
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.updateLineGripItem()
            self.updateSizeGripItem()
            return
        if change == QGraphicsItem.ItemSceneHasChanged and self.scene():
            self.addGripItem()
            self.updateLineGripItem()
            self.updateSizeGripItem()
            return
        return super(NodeItem, self).itemChange(change, value)

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

    def contextMenuEvent(self, event):
        """Pop up menu
        :return:
        """
        contextMenu = QMenu()
        addLabelAction = contextMenu.addAction("add Label")
        # addLabelAction.triggered.connect(self.addLabel)
        action = contextMenu.exec_(event.screenPos())
        if action == addLabelAction:
            self.label = ItemLabel(event.scenePos(), self)
            self.scene().labelAdded.emit(self.label)

    def __getstate__(self):
        return {
            "_classname_": self.__class__.__name__,
            "width": self.width,
            "height": self.height,
            "pos": (self.pos().x(), self.pos().y()),
            "lineGripItems": [(hex(id(i)), i.m_index) for i in self.lineGripItems],
            "label": self.label
        }

    def __setstate__(self, dict):
        self.prepareGeometryChange()
        self.width = dict['width']
        self.height = dict['height']
        self.rect = QRectF(-self.width / 2, -self.height / 2, self.width, self.height)
        self.updateSizeGripItem()


class InflowLine(NodeItem):
    def __init__(self):
        super(InflowLine, self).__init__("svg/piping/Inflow Line")
        self.grips = [
            [100, 50, "right"]
        ]


class OutflowLine(NodeItem):
    def __init__(self):
        super(OutflowLine, self).__init__("svg/Piping/Outflow Line")
        self.grips = [
            [0, 50, "left"]
        ]


class DuplexPump(NodeItem):
    def __init__(self):
        super(DuplexPump, self).__init__("svg/Pumps/Duplex Pump")
        self.grips = [
            [100, 68.8031698, "right"],
            [0, 88.1365808, "left"]
        ]


class PlungerPump(NodeItem):
    def __init__(self):
        super(PlungerPump, self).__init__("svg/Pumps/Plunger Pump")
        self.grips = [
            [87.0328592, 100, "top"],
            [87.0328592, 0, "bottom"]
        ]


class ProportioningPump(NodeItem):
    def __init__(self):
        super(ProportioningPump, self).__init__("svg/Pumps/Proportioning Pump")
        self.grips = [
            [100, 83.0966226, "right"],
            [0, 83.0966226, "left"]
        ]


class ReciprocatingPump(NodeItem):
    def __init__(self):
        super(ReciprocatingPump, self).__init__("svg/Pumps/Reciprocating Pump")
        self.grips = [
            [100, 78.3969475, "right"],
            [0, 78.3969475, "left"]
        ]


class BlowingEgg(NodeItem):
    def __init__(self):
        super(BlowingEgg, self).__init__("svg/Pumps/Blowing Egg")
        self.grips = [
            [15.2887853, 56.4147177, "top"],
            [84.7112147, 56.4147177, "top"]
        ]


class EjectorVaporService(NodeItem):
    def __init__(self):
        super(EjectorVaporService, self).__init__("svg/Pumps/Ejector(Vapor Service)")
        self.grips = [
            [18, 100, "top"],
            [0, 50, "left"],
            [100, 50, "right"]
        ]


class HandPumpWithDrum(NodeItem):
    def __init__(self):
        super(HandPumpWithDrum, self).__init__("svg/Pumps/Hand Pump with Drum")
        self.grips = [
            [92.8093483, 70.60413752309337, "right"],
            [7.913824600849647, 70.60413752309337, "left"],
            [4.136894788615162, 86.9886362, "left"]
        ]


class CentrifugalCompressor(NodeItem):
    def __init__(self):
        super(CentrifugalCompressor, self).__init__("svg/Compressors/Centrifugal Compressor")
        self.grips = [
            [41.316753407496, 89.824108247573, "top"],
            [62.0517030576456, 79.183192150093, "top"],
            [41.316753407496, 6.447877022097, "bottom"],
            [62.0517030576456, 16.14847772052, "bottom"]
        ]


class EjectorCompressor(NodeItem):
    def __init__(self):
        super(EjectorCompressor, self).__init__("svg/Compressors/Ejector Compressor")
        self.grips = [
            [13.1018813062, 100, "top"],
            [0, 50, "left"],
            [100, 50, "right"]
        ]


class Fan(NodeItem):
    def __init__(self):
        super(Fan, self).__init__("svg/Compressors/Fan")
        self.grips = [
            [50, 79.92762310350343, "top"],
            [0, 79.92762310350343, "left"],
            [100, 79.92762310350343, "right"]
        ]


class PositiveDisplacementCompressor(NodeItem):
    def __init__(self):
        super(PositiveDisplacementCompressor, self).__init__("svg/Compressors/Positive Displacement Compressor")
        self.grips = [
            [50, 100, "top"],
            [21.15509548928236, 30, "left"],
            [79.57853462426666, 30, "right"]
        ]


class ReciprocatingCompressor(NodeItem):
    def __init__(self):
        super(ReciprocatingCompressor, self).__init__("svg/Compressors/Reciprocating Compressor")
        self.grips = [
            [22.85680252121469, 83, "left"],
            [46.81088180183039, 83, "right"]
        ]


class Turbine(NodeItem):
    def __init__(self):
        super(Turbine, self).__init__("svg/Compressors/Turbine")
        self.grips = [
            [18.06209745144267, 79.11931909160472, "top"],
            [45.2091373550176,  91.385325275219, "top"],
            [18.06209745144267, 16.41537491819628, "bottom"],
            [45.2091373550176, 4.5725942986116, "bottom"]
        ]


class OilGasOrPulverizedFuelFurnace(NodeItem):
    def __init__(self):
        super(OilGasOrPulverizedFuelFurnace, self).__init__("svg/Furnaces and Boilers/Oil Gas or Pulverized Fuel Furnace")
        self.grips = [
            [58.27673386073162,100,"top"],
            [0,19.692723451106,"left"] ,
            [17.2777337415748,33.3944873323144,"left",66.7889746646288],
            [100,33.3944873323144,"right",66.7889746646288],
            [57.9723659874,0,"bottom",81.389264491796]
        ]


class SolidFuelFurnace(NodeItem):
    def __init__(self):
        super(SolidFuelFurnace, self).__init__("svg/Furnaces and Boilers/Solid Fuel Furnace")
        self.grips = [
            [50,100,"top"],
            [0,33.39352642259468,"left",66.78705284518936],
            [100,33.39352642259468,"right",66.78705284518936],
            [50,0,"bottom",100]
        ]


# class Exchanger(NodeItem):
#     def __init__(self):
#         super(Exchanger, self).__init__("svg/Heating or Cooling Arrangements/905Exchanger")
#         self.grips = [
#             [92.8093483, 70.60413752309337, "right"],
#             [7.913824600849647, 70.60413752309337, "left"],
#             [4.136894788615162, 86.9886362, "left"]
#         ]


# class KettleReboiler(NodeItem):
#     def __init__(self):
#         super(KettleReboiler, self).__init__("svg/Heating or Cooling Arrangements/907Kettle Reboiler")
#         self.grips = [
#             [41.316753407496, 89.824108247573, "top"],
#             [62.0517030576456, 79.183192150093, "top"],
#             [41.316753407496, 6.447877022097, "bottom"],
#             [62.0517030576456, 16.14847772052, "bottom"]
#         ]


class Exchanger(NodeItem):
    def __init__(self):
        super(Exchanger, self).__init__("svg/Heating or Cooling Arrangements/Exchanger")
        self.grips = [
            [100,31.74474612706027,"right"],
            [100,62.70549343934227,"right"],
            [33.68240920045628,100,"top"],
            [33.68240920045628,0,"bottom"]
        ]


# class Fan(NodeItem):
#     def __init__(self):
#         super(Fan, self).__init__("svg/Compressors/Fan")
#         self.grips = [
#             [41.4323581, 100, "top"],
#             [61.1489583, 100, "top"]
#         ]


class HeatExchanger(NodeItem):
    def __init__(self):
        super(HeatExchanger, self).__init__("svg/Heating or Cooling Arrangements/Heat Exchanger")
        self.grips = [
            [0,47.14356681569796,"left"],
            [100,47.14356681569796,"right"],
            [50.92839727035332,100,"top"],
            [50.92839727035332,0,"bottom"]
        ]


class ImmersionCoil(NodeItem):
    def __init__(self):
        super(ImmersionCoil, self).__init__("svg/Heating or Cooling Arrangements/Immersion Coil")
        self.grips = [
            [44.56276981957,100,"top"],
            [88.232463407718,100,"top"]
        ]


class HorizontalVessel(NodeItem):
    def __init__(self):
        super(HorizontalVessel, self).__init__("svg/Process Vessels/Horizontal Vessel")
        self.grips = [
            [50,100,"top",87.08554680344],
            [0,50,"left"],
            [100,50,"right"],
            [50,0,"bottom",87.08554680344]
        ]

class PackedVessel(NodeItem):
    def __init__(self):
        super(PackedVessel, self).__init__("svg/Process Vessels/Packed Vessel")
        self.grips = [
            [50,100,"top"],
            [0,50,"left",86.703566201060],
            [100,50,"right",86.703566201060],
            [50,0,"bottom"]
        ]

class TraysOrPlates(NodeItem):
    def __init__(self):
        super(TraysOrPlates, self).__init__("svg/Process Vessels/Trays or plates")
        self.grips = [
        ]

class VerticalVessel(NodeItem):
    def __init__(self):
        super(VerticalVessel, self).__init__("svg/Process Vessels/Vertical Vessel")
        self.grips = [
            [50,100,"top"],
            [0,50,"left",86.703566201060],
            [100,50,"right",86.703566201060],
            [50,0,"bottom"]
        ]


class Separators(NodeItem):
    def __init__(self):
        super(Separators, self).__init__("svg/Separators/Separators for Liquids, Decanter")
        self.grips = [
            [50,100,"top",100],
            [0,50,"left",100],
            [100,50,"right",100],
            [50,0,"bottom",100]
        ]

class FixedRoofTank(NodeItem):
    def __init__(self):
        super(FixedRoofTank, self).__init__("svg/Storage Vessels Tanks/Fixed Roof Tank")
        self.grips = [
            [50,100,"top"],
            [0,50,"left",100],
            [100,50,"right",100],
            [50,0,"bottom",100]
        ]


class FloatingRoofTank(NodeItem):
    def __init__(self):
        super(FloatingRoofTank, self).__init__("svg/Storage Vessels Tanks/Floating Roof Tank")
        self.grips = [
            [0,50,"left",100],
            [100,50,"right",100],
            [50,0,"bottom",100]
        ]

class SeparatorsForLiquidsDecanter(NodeItem):
    def __init__(self):
        super(SeparatorsForLiquidsDecanter, self).__init__("svg/Separators/Separators for Liquids, Decanter")
        self.grips = [
            [50,100,"top",100],
            [0,50,"left",100],
            [100,50,"right",100],
            [50,0,"bottom",100]
        ]


