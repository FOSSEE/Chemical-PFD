# from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer
from PyQt5.QtWidgets import QLineEdit, QGraphicsItem, QGraphicsEllipseItem, QGraphicsProxyWidget, QGraphicsPathItem, \
    QGraphicsSceneHoverEvent, QGraphicsColorizeEffect
from PyQt5.QtGui import QPen, QColor, QFont, QCursor, QPainterPath, QPainter, QDrag, QBrush, QImage
from PyQt5.QtCore import Qt, QRectF, QPointF, QSizeF, QEvent, QMimeData, QFile, QIODevice, QRect

from .line import Line


# resourceManager = ApplicationContext()


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
        # if line get started then update it's end point
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
        # self.m_renderer = QSvgRenderer(resourceManager.get_resource(f'toolbar/{unitOperationType}.svg'))
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

    def resize(self, index, new_pos):
        """Move grip item with changing rect of node item
        """
        x = self.boundingRect().x()
        y = self.boundingRect().y()
        width = self.boundingRect().width()
        height = self.boundingRect().height()
        old_pos = self.sizeGripItems[index].pos()
        self.prepareGeometryChange()

        if index == 0 or index == 1:
            self.rect = QRectF(x + new_pos.x() - old_pos.x(), y + new_pos.y() - old_pos.y(),
                               width - new_pos.x() + old_pos.x(),
                               height - new_pos.y() + old_pos.y())

        if index == 2 or index == 3:
            self.rect = QRectF(x, y, width + new_pos.x() - old_pos.x(), height + new_pos.y() - old_pos.y())

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
                # self.scene().addItem(item)
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

#classes of pfd-symbols
class AirBlownCooler(NodeItem):
    def __init__(self):
        super(AirBlownCooler, self).__init__("AirBlownCooler", parent=None)


class Bag(NodeItem):
    def __init__(self):
        super(Bag, self).__init__("Bag", parent=None)


class Boiler(NodeItem):
    def __init__(self):
        super(Boiler, self).__init__("Boiler", parent=None)


class Breaker(NodeItem):
    def __init__(self):
        super(Breaker, self).__init__("Breaker", parent=None)


class BriquettingMachine(NodeItem):
    def __init__(self):
        super(BriquettingMachine, self).__init__("BriquettingMachine", parent=None)


class Centrifugal(NodeItem):
    def __init__(self):
        super(Centrifugal, self).__init__("Centrifugal", parent=None)


class CentrifugalCompressor(NodeItem):
    def __init__(self):
        super(CentrifugalCompressor, self).__init__("CentrifugalCompressor", parent=None)


class Centrifugalpump(NodeItem):
    def __init__(self):
        super(Centrifugalpump, self).__init__("Centrifugalpump", parent=None)


class CentrifugalPump2(NodeItem):
    def __init__(self):
        super(CentrifugalPump2, self).__init__("CentrifugalPump2", parent=None)


class CentrifugalPump3(NodeItem):
    def __init__(self):
        super(CentrifugalPump3, self).__init__("CentrifugalPump3", parent=None)


class Column(NodeItem):
    def __init__(self):
        super(Column, self).__init__("Column", parent=None)


class Compressor(NodeItem):
    def __init__(self):
        super(Compressor, self).__init__("Compressor", parent=None)


class CompressorSilencers(NodeItem):
    def __init__(self):
        super(CompressorSilencers, self).__init__("CompressorSilencers", parent=None)


class Condenser(NodeItem):
    def __init__(self):
        super(Condenser, self).__init__("Condenser", parent=None)


class Cooler(NodeItem):
    def __init__(self):
        super(Cooler, self).__init__("Cooler", parent=None)


class CoolingTower3(NodeItem):
    def __init__(self):
        super(CoolingTower3, self).__init__("CoolingTower3", parent=None)


class CoolingTwoer2(NodeItem):
    def __init__(self):
        super(CoolingTwoer2, self).__init__("CoolingTwoer2", parent=None)


class Crusher(NodeItem):
    def __init__(self):
        super(Crusher, self).__init__("Crusher", parent=None)


class DoublePipeHeat(NodeItem):
    def __init__(self):
        super(DoublePipeHeat, self).__init__("DoublePipeHeat", parent=None)


class ExtractorHood(NodeItem):
    def __init__(self):
        super(ExtractorHood, self).__init__("ExtractorHood", parent=None)


class FiredHeater(NodeItem):
    def __init__(self):
        super(FiredHeater, self).__init__("FiredHeater", parent=None)


class ForcedDraftCooling(NodeItem):
    def __init__(self):
        super(ForcedDraftCooling, self).__init__("ForcedDraftCooling", parent=None)


class Furnace(NodeItem):
    def __init__(self):
        super(Furnace, self).__init__("Furnace", parent=None)


class GasBottle(NodeItem):
    def __init__(self):
        super(GasBottle, self).__init__("GasBottle", parent=None)


class HalfPipeMixingVessel(NodeItem):
    def __init__(self):
        super(HalfPipeMixingVessel, self).__init__("HalfPipeMixingVessel", parent=None)


class Heater(NodeItem):
    def __init__(self):
        super(Heater, self).__init__("Heater", parent=None)


class HeatExchanger(NodeItem):
    def __init__(self):
        super(HeatExchanger, self).__init__("HeatExchanger", parent=None)


class HeatExchanger2(NodeItem):
    def __init__(self):
        super(HeatExchanger2, self).__init__("HeatExchanger2", parent=None)


class HorizontalVessel(NodeItem):
    def __init__(self):
        super(HorizontalVessel, self).__init__("HorizontalVessel", parent=None)


class InducedDraftCooling(NodeItem):
    def __init__(self):
        super(InducedDraftCooling, self).__init__("InducedDraftCooling", parent=None)


class jacketedMixingVessel(NodeItem):
    def __init__(self):
        super(jacketedMixingVessel, self).__init__("jacketedMixingVessel", parent=None)


class LiquidRingCompressor(NodeItem):
    def __init__(self):
        super(LiquidRingCompressor, self).__init__("LiquidRingCompressor", parent=None)


class Mixing(NodeItem):
    def __init__(self):
        super(Mixing, self).__init__("Mixing", parent=None)


class MixingReactor(NodeItem):
    def __init__(self):
        super(MixingReactor, self).__init__("MixingReactor", parent=None)


class OilBurner(NodeItem):
    def __init__(self):
        super(OilBurner, self).__init__("OilBurner", parent=None)


class OpenTank(NodeItem):
    def __init__(self):
        super(OpenTank, self).__init__("OpenTank", parent=None)


class ProportionalPump(NodeItem):
    def __init__(self):
        super(ProportionalPump, self).__init__("ProportionalPump", parent=None)


class Pump(NodeItem):
    def __init__(self):
        super(Pump, self).__init__("Pump", parent=None)


class Pump2(NodeItem):
    def __init__(self):
        super(Pump2, self).__init__("Pump2", parent=None)


class ReboilerHeatExchange(NodeItem):
    def __init__(self):
        super(ReboilerHeatExchange, self).__init__("ReboilerHeatExchange", parent=None)


class ReciprocatingCompressor(NodeItem):
    def __init__(self):
        super(ReciprocatingCompressor, self).__init__("ReciprocatingCompressor", parent=None)


class RotaryCompresor(NodeItem):
    def __init__(self):
        super(RotaryCompresor, self).__init__("RotaryCompresor", parent=None)


class RotaryGearPump(NodeItem):
    def __init__(self):
        super(RotaryGearPump, self).__init__("RotaryGearPump", parent=None)


class ScrewPump(NodeItem):
    def __init__(self):
        super(ScrewPump, self).__init__("ScrewPump", parent=None)


class SelectableCompressor(NodeItem):
    def __init__(self):
        super(SelectableCompressor, self).__init__("SelectableCompressor", parent=None)


class SelectableFan(NodeItem):
    def __init__(self):
        super(SelectableFan, self).__init__("SelectableFan", parent=None)


class SinglePassHeat(NodeItem):
    def __init__(self):
        super(SinglePassHeat, self).__init__("SinglePassHeat", parent=None)


class SpiralHeatExchanger(NodeItem):
    def __init__(self):
        super(SpiralHeatExchanger, self).__init__("SpiralHeatExchanger", parent=None)


class StraightTubersHeat(NodeItem):
    def __init__(self):
        super(StraightTubersHeat, self).__init__("StraightTubersHeat", parent=None)


class Tank(NodeItem):
    def __init__(self):
        super(Tank, self).__init__("Tank", parent=None)


class TurbinePump(NodeItem):
    def __init__(self):
        super(TurbinePump, self).__init__("TurbinePump", parent=None)


class UTubeHeatExchanger(NodeItem):
    def __init__(self):
        super(UTubeHeatExchanger, self).__init__("UTubeHeatExchanger", parent=None)


class VaccumPump(NodeItem):
    def __init__(self):
        super(VaccumPump, self).__init__("VaccumPump", parent=None)


class VerticalPump(NodeItem):
    def __init__(self):
        super(VerticalPump, self).__init__("VerticalPump", parent=None)


class VerticalVessel(NodeItem):
    def __init__(self):
        super(VerticalVessel, self).__init__("VerticalVessel", parent=None)


class WastewaterTreatment(NodeItem):
    def __init__(self):
        super(WastewaterTreatment, self).__init__("WastewaterTreatment", parent=None)
