import math
from PyQt5.QtGui import QPen, QPainterPath, QBrush, QPainterPathStroker, QPainter, QCursor, QPolygonF
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem, QMenu, QGraphicsLineItem
from PyQt5.QtCore import Qt, QPointF, QRectF, QLineF, pyqtSignal

from collections import defaultdict

class Grabber(QGraphicsPathItem):
    """
    Extends QGraphicsPathItem to create grabber for line for moving a particular segment
    """
    circle = QPainterPath()
    circle.addEllipse(QRectF(-5, -5, 10, 10))

    def __init__(self, annotation_line, index, direction):
        super(Grabber, self).__init__()
        # store line to which it connects
        self.m_annotation_item = annotation_line
        # index of first point of segment of above line
        self.m_index = index
        self.direction = direction
        self.setPath(Grabber.circle)
        # set graphical settings for this item
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        # initially make invisible
        self.pen = QPen(Qt.white, -1, Qt.SolidLine)
        self.brush = QBrush(Qt.transparent)

    def itemChange(self, change, value):
        """ move position of grabber after resize"""
        if change == QGraphicsItem.ItemPositionChange and self.isEnabled():
            p = QPointF(self.pos())
            if self.direction == Qt.Horizontal:
                p.setX(value.x())
                if self.parentItem().refLine and self.m_index == len(self.parentItem().points) - 2:
                    points = self.parentItem().refLine.points
                    point1 = points[self.parentItem().refIndex]
                    point2 = points[self.parentItem().refIndex + 1]
                    point1 = self.parentItem().mapFromItem(self.parentItem().refLine, point1)
                    point2 = self.parentItem().mapFromItem(self.parentItem().refLine, point2)
                    if p.x() < min(point1.x(), point2.x()):
                        p.setX(min(point1.x(), point2.x()))
                    elif p.x() > max(point1.x(), point2.x()):
                        p.setX(max(point1.x(), point2.x()))
            elif self.direction == Qt.Vertical:
                p.setY(value.y())
                if self.parentItem().refLine and self.m_index == len(self.parentItem().points) - 2:
                    points = self.parentItem().refLine.points
                    point1 = points[self.parentItem().refIndex]
                    point2 = points[self.parentItem().refIndex + 1]
                    point1 = self.parentItem().mapFromItem(self.parentItem().refLine, point1)
                    point2 = self.parentItem().mapFromItem(self.parentItem().refLine, point2)
                    if p.y() < min(point1.y(), point2.y()):
                        p.setY(min(point1.y(), point2.y()))
                    elif p.y() > max(point1.y(), point2.y()):
                        p.setY(max(point1.y(), point2.y()))

            movement = p - self.pos()
            self.m_annotation_item.movePoints(self.m_index, movement)
            return p
        return super(Grabber, self).itemChange(change, value)

    def paint(self, painter, option, widget):
        """paints the path of grabber only if it is selected
        """
        if self.isSelected() and not self.m_annotation_item.isSelected():
            # show parent line of grabber
            self.m_annotation_item.setSelected(True)
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawPath(self.path())

    def shape(self):
        """Overrides shape method and set shape to segment on which grabber is located"""
        index = self.m_index
        # take start and end point of segment
        startPoint = QPointF(self.parentItem().points[index])
        endPoint = QPointF(self.parentItem().points[index + 1])
        # map in grabber's co-ordinate
        startPoint = self.mapFromParent(startPoint)
        endPoint = self.mapFromParent(endPoint)
        # create path as line
        path = QPainterPath(startPoint)
        path.lineTo(endPoint)
        # generate outlines for path
        stroke = QPainterPathStroker()
        stroke.setWidth(8)
        return stroke.createStroke(path)

    def boundingRect(self):
        return self.shape().boundingRect()

    def hoverEnterEvent(self, event):
        """
        Changes cursor to horizontal movement or vertical movement
         depending on the direction of the grabber on mouse enter
        """
        if self.direction == Qt.Horizontal:
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

    def show(self):
        # set pen to show
        self.pen = QPen(Qt.black, 2, Qt.SolidLine)
        self.brush = QBrush(Qt.cyan)

    def hide(self):
        # set pen to transparent
        self.pen = QPen(Qt.white, -1, Qt.SolidLine)
        self.brush = QBrush(Qt.transparent)


class LineLabel(QGraphicsTextItem):
    nameChanged = pyqtSignal()
    
    def __init__(self, pos, parent=None):
        super(LineLabel, self).__init__()
        # initial text
        self.setPlainText("abc")
        # stores index of first point of segment
        self.index = None
        # distance from line segment
        self.gap = None
        # set graphical setting
        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsFocusable)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        # set center of text label at mouse pos
        self.setPos(pos - self.boundingRect().center())
        self.setParentItem(parent)
        # add line item to test label
        self.line = QGraphicsLineItem()
        self.line.setParentItem(self)
        self.line.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        self.line.setFlag(QGraphicsItem.ItemStacksBehindParent)
        # reset position of line
        self.resetPos()
        self.values = defaultdict(lambda: 0)
        
    def paint(self, painter, option, widget):
        # draw ellipse shape
        painter.save()  # save painter
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))  # set pen to painter
        painter.setBrush(QBrush(Qt.white))  # set brush
        painter.drawEllipse(self.boundingRect())  # draw ellipse
        painter.restore()  # restore painter as before drawing ellipse
        super(LineLabel, self).paint(painter, option, widget)

    def updateLabel(self):
        # finds new position on segment
        offset = self.gap  # distance from segment
        points = self.parentItem().points  # points of line
        firstPoint = points[self.index]  # first point of segment on which label is attached
        endPoint = points[self.index + 1]  # second point
        center = self.mapToParent(self.boundingRect().center())
        newPos = center
        # if segment is vertical
        if firstPoint.x() == endPoint.x():
            newPos.setX(firstPoint.x() + self.gap)
            if min(firstPoint.y(), endPoint.y()) > newPos.y():
                newPos.setY(min(firstPoint.y(), endPoint.y()))
            elif newPos.y() > max(firstPoint.y(), endPoint.y()):
                newPos.setY(max(firstPoint.y(), endPoint.y()))
        # segment is horizontal
        elif firstPoint.y() == endPoint.y():
            newPos.setY(firstPoint.y() + self.gap)
            if min(firstPoint.x(), endPoint.x()) > newPos.x():
                newPos.setX(min(firstPoint.x(), endPoint.x()))
            elif newPos.x() > max(firstPoint.x(), endPoint.x()):
                newPos.setX(max(firstPoint.x(), endPoint.x()))
        # transfer center positon to top left
        newPos -= QPointF(self.boundingRect().width() / 2, self.boundingRect().height() / 2)
        self.setPos(newPos)

    def resetPos(self):
        """ finds the segment of line on which mouse is clicked for adding label
        and resets it's position on that segment
        """
        points = self.parentItem().points
        min_A = QPointF()
        min_B = QPointF()
        min_dis = math.inf
        for i in range(len(points) - 1):
            A = points[i]
            B = points[i + 1]
            C = QPointF(self.pos() + self.boundingRect().center())
            BAx = B.x() - A.x()
            BAy = B.y() - A.y()
            CAx = C.x() - A.x()
            CAy = C.y() - A.y()
            length = math.sqrt(BAx * BAx + BAy * BAy)
            if BAx == 0:
                if not min(A.y(), B.y()) <= C.y() <= max(A.y(), B.y()):
                    continue
            if BAy == 0:
                if not min(A.x(), B.x()) <= C.x() <= max(A.x(), B.x()):
                    continue
            if length > 0:
                dis = (BAx * CAy - CAx * BAy) / length
                if abs(dis) < abs(min_dis):
                    min_dis = dis
                    min_A = A
                    min_B = B
                    self.index = i
        point = self.mapFromScene(min_A)
        if min_A.x() == min_B.x():
            self.setPos(self.parentItem().mapFromScene(QPointF(min_A.x() + 10, self.y())))
            self.gap = 10 + self.boundingRect().width() / 2
        else:
            self.setPos(self.parentItem().mapFromScene(QPointF(self.x(), min_A.y() - 30)))
            self.gap = -30 + self.boundingRect().height() / 2

    def itemChange(self, change, value):
        # if position of label changes
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            newPos = QPointF(value)  # new position
            newPos += QPointF(self.boundingRect().width() / 2, self.boundingRect().height() / 2)  # pos of center
            points = self.parentItem().points
            firstPoint = points[self.index]
            endPoint = points[self.index + 1]
            if firstPoint.x() == endPoint.x():
                if min(firstPoint.y(), endPoint.y()) > newPos.y():
                    newPos.setY(min(firstPoint.y(), endPoint.y()))
                elif newPos.y() > max(firstPoint.y(), endPoint.y()):
                    newPos.setY(max(firstPoint.y(), endPoint.y()))
            elif firstPoint.y() == endPoint.y():
                if min(firstPoint.x(), endPoint.x()) > newPos.x():
                    newPos.setX(min(firstPoint.x(), endPoint.x()))
                elif newPos.x() > max(firstPoint.x(), endPoint.x()):
                    newPos.setX(max(firstPoint.x(), endPoint.x()))
            newPos -= QPointF(self.boundingRect().width() / 2,
                              self.boundingRect().height() / 2)  # change center pos to top-left
            return newPos
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            self.updateGap()
            self.updateLine()
            return
        return super(LineLabel, self).itemChange(change, value)

    def updateGap(self):
        # updates distance of line from it's connection segment
        points = self.parentItem().points
        firstPoint = points[self.index]
        endPoint = points[self.index + 1]
        firstPoint = self.mapFromParent(firstPoint)
        endPoint = self.mapFromParent(endPoint)
        center = self.boundingRect().center()
        if firstPoint.x() == endPoint.x():
            self.gap = center.x() - firstPoint.x()
        else:
            self.gap = center.y() - firstPoint.y()

    def updateLine(self):
        # updates line item of label
        points = self.parentItem().points
        firstPoint = points[self.index]
        endPoint = points[self.index + 1]
        point = self.mapFromParent(firstPoint)
        center = self.boundingRect().center()
        if firstPoint.x() == endPoint.x():
            self.line.setLine(center.x(), center.y(), point.x(), center.y())
        else:
            self.line.setLine(center.x(), center.y(), center.x(), point.y())

    def mouseDoubleClickEvent(self, event):
        # set text editable
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.setFocus()
        super(LineLabel, self).mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        super(LineLabel, self).focusOutEvent(event)
        self.setTextInteractionFlags(Qt.NoTextInteraction)  # set text non interactive
        self.nameChanged.emit()

    def __getstate__(self):
        return {
            "text": self.toPlainText(),
            "index": self.index,
            "gap": self.gap,
            "pos": (self.pos().x(), self.pos().y())
        }

    def __setstate__(self, dict):
        self.setPlainText(dict['text'])
        self.index = dict['index']
        self.gap = dict['gap']


def findIndex(line, pos):
    # finds index of first point of segment of line which is nearer to given position
    points = line.points
    min_A = QPointF()
    min_B = QPointF()
    min_dis = math.inf
    index = -1
    # iterating over points of line
    for i in range(len(points) - 1):
        A = points[i]
        B = points[i + 1]
        C = pos
        BAx = B.x() - A.x()
        BAy = B.y() - A.y()
        CAx = C.x() - A.x()
        CAy = C.y() - A.y()
        length = math.sqrt(BAx * BAx + BAy * BAy)  # length of segment
        if BAx == 0:
            if not min(A.y(), B.y()) <= C.y() <= max(A.y(), B.y()):
                continue
        if BAy == 0:
            if not min(A.x(), B.x()) <= C.x() <= max(A.x(), B.x()):
                continue
        if length > 0:
            dis = (BAx * CAy - CAx * BAy) / length
            if abs(dis) < abs(min_dis):
                min_dis = dis
                min_A = A
                min_B = B
                index = i
    return index


class Line(QGraphicsPathItem):
    """
    Extends QGraphicsPathItem to draw zig-zag line consisting of multiple points
    """

    def __init__(self, startPoint, endPoint, **args):
        QGraphicsItem.__init__(self, **args)
        # store startpoint and endpoint of line
        self.startPoint = startPoint
        self.endPoint = endPoint
        # stores all points of line
        self.points = []
        # stores grips of line
        self.startGripItem = None
        self.endGripItem = None
        self.m_grabbers = []
        # set graphical settings for line
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        # store reference if line connect another line
        self.refLine = None  # reference line
        self.refIndex = None  # start index of segment to which it connects
        self.commonPathsCenters = []
        self.midLines = []
        self.label = []
        # if line point on rectangle grip
        self.startGap = None # distance from center of start grip
        self.endGap = None # distance from center of end grip

    def boundingRect(self):
        # adjust bounding rect such that it contains intersection curve and arrow
        rect = self.shape().boundingRect()
        rect.adjust(-10, -10, 10, 10)
        return rect

    def advance(self, phase):
        """ called by scene when item moves or updates on scene
        """
        if not phase:
            return
        # fine collision with line in ascending order
        items = self.scene().items(self.shape(), Qt.IntersectsItemShape, Qt.AscendingOrder)
        self.commonPathsCenters = [] # remove all previous interaction
        # if item is line and stacked above
        for item in items:
            if type(item) in [type(self)]:
                if item == self:
                    break
                shape = item.shape() # shape of item
                shape = self.mapFromItem(item, item.shape()) # map shape to self
                commonPath = self.shape().intersected(shape) # find common path btw lines
                polygons = commonPath.toSubpathPolygons() # chane common path to polygon
                for polygon in polygons:
                    center = polygon.boundingRect().center() # center of polygon
                    # if collision is btw perpendicular line
                    if polygon.size() == 5:
                        # ignore collision if other line has end point on this line
                        if item.refLine:
                            i = len(item.points) - 2
                            x1, y1 = item.points[i].x(), item.points[i].y()
                            x2, y2 = item.points[i + 1].x(), item.points[i + 1].y()
                            x, y = center.x(), center.y()
                            if x == x1 == x2 and not min(y1, y2) + 8 <= y < max(y1, y2) - 8:
                                continue
                            elif y == y1 == y2 and not min(x1, x2) + 8 <= x < max(x1, x2) - 8:
                                continue
                            else:
                                self.commonPathsCenters.append(center)
                        else:
                            self.commonPathsCenters.append(center)
        self.update()

    def paint(self, painter, option, widget):
        color = Qt.red if self.isSelected() else Qt.black
        painter.setPen(QPen(color, 2, Qt.SolidLine))
        path = QPainterPath(self.startPoint) # start path
        # iterating over all points of line
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i].x(), self.points[i].y()
            x2, y2 = self.points[i + 1].x(), self.points[i + 1].y()
            for point in sorted(self.commonPathsCenters, key=lambda x: x.x() + x.y(), reverse=x2 < x1 or y2 < y1):
                x, y = point.x(), point.y()
                if x == x1 == x2:
                    # vertical
                    if min(y1, y2) + 8 <= y < max(y1, y2) - 8:
                        if y2 > y1:
                            path.lineTo(point - QPointF(0, 8))
                            path.arcTo(QRectF(x - 8, y - 8, 16, 16), 90, -180)
                            path.moveTo(point + QPointF(0, 8))
                        else:
                            path.lineTo(point + QPointF(0, 8))
                            path.arcTo(QRectF(x - 8, y - 8, 16, 16), -90, 180)
                            path.moveTo(point - QPointF(0, 8))
                elif y == y1 == y2:
                    # horizontal
                    if min(x1, x2) + 8 <= x < max(x1, x2) - 8:
                        if x2 > x1:
                            path.lineTo(point - QPointF(8, 0))
                            path.arcTo(QRectF(x - 8, y - 8, 16, 16), 180, 180)
                            path.moveTo(point + QPointF(8, 0))
                        else:
                            path.lineTo(point + QPointF(8, 0))
                            path.arcTo(QRectF(x - 8, y - 8, 16, 16), 0, -180)
                            path.lineTo(point - QPointF(8, 0))
            path.lineTo(self.points[i + 1])
            # draw arrow in last segment
            if i == len(self.points) - 2:
                arrow_size = 20.0
                line = QLineF(self.points[i], self.points[i + 1])
                if line.length() < 20:
                    continue
                angle = math.acos(line.dx() / line.length())

                if line.dy() >= 0:
                    angle = (math.pi * 2) - angle

                arrow_p1 = line.p2() - QPointF(math.sin(angle + math.pi / 2.5) * arrow_size,
                                               math.cos(angle + math.pi / 2.5) * arrow_size)

                arrow_p2 = line.p2() - QPointF(math.sin(angle + math.pi - math.pi / 2.5) * arrow_size,
                                               math.cos(angle + math.pi - math.pi / 2.5) * arrow_size)

                arrowHead = QPolygonF()
                arrowHead.append(line.p2())
                arrowHead.append(arrow_p1)
                arrowHead.append(arrow_p2)
                painter.save()
                painter.setBrush(Qt.black)
                painter.drawPolygon(arrowHead)
                painter.restore()

        painter.drawPath(path) # draw final path

    def createPath(self):
        """
        creates initial path and stores it's points
        :return:
        """
        offset = 30
        x0, y0 = self.startPoint.x(), self.startPoint.y()
        x1, y1 = self.endPoint.x(), self.endPoint.y()
        # create path for line in process
        self.points = [self.startPoint, QPointF((x0 + x1) / 2, y0), QPointF((x0 + x1) / 2, y1), self.endPoint]
        # final path of line
        if self.refLine:
            # line has end point on other line
            from .shapes import LineGripItem
            direction = "left"
            points = self.refLine.points
            point1 = points[self.refIndex]
            point2 = points[self.refIndex + 1]
            if point1.x() == point2.x():
                if point1.x() < self.startPoint.x():
                    direction = "right"
                else:
                    direction = "left"
            elif point1.y() == point2.y():
                if point1.y() > self.startPoint.y():
                    direction = "top"
                else:
                    direction = "bottom"
            self.endGripItem = LineGripItem(-1, [0, 0, direction], self)
            self.endGripItem.setPos(self.endPoint)

        if self.startGripItem and self.endGripItem:
            # determine ns (point next to start)
            item = self.startGripItem
            if item.m_location == "top":
                ns = QPointF(self.startPoint.x(), self.startPoint.y() - offset)
            elif item.m_location == "left":
                ns = QPointF(self.startPoint.x() - offset, self.startPoint.y())
            elif item.m_location == "bottom":
                ns = QPointF(self.startPoint.x(), self.startPoint.y() + offset)
            else:
                ns = QPointF(self.startPoint.x() + offset, self.startPoint.y())
            # determine pe (point previous to end)
            item = self.endGripItem
            if item.m_location == "top":
                pe = QPointF(self.endPoint.x(), self.endPoint.y() - offset)
            elif item.m_location == "left":
                pe = QPointF(self.endPoint.x() - offset, self.endPoint.y())
            elif item.m_location == "bottom":
                pe = QPointF(self.endPoint.x(), self.endPoint.y() + offset)
            else:
                pe = QPointF(self.endPoint.x() + offset, self.endPoint.y())
            start = self.startPoint
            end = self.endPoint
            sitem = self.startGripItem.mapRectToScene(self.startGripItem.parentItem().boundingRect())
            eitem = self.endGripItem.mapRectToScene(self.endGripItem.parentItem().boundingRect())
            if self.refLine:
                eitem = self.endGripItem.mapRectToScene(QRectF(0, 0, 0, 0))

            if self.startGripItem.m_location in ["right"]:
                if self.endGripItem.m_location in ["top"]:
                    if start.x() + offset < end.x():
                        if start.y() + offset < end.y():
                            self.points = [start, QPointF(end.x(), start.y()), end]
                        else:
                            if start.x() + offset < eitem.left() - offset:
                                self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                            else:
                                x = max(eitem.right() + offset, ns.x())
                                self.points = [start, QPointF(x, start.y()), QPointF(x, pe.y()), pe, end]

                    elif sitem.left() > end.x():
                        if sitem.bottom() + offset < end.y():
                            self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                        elif sitem.top() - offset < end.y():
                            self.points = [start, ns, QPointF(ns.x(), sitem.top() - offset),
                                           QPointF(pe.x(), sitem.top() - offset), end]
                        else:
                            self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                    else:
                        self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                        if start.y() > end.y():
                            x = max(eitem.right() + offset, ns.x())
                            self.points = [start, QPointF(x, start.y()), QPointF(x, pe.y()), pe, end]

                elif self.endGripItem.m_location in ["bottom"]:
                    if start.x() + offset < eitem.left():
                        if start.y() - offset < end.y():
                            self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                        else:
                            self.points = [start, QPointF(end.x(), start.y()), end]

                    elif sitem.left() > end.x():
                        if sitem.bottom() + offset < end.y():
                            self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                        elif sitem.top() - offset < end.y():
                            y = max(pe.y(), sitem.bottom() + offset)
                            self.points = [start, ns, QPointF(ns.x(), y),
                                           QPointF(pe.x(), y), end]
                        else:
                            self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                    else:
                        self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                        if start.y() < end.y():
                            x = max(eitem.right() + offset, ns.x())
                            self.points = [start, QPointF(x, start.y()), QPointF(x, pe.y()), pe, end]

                elif self.endGripItem.m_location in ["right"]:
                    x = max(start.x() + offset, pe.x())
                    self.points = [start, QPointF(x, start.y()), QPointF(x, end.y()), end]
                    if start.x() + offset < eitem.top():
                        if start.y() + offset > eitem.top() and end.y() >= start.y():
                            self.points = [start, ns, QPointF(ns.x(), eitem.top()),
                                           QPointF(pe.x(), eitem.top()), pe, end]
                        elif start.y() - offset < eitem.bottom() and end.y() <= start.y():
                            self.points = [start, ns, QPointF(ns.x(), eitem.bottom()),
                                           QPointF(pe.x(), eitem.bottom()), pe, end]
                    elif sitem.top() - offset < end.y() < sitem.bottom() + offset:
                        if end.y() < start.y():
                            self.points = [start, ns, QPointF(ns.x(), sitem.top()),
                                           QPointF(pe.x(), sitem.top()), pe, end]
                        else:
                            self.points = [start, ns, QPointF(ns.x(), sitem.bottom()),
                                           QPointF(pe.x(), sitem.bottom()), pe, end]

                elif self.endGripItem.m_location in ["left"]:
                    self.points = [start, QPointF((start.x() + end.x()) / 2, start.y()),
                                   QPointF((start.x() + end.x()) / 2, end.y()), end]
                    if end.x() < start.x() + offset:
                        if eitem.bottom() <= sitem.top() - offset:
                            self.points = [start, ns, QPointF(ns.x(), sitem.top()),
                                           QPointF(pe.x(), sitem.top()), pe, end]
                        elif eitem.top() >= sitem.bottom() + offset:
                            self.points = [start, ns, QPointF(ns.x(), sitem.bottom()),
                                           QPointF(pe.x(), sitem.bottom()), pe, end]
                        elif end.y() <= start.y():
                            y = min(eitem.top(), sitem.top())
                            self.points = [start, ns, QPointF(ns.x(), y),
                                           QPointF(pe.x(), y), pe, end]
                        else:
                            y = max(eitem.bottom(), sitem.bottom())
                            self.points = [start, ns, QPointF(ns.x(), y),
                                           QPointF(pe.x(), y), pe, end]


            elif self.startGripItem.m_location in ["left"]:
                if self.endGripItem.m_location in ["top"]:
                    if start.x() + offset < eitem.left():
                        if end.y() > sitem.bottom() + offset:
                            self.points = [start, ns, QPointF(ns.x(), sitem.bottom()),
                                           QPointF(pe.x(), sitem.bottom()), end]
                        else:
                            y = min(sitem.top(), pe.y())
                            self.points = [start, ns, QPointF(ns.x(), y),
                                           QPointF(pe.x(), y), end]
                    elif eitem.right() >= start.x() - offset:
                        x = min(ns.x(), eitem.left())
                        self.points = [start, QPointF(x, ns.y()),
                                       QPointF(x, pe.y()), pe, end]
                    else:
                        if end.y() >= start.y() + offset:
                            self.points = [start, QPointF(end.x(), start.y()), end]
                        else:
                            x = (start.x() + end.x()) / 2
                            self.points = [start, QPointF(x, start.y()),
                                           QPointF(x, pe.y()), pe, end]

                elif self.endGripItem.m_location in ["bottom"]:
                    if start.x() + offset < eitem.left():
                        if end.y() < sitem.top() - offset:
                            self.points = [start, ns, QPointF(ns.x(), sitem.top()),
                                           QPointF(pe.x(), sitem.top()), end]
                        else:
                            y = max(sitem.bottom(), pe.y())
                            self.points = [start, ns, QPointF(ns.x(), y),
                                           QPointF(pe.x(), y), end]
                    elif eitem.right() >= start.x() - offset:
                        x = min(ns.x(), eitem.left())
                        self.points = [start, QPointF(x, ns.y()),
                                       QPointF(x, pe.y()), pe, end]
                    else:
                        if end.y() <= start.y() - offset:
                            self.points = [start, QPointF(end.x(), start.y()), end]
                        else:
                            x = (start.x() + end.x()) / 2
                            self.points = [start, QPointF(x, start.y()),
                                           QPointF(x, pe.y()), pe, end]

                elif self.endGripItem.m_location in ["right"]:
                    self.points = [start, QPointF((start.x() + end.x()) / 2, start.y()),
                                   QPointF((start.x() + end.x()) / 2, end.y()), end]
                    if end.x() > start.x() + offset:
                        if eitem.bottom() <= sitem.top() - offset:
                            self.points = [start, ns, QPointF(ns.x(), sitem.top()),
                                           QPointF(pe.x(), sitem.top()), pe, end]
                        elif eitem.top() >= sitem.bottom() + offset:
                            self.points = [start, ns, QPointF(ns.x(), sitem.bottom()),
                                           QPointF(pe.x(), sitem.bottom()), pe, end]
                        elif end.y() <= start.y():
                            y = min(eitem.top(), sitem.top())
                            self.points = [start, ns, QPointF(ns.x(), y),
                                           QPointF(pe.x(), y), pe, end]
                        else:
                            y = max(eitem.bottom(), sitem.bottom())
                            self.points = [start, ns, QPointF(ns.x(), y),
                                           QPointF(pe.x(), y), pe, end]

                elif self.endGripItem.m_location in ["left"]:
                    self.points = [start, QPointF(pe.x(), start.y()), pe, end]
                    if start.x() + offset < end.x():
                        self.points = [start, ns, QPointF(ns.x(), end.y()), end]
                        if sitem.bottom() + offset > end.y() > sitem.top() - offset:
                            self.points = [start, ns, QPointF(ns.x(), sitem.top()),
                                           QPointF(pe.x(), sitem.top()), pe, end]
                    elif eitem.top() - offset < start.y() < eitem.bottom() + offset:
                        if end.y() > start.y():
                            self.points = [start, ns, QPointF(ns.x(), eitem.top()),
                                           QPointF(pe.x(), eitem.top()), pe, end]
                        else:
                            self.points = [start, ns, QPointF(ns.x(), eitem.bottom()),
                                           QPointF(pe.x(), eitem.bottom()), pe, end]


            elif self.startGripItem.m_location in ["top"]:
                if self.endGripItem.m_location in ["top"]:
                    self.points = [self.startPoint, QPointF(start.x(), pe.y()),
                                   pe, self.endPoint]
                    if start.y() < end.y():
                        self.points = [self.startPoint, ns, QPointF(pe.x(), ns.y()), self.endPoint]
                    if sitem.right() > end.x() > sitem.left() or eitem.right() > start.x() > eitem.left():
                        x = max(sitem.right(), eitem.right())
                        x += offset
                        if start.x() > end.x():
                            x = min(sitem.left(), eitem.left())
                            x -= offset
                        self.points = [start, ns, QPointF(x, ns.y()),
                                       QPointF(x, pe.y()), pe, end]

                elif self.endGripItem.m_location in ["bottom"]:
                    self.points = [self.startPoint, ns, QPointF((x0 + x1) / 2, ns.y()), QPointF((x0 + x1) / 2, pe.y()),
                                   pe, self.endPoint]
                    if start.y() - offset > end.y():
                        self.points = [start, QPointF(start.x(), (y0 + y1) / 2), QPointF(end.x(), (y0 + y1) / 2),
                                       self.endPoint]
                    elif sitem.right() > end.x() > sitem.left() or eitem.right() > start.x() > eitem.left():
                        x = max(sitem.right(), eitem.right())
                        x += offset
                        if start.x() > end.x():
                            x = min(sitem.left(), eitem.left())
                            x -= offset
                        self.points = [start, ns, QPointF(x, ns.y()),
                                       QPointF(x, pe.y()), pe, end]

                elif self.endGripItem.m_location in ["right"]:
                    y = min(ns.y(), eitem.bottom() + offset)
                    self.points = [start, QPointF(ns.x(), y), QPointF(pe.x(), y), pe, end]
                    if sitem.left() - offset < end.x() < sitem.right() + offset and end.y() > start.y() + offset:
                        self.points = [start, ns, QPointF(sitem.right() + offset, ns.y()),
                                       QPointF(sitem.right() + offset, pe.y()), end]
                    elif eitem.top() < start.y() - offset < eitem.bottom():
                        self.points = [start, ns, QPointF(start.x(), eitem.top()),
                                       QPointF(pe.x(), eitem.top()), pe, end]

                elif self.endGripItem.m_location in ["left"]:
                    y = min(ns.y(), eitem.bottom() + offset)
                    self.points = [start, QPointF(ns.x(), y), QPointF(pe.x(), y), pe, end]
                    if sitem.left() - offset < end.x() < sitem.right() + offset and end.y() > start.y() + offset:
                        self.points = [start, ns, QPointF(sitem.left() - offset, ns.y()),
                                       QPointF(sitem.left() - offset, pe.y()), end]
                    elif eitem.top() < start.y() - offset < eitem.bottom():
                        self.points = [start, QPointF(start.x(), eitem.top()),
                                       QPointF(pe.x(), eitem.top()), pe, end]

            elif self.startGripItem.m_location in ["bottom"]:
                if self.endGripItem.m_location in ["top"]:
                    self.points = [self.startPoint, ns, QPointF((x0 + x1) / 2, ns.y()), QPointF((x0 + x1) / 2, pe.y()),
                                   pe, self.endPoint]
                    if start.y() < end.y():
                        self.points = [self.startPoint, ns, QPointF(pe.x(), ns.y()), self.endPoint]
                    if sitem.right() > end.x() > sitem.left() or eitem.right() > start.x() > eitem.left():
                        x = max(sitem.right(), eitem.right())
                        x += offset
                        self.points = [start, ns, QPointF(x, ns.y()),
                                       QPointF(x, pe.y()), pe, end]

                elif self.endGripItem.m_location in ["bottom"]:
                    self.points = [self.startPoint, ns, QPointF((x0 + x1) / 2, ns.y()), QPointF((x0 + x1) / 2, pe.y()),
                                   pe, self.endPoint]
                    if sitem.right() > end.x() > sitem.left() or eitem.right() > start.x() > eitem.left():
                        x = max(sitem.right(), eitem.right())
                        x += offset
                        self.points = [start, ns, QPointF(x, ns.y()),
                                       QPointF(x, pe.y()), pe, end]

                elif self.endGripItem.m_location in ["right"]:
                    y = max(ns.y(), eitem.bottom() + offset)
                    self.points = [start, QPointF(ns.x(), y), QPointF(pe.x(), y), pe, end]
                    if sitem.left() - offset < end.x() < sitem.right() + offset:
                        self.points = [start, ns, QPointF(sitem.right() + offset, ns.y()),
                                       QPointF(sitem.right() + offset, pe.y()), end]

                elif self.endGripItem.m_location in ["left"]:
                    y = max(ns.y(), eitem.bottom() + offset)
                    self.points = [start, QPointF(ns.x(), y), QPointF(pe.x(), y), pe, end]
                    if sitem.left() - offset < end.x() < sitem.right() + offset:
                        self.points = [start, ns, QPointF(sitem.left() - offset, ns.y()),
                                       QPointF(sitem.left() - offset, pe.y()), end]

        # path of line
        path = QPainterPath(self.startPoint)
        for i in range(1, len(self.points)):
            path.lineTo(self.points[i])
        self.setPath(path)

        if self.refLine:
            # remove added grip
            self.scene().removeItem(self.endGripItem)
            self.endGripItem = None
            self.addGrabber()
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
        # update grabber of line
        self.updateGrabber()
        # update labels connected to line
        for label in self.label:
            label.updateLabel()
        # update line have end point on this line
        self.updateMidLines()

    def updatePoints(self):
        """
        updates points of line when grabber is moved
        :return:
        """
        if self.startGripItem:
            self.points[0] = self.startPoint
            point = self.points[1]
            if self.startGripItem.m_location in ["left", "right"]:
                self.points[1] = QPointF(point.x(), self.startPoint.y())
            else:
                self.points[1] = QPointF(self.startPoint.x(), point.y())

        if self.endGripItem:
            self.points[len(self.points) - 1] = self.endPoint
            point = self.points[len(self.points) - 2]
            if self.endGripItem.m_location in ["left", "right"]:
                self.points[len(self.points) - 2] = QPointF(point.x(), self.endPoint.y())
            else:
                self.points[len(self.points) - 2] = QPointF(self.endPoint.x(), point.y())

        if self.refLine:
            self.endPoint = self.points[len(self.points) - 1]

    def shape(self):
        """generates outline for path
        """
        qp = QPainterPathStroker()
        qp.setWidth(8)
        path = qp.createStroke(self.path())
        return path

    def movePoints(self, index, movement):
        """move points of line
        """
        for i in [index, index + 1]:
            point = self.points[i]
            point += movement
            self.points[i] = point
        self.updatePath()

    def addGrabber(self):
        """adds grabber when line is moved
        """
        for grabber in self.m_grabbers:
            self.scene().removeItem(grabber)
        if self.endGripItem:
            count = range(1, len(self.points) - 2)
        else:
            count = range(1, len(self.points) - 1)
        for i in count:
            if self.points[i].x() == self.points[i + 1].x():
                direction = Qt.Horizontal
            else:
                direction = Qt.Vertical
            item = Grabber(self, i, direction)
            item.setParentItem(self)
            item.setPos(self.pos())
            self.m_grabbers.append(item)

    def updateGrabber(self, index_no_updates=None):
        """updates all grabber of line when it is moved
        """
        index_no_updates = index_no_updates or []
        for grabber in self.m_grabbers:
            if grabber.m_index in index_no_updates or grabber.isSelected(): continue
            index = grabber.m_index
            startPoint = self.points[index]
            endPoint = self.points[index + 1]
            pos = (startPoint + endPoint) / 2
            grabber.setEnabled(False)
            grabber.setPos(pos)
            grabber.setEnabled(True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            # on selection stack above to show curve on it
            if value == 1:
                self.showGripItem()
                items = self.collidingItems(Qt.IntersectsItemShape)
                for item in items:
                    if type(item) == type(self):
                        item.stackBefore(self)
                self.scene().update()
            else:
                self.hideGripItem()
            return
        if change == QGraphicsItem.ItemSceneHasChanged and not self.scene():
            # if line is removed from scene
            for line in self.midLines:
                # remove lines connected to it
                if line.scene():
                    line.scene().removeItem(line)
            if self.startGripItem and self.startGripItem.lines and not self.startGripItem.tempLine:
                # remove line reference from grips
                if self in self.startGripItem.lines: self.startGripItem.lines.remove(self)
                if self.endGripItem and self.endGripItem.lines:
                    if self in self.endGripItem.lines: self.endGripItem.lines.remove(self)
                if self.refLine:
                    if self in self.refLine.midLines: self.refLine.midLines.remove(self)

        return super(Line, self).itemChange(change, value)

    def updateLine(self, endPoint=None):

        """This function is used to update connecting line when it add on
           canvas and when it's grip item  moves
        :return:
        """
        if endPoint:
            self.endPoint = endPoint
            self.createPath()
            self.updateGrabber()
            return
        # update start point
        if self.startGripItem:
            item = self.startGripItem
            startPoint = item.parentItem().mapToScene(item.pos()) # center of grip
            # end grip is rectangle
            if item.size and item.m_location in ["top", "bottom"]:
                startPoint.setX(startPoint.x() - self.startGap * item.boundingRect().width())
            elif item.size:
                startPoint.setY(
                    startPoint.y() - self.startGap * item.boundingRect().height())
            self.startPoint = startPoint
        # end point on line
        if self.endGripItem:
            item = self.endGripItem
            endPoint = item.parentItem().mapToScene(item.pos()) # center of grip
            # end grip is rectangle
            if item.size and item.m_location in ["top", "bottom"]:
                endPoint.setX(
                    endPoint.x() - self.endGap * item.boundingRect().width())
            elif item.size:
                endPoint.setY(
                    endPoint.y() - self.endGap * item.boundingRect().height())
            self.endPoint = endPoint
            self.updatePath()
        # end point on other line
        elif self.refLine:
            self.updatePath()

    def updateMidLines(self):
        """ Updates all lines connecting to it
        """
        for line in self.midLines:
            points = line.refLine.points
            point1 = points[line.refIndex]
            point2 = points[line.refIndex + 1]
            i = len(line.points) - 1
            if point1.x() == point2.x():
                line.points[i].setX(point1.x())
                if line.points[i].y() < min(point1.y(), point2.y()):
                    line.points[i].setY(min(point1.y(), point2.y()))
                    line.points[i - 1].setY(min(point1.y(), point2.y()))
                elif line.points[i].y() > max(point1.y(), point2.y()):
                    line.points[i].setY(max(point1.y(), point2.y()))
                    line.points[i - 1].setY(max(point1.y(), point2.y()))
            elif point1.y() == point2.y():
                line.points[i].setY(point1.y())
                if line.points[i].x() < min(point1.x(), point2.x()):
                    line.points[i].setX(min(point1.x(), point2.x()))
                    line.points[i - 1].setX(min(point1.x(), point2.x()))
                elif line.points[i].x() > max(point1.x(), point2.x()):
                    line.points[i].setX(max(point1.x(), point2.x()))
                    line.points[i - 1].setX(max(point1.x(), point2.x()))
            line.updatePath()

    def showGripItem(self):
        """shows grip items which contains line
        """
        if self.startGripItem: self.startGripItem.show()
        if self.endGripItem: self.endGripItem.show()
        for grabber in self.m_grabbers:
            grabber.show()

    def hideGripItem(self):
        """hides grip items which contains line
        """
        if self.startGripItem: self.startGripItem.hide()
        if self.endGripItem: self.endGripItem.hide()
        for grabber in self.m_grabbers:
            grabber.hide()

    def setStartGripItem(self, item):
        self.startGripItem = item

    def setEndGripItem(self, item):
        self.endGripItem = item

    def contextMenuEvent(self, event):
        """Pop up menu
        :return:
        """
        # create a menu and add action
        contextMenu = QMenu()
        addLableAction = contextMenu.addAction("Add Text Label")  # add action for text label
        action = contextMenu.exec_(event.screenPos())
        # check for label action and add text label as child
        if action == addLableAction:
            label = LineLabel(event.scenePos(), self)
            self.label.append(label)  # text label as child
            self.scene().labelAdded.emit(label)

    def __getstate__(self):
        return {
            "_classname_": self.__class__.__name__,
            "startPoint": (self.startPoint.x(), self.startPoint.y()),
            "endPoint": (self.endPoint.x(), self.endPoint.y()),
            "points": [(point.x(), point.y()) for point in self.points],
            "startGripItem": hex(id(self.startGripItem)),
            "endGripItem": hex(id(self.endGripItem)) if self.endGripItem else 0,
            "refLine": hex(id(self.refLine)) if self.refLine else 0,
            "refIndex": self.refIndex,
            "label": [i for i in self.label],
            "id": hex(id(self))
        }

    def __setstate__(self, dict):
        self.points = [QPointF(x, y) for x, y in dict["points"]]
