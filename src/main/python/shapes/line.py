from PyQt5.QtGui import QPen, QPainterPath, QBrush, QPainterPathStroker, QPainter, QCursor
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem
from PyQt5.QtCore import Qt, QPointF, QRectF

class Grabber(QGraphicsPathItem):
    """
    Extends QGraphicsPathItem to create grabber for line for moving a particular segment
    """
    circle = QPainterPath()
    circle.addEllipse(QRectF(-5, -5, 10, 10))

    def __init__(self, annotation_line, index, direction):
        super(Grabber, self).__init__()
        self.m_index = index
        self.m_annotation_item = annotation_line
        self._direction = direction
        self.setPath(Grabber.circle)
        # set graphical settings for this item
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

    def itemChange(self, change, value):
        """ move position of grabber after resize"""
        if change == QGraphicsItem.ItemPositionChange and self.isEnabled():
            p = QPointF(self.pos())
            if self._direction == Qt.Horizontal:
                p.setX(value.x())
            elif self._direction == Qt.Vertical:
                p.setY(value.y())
            movement = p - self.pos()
            self.m_annotation_item.movePoints(self.m_index, movement)
            return p
        return super(Grabber, self).itemChange(change, value)

    def paint(self, painter, option, widget):
        """paints the path of grabber only if it is selected
        """
        if self.isSelected():
            # show line of grabber
            self.m_annotation_item.setSelected(True)
            painter.setBrush(QBrush(Qt.cyan))
        color = Qt.black if self.isSelected() else Qt.white
        width = 2 if self.isSelected() else -1
        painter.setPen(QPen(color, width, Qt.SolidLine))
        painter.drawPath(self.path())

        # To paint path of shape
        # color = Qt.red if self.isSelected() else Qt.black
        # painter.setPen(QPen(Qt.blue, 1, Qt.SolidLine))
        # painter.drawPath(self.shape())

    def shape(self):
        """Overrides shape method and set shape to segment on which grabber is located"""
        index = self.m_index
        startPoint = QPointF(self.m_annotation_item.path().elementAt(index))
        endPoint = QPointF(self.m_annotation_item.path().elementAt(index + 1))
        startPoint = self.mapFromParent(startPoint)
        endPoint = self.mapFromParent(endPoint)
        path = QPainterPath(startPoint)
        path.lineTo(endPoint)
        # generate outlines for path
        stroke = QPainterPathStroker()
        stroke.setWidth(8)
        return stroke.createStroke(path)

    def boundingRect(self):
        return self.shape().boundingRect()

    def mousePressEvent(self, event):
        print('grabber clicked', self)
        super(Grabber, self).mousePressEvent(event)

    def hoverEnterEvent(self, event):
        """
        Changes cursor to horizontal movement or vertical movement
         depending on the direction of the grabber on mouse enter
        """
        if self._direction == Qt.Horizontal:
            self.setCursor(QCursor(Qt.SplitHCursor))
        else:
            self.setCursor(QCursor(Qt.SplitVCursor))
        super(Grabber, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """
        reverts cursor to default on mouse leave
        """
        self.setCursor(QCursor(Qt.ArrowCursor))
        super(Grabber, self).hoverLeaveEvent(event)


class Line(QGraphicsPathItem):
    """
    Extends QGraphicsPathItem to draw zig-zag line consisting of multiple points
    """
    penStyle = Qt.SolidLine

    def __init__(self, startPoint, endPoint, **args):
        QGraphicsItem.__init__(self, **args)
        self.startPoint = startPoint
        self.endPoint = endPoint
        #stores all points of line
        self.points = []
        self.points.extend([startPoint, endPoint])
        self.startGripItem = None
        self.endGripItem = None
        self._selected = False
        self.m_grabbers = []
        # stores current pen style of line
        self.penStyle = Line.penStyle
        # set graphical settings for this item
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        # initiates path
        self.createPath()

    def createPath(self):
        """
        creates initial path and stores it's points
        :return:
        """
        offset = 30
        x0, y0 = self.startPoint.x(), self.startPoint.y()
        x1, y1 = self.endPoint.x(), self.endPoint.y()
        self.points = [self.startPoint, QPointF((x0 + x1) / 2, y0), QPointF((x0 + x1) / 2, y1), self.endPoint]
        if self.startGripItem and self.startGripItem.m_location in ["left", "right"]:
            if self.endGripItem and self.endGripItem.m_location in ["top", "bottom"]:
                if self.endGripItem.m_location == "top": offset = -offset
                self.points = [self.startPoint, QPointF((x0 + x1) / 2, y0), QPointF((x0 + x1) / 2, y1 + offset),
                               QPointF(self.endPoint.x(), y1 + offset), self.endPoint]

        if self.startGripItem and self.startGripItem.m_location in ["top", "bottom"]:
            self.points = [self.startPoint, QPointF(x0, (y0 + y1) / 2), QPointF(x1, (y0 + y1) / 2), self.endPoint]
            if self.endGripItem and self.endGripItem.m_location in ["left", "right"]:
                self.points = [self.startPoint, QPointF(x0, (y0 + y1) / 2), QPointF(x1 - offset, (y0 + y1) / 2),
                               QPointF(x1 - offset, self.endPoint.y()), self.endPoint]
        # draw line
        path = QPainterPath(self.startPoint)
        for i in range(1, len(self.points)):
            path.lineTo(self.points[i])
        self.setPath(path)
        if self.endGripItem:
            self.addGrabber()

    def updatePath(self):
        """ update path when svg item moves
        """
        path = QPainterPath(self.startPoint)
        self.updatePoints()

        for i in range(1, len(self.points) - 1):
            path.lineTo(self.points[i])
        path.lineTo(self.endPoint)
        self.setPath(path)

    def updatePoints(self):
        """
        updates points of line when grabber is moved
        :return:
        """
        if self.startGripItem.m_location in ["left", "right"]:
            point = self.points[1]
            self.points[1] = QPointF(point.x(), self.startPoint.y())
            if self.endGripItem.m_location in ["left", "right"]:
                point = self.points[len(self.points) - 2]
                self.points[len(self.points) - 2] = QPointF(point.x(), self.endPoint.y())
            else:
                point = self.points[len(self.points) - 2]
                self.points[len(self.points) - 2] = QPointF(self.endPoint.x(), point.y())

        else:
            point = self.points[1]
            self.points[1] = QPointF(self.startPoint.x(), point.y())
            if self.endGripItem.m_location in ["left", "right"]:
                point = self.points[len(self.points) - 2]
                self.points[len(self.points) - 2] = QPointF(point.x(), self.endPoint.y())
            else:
                point = self.points[len(self.points) - 2]
                self.points[len(self.points) - 2] = QPointF(self.endPoint.x(), point.y())

    def shape(self):
        """generates outline for path
        """
        qp = QPainterPathStroker()
        qp.setWidth(8)
        path = qp.createStroke(self.path())
        return path

    def paint(self, painter, option, widget):
        color = Qt.red if self.isSelected() else Qt.black
        painter.setPen(QPen(color, 2, self.penStyle))
        painter.drawPath(self.path())

        # To paint path of shape
        # painter.setPen(QPen(Qt.blue, 1, Qt.SolidLine))
        # painter.drawPath(self.shape())
        if self.isSelected():
            self.showGripItem()
            self._selected = True
        elif self._selected:
            self.hideGripItem()
            self._selected = False

    def movePoints(self, index, movement):
        """move points of line
        """
        for i in [index, index + 1]:
            point = self.points[i]
            point += movement
            self.points[i] = point
            self.updatePath()
        self.updateGrabber([index])

    def addGrabber(self):
        """adds grabber when line is moved
        """
        if self.startGripItem.m_location in ["left", "right"]:
            direction = [Qt.Horizontal, Qt.Vertical]
        else:
            direction = [Qt.Vertical, Qt.Horizontal]
        for i in range(1, len(self.points) - 2):
            item = Grabber(self, i, direction[i - 1])
            item.setParentItem(self)
            item.setPos(self.pos())
            self.scene().addItem(item)
            self.m_grabbers.append(item)

    def updateGrabber(self, index_no_updates=None):
        """updates all grabber of line when it is moved
        """
        index_no_updates = index_no_updates or []
        for grabber in self.m_grabbers:
            if grabber.m_index in index_no_updates: continue
            index = grabber.m_index
            startPoint = self.points[index]
            endPoint = self.points[index + 1]
            pos = (startPoint + endPoint) / 2
            grabber.setEnabled(False)
            grabber.setPos(pos)
            grabber.setEnabled(True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSceneHasChanged and self.scene():
            # self.addGrabber()
            # self.updateGrabber()
            return
        return super(Line, self).itemChange(change, value)

    def updateLine(self, startPoint=None, endPoint=None):

        """This function is used to update connecting line when it add on
           canvas and when it's grip item  moves
        :return:
        """
        self.prepareGeometryChange()
        if startPoint:
            self.startPoint = startPoint
        if endPoint:
            self.endPoint = endPoint
            self.createPath()
            self.updateGrabber()
            return

        if self.startGripItem and self.endGripItem:
            item = self.startGripItem
            self.startPoint = item.parentItem().mapToScene(item.pos())
            item = self.endGripItem
            self.endPoint = item.parentItem().mapToScene(item.pos())
            self.updatePath()
            self.updateGrabber()

    def removeFromCanvas(self):
        """This function is used to remove connecting line from canvas
        :return:
        """
        if self.scene():
            self.scene().removeItem(self)

    def showGripItem(self):
        """hides grip items which contains line
        """
        if self.startGripItem: self.startGripItem.show()
        if self.endGripItem: self.endGripItem.show()
        # for grabber in self.m_grabber:
        #     grabber.setSelected(True)

    def hideGripItem(self):
        """hides grip items which contains line
        """
        if self.startGripItem: self.startGripItem.hide()
        if self.endGripItem: self.endGripItem.hide()

    def setStartGripItem(self, item):
        self.startGripItem = item

    def setEndGripItem(self, item):
        self.endGripItem = item

    def setPenStyle(self, style):
        """change current pen style for line"""
        self.penStyle = style
