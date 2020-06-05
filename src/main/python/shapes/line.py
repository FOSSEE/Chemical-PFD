import math
from PyQt5.QtGui import QPen, QPainterPath, QBrush, QPainterPathStroker, QPainter, QCursor
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem
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
        self.pen = QPen(Qt.white, -1, Qt.SolidLine)
        self.brush = QBrush(Qt.transparent)

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
        if self.isSelected() and not self.m_annotation_item.isSelected() :
            # show parent line of grabber
            self.m_annotation_item.setSelected(True)
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
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

    def show(self):
        self.pen = QPen(Qt.black, 2, Qt.SolidLine)
        self.brush = QBrush(Qt.cyan)

    def hide(self):
        self.pen = QPen(Qt.white, -1, Qt.SolidLine)
        self.brush = QBrush(Qt.transparent)

class LineLabel(QGraphicsTextItem):
    def __init__(self, parent=None):
        super(LineLabel, self).__init__(parent=parent)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setPlainText("abc")

    def paint(self, painter, option, widget):
        super(LineLabel, self).paint(painter,option,widget)
        painter.drawEllipse(self.boundingRect())

    def updateLabel(self):
        points = self.parentItem().points
        # min_A = QPointF()
        # min_B =QPointF()
        # min_dis =math.inf
        # for i in range(1, len(points)):
        #     A = points[i - 1]
        #     B = points[i]
        #     C = self.pos()
        #     BAx = B.x() - A.x()
        #     BAy = B.y() - A.y()
        #     CAx = C.x() - A.x()
        #     CAy = C.y() - A.y()
        #     length = math.sqrt(BAx * BAx + BAy * BAy)
        #     if length >0:
        #         dis = (BAx*CAy - CAx*BAy)/length
        #         if abs(dis) < abs(min_dis):
        #             min_dis=dis
        #             min_A=A
        #             min_B=B
        #
        # self.setPos(self.parentItem().mapFromScene(QPointF(min_A)))
        # print(self.pos())

    def itemChange(self, change, value):
        # if change == QGraphicsItem.ItemPositionChange:
        #     print("label change", change, value)
        return super(LineLabel, self).itemChange(change,value)


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
        self.commonPaths=[]
        self.label = LineLabel(self)

    def advance(self, phase):
        # items = self.collidingItems(Qt.IntersectsItemShape)
        items = self.scene().items(self.shape(),Qt.IntersectsItemShape,Qt.AscendingOrder)
        self.commonPaths = []
        for item in items:
            if type(item) in [type(self)]:
                if item == self:
                    break
                shape = item.shape()
                shape = self.mapFromItem(item, item.shape())
                commonPath = self.shape().intersected(shape)
                polygons = commonPath.toSubpathPolygons()
                for polygon in polygons:
                    center = polygon.boundingRect().center()
                    self.commonPaths.append(center)
                
                # self.commonPaths[commonPath] = item
        print(self.commonPaths)
        self.update()
    
    def paint(self, painter, option, widget):
        color = Qt.red if self.isSelected() else Qt.black
        painter.setPen(QPen(color, 2, self.penStyle))
        # path = self.path()
        # painter.drawPath(path)
        path = QPainterPath(self.startPoint)
        # iterating over all points of line
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i].x(), self.points[i].y()
            x2, y2 = self.points[i+1].x(), self.points[i+1].y()
            for point in sorted(self.commonPaths, key = lambda x: x.x() + x.y(), reverse=x2<x1 or y2<y1):
                x, y = point.x(), point.y()
                # if not x1 * (y - y2) + x * (y2 - y1) + x2 * (y1 - y) :
                if x == x1 == x2:
                    #vertical
                    if min(y1, y2) <= y < max(y1, y2):
                        if y2>y1:
                            path.lineTo(point - QPointF(0, 8))
                            path.arcTo(QRectF(x-8, y-8, 16, 16), 90, -180)
                            path.moveTo(point + QPointF(0, 8))
                        else:
                            path.lineTo(point + QPointF(0, 8))
                            path.arcTo(QRectF(x-8, y-8, 16, 16), -90, 180)
                            path.moveTo(point - QPointF(0, 8))
                elif y == y1 == y2:
                    #horizontal
                    if min(x1, x2) <= x < max(x1, x2):
                        if x2>x1:
                            path.lineTo(point - QPointF(8, 0))
                            path.arcTo(QRectF(x-8, y-8, 16, 16), 180, 180)
                            path.moveTo(point + QPointF(8, 0))
                        else:
                            path.lineTo(point + QPointF(8, 0))
                            path.arcTo(QRectF(x-8, y-8, 16, 16), 0, -180)
                            path.lineTo(point - QPointF(8, 0))
            path.lineTo(self.points[i+1])
                
        painter.drawPath(path)




    def createPath(self):
        """
        creates initial path and stores it's points
        :return:
        """
        offset = 30
        x0, y0 = self.startPoint.x(), self.startPoint.y()
        x1, y1 = self.endPoint.x(), self.endPoint.y()
        # create line is in process
        self.points = [self.startPoint, QPointF((x0 + x1) / 2, y0), QPointF((x0 + x1) / 2, y1), self.endPoint]
        # final path of line
        if self.startGripItem and self.endGripItem:
            # determine ns (point next to start)
            item = self.startGripItem
            self.startPoint = item.parentItem().mapToScene(item.pos())
            if item.m_location == "top":
                ns = QPointF(self.startPoint.x(), self.startPoint.y() - offset)
            elif item.m_location == "left":
                ns = QPointF(self.startPoint.x() - offset, self.startPoint.y())
            elif item.m_location == "bottom":
                ns = QPointF(self.startPoint.x(), self.startPoint.y() + offset)
            else:
                ns = QPointF(self.startPoint.x() + offset, self.startPoint.y())
            # pe (point previous to end)
            item = self.endGripItem
            self.endPoint = item.parentItem().mapToScene(item.pos())
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
            sheight = self.startGripItem.m_annotation_item.boundingRect().height() / 2
            swidth = self.startGripItem.m_annotation_item.boundingRect().width() / 2
            eheight = self.endGripItem.m_annotation_item.boundingRect().height() / 2
            ewidth = self.endGripItem.m_annotation_item.boundingRect().width() / 2

            if self.startGripItem.m_location in ["right"]:
                if self.endGripItem.m_location in ["top"]:
                    if start.x() + offset < end.x() - ewidth:
                        if start.y() + offset < end.y():
                            self.points = [start, QPointF(end.x(), start.y()), end]
                        else:
                            self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                    elif start.x() - 2 * swidth > end.x():
                        if start.y() + sheight + offset < end.y():
                            self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                        elif start.y() - sheight - offset < end.y():
                            self.points = [start, ns, QPointF(ns.x(), ns.y() - sheight - offset),
                                           QPointF(pe.x(), ns.y() - sheight - offset), end]
                        else:
                            self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                    else:
                        self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                        if start.y() > end.y():
                            x = max(end.x() + ewidth + offset, ns.x())
                            self.points = [start, QPointF(x, start.y()), QPointF(x, pe.y()), pe, end]

                elif self.endGripItem.m_location in ["bottom"]:
                    if start.x() + offset < end.x() - ewidth:
                        if start.y() + offset < end.y():
                            self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                        else:
                            self.points = [start, QPointF(end.x(), start.y()), end]

                    elif start.x() - 2 * swidth > end.x():
                        if start.y() + sheight + offset < end.y():
                            self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                        elif start.y() - sheight - offset < end.y():
                            y = max(pe.y(), start.y() + sheight + offset)
                            self.points = [start, ns, QPointF(ns.x(), y),
                                           QPointF(pe.x(), y), end]
                        else:
                            self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                    else:
                        self.points = [start, ns, QPointF(ns.x(), pe.y()), pe, end]
                        if start.y() < end.y():
                            x = max(end.x() + ewidth + offset, ns.x())
                            self.points = [start, QPointF(x, start.y()), QPointF(x, pe.y()), pe, end]

                elif self.endGripItem.m_location in ["right"]:
                    x = max(start.x() + offset, pe.x())
                    self.points = [start, QPointF(x, start.y()), QPointF(x, end.y()), end]
                    if start.x() + offset < end.x() - ewidth:
                        if start.y() + offset > end.y() - eheight and end.y() >= start.y():
                            self.points = [start, ns, QPointF(ns.x(), pe.y() - eheight),
                                           QPointF(pe.x(), pe.y() - eheight), pe, end]
                        elif start.y() - offset < end.y() + eheight and end.y() <= start.y():
                            self.points = [start, ns, QPointF(ns.x(), pe.y() + eheight),
                                           QPointF(pe.x(), pe.y() + eheight), pe, end]
                    elif start.y() - sheight - offset < end.y() < start.y() + sheight + offset:
                        if end.y() < start.y():
                            self.points = [start, ns, QPointF(ns.x(), ns.y() - sheight),
                                           QPointF(pe.x(), ns.y() - sheight), pe, end]
                        else:
                            self.points = [start, ns, QPointF(ns.x(), ns.y() + sheight),
                                           QPointF(pe.x(), ns.y() + sheight), pe, end]

                elif self.endGripItem.m_location in ["left"]:
                    self.points = [start, QPointF((start.x() + end.x()) / 2, start.y()),
                                   QPointF((start.x() + end.x()) / 2, end.y()), end]
                    if end.x() < start.x() + offset:
                        if end.y() + eheight <= start.y() - sheight - offset:
                            self.points = [start, ns, QPointF(ns.x(), ns.y() - sheight),
                                           QPointF(pe.x(), ns.y() - sheight), pe, end]
                        elif end.y() - eheight >= start.y() + sheight + offset:
                            self.points = [start, ns, QPointF(ns.x(), ns.y() + sheight),
                                           QPointF(pe.x(), ns.y() + sheight), pe, end]
                        elif end.y() <= start.y():
                            y = min(end.y() - eheight, start.y() - sheight)
                            self.points = [start, ns, QPointF(ns.x(), y),
                                           QPointF(pe.x(), y), pe, end]
                        else:
                            y = max(end.y() + eheight, start.y() + sheight)
                            self.points = [start, ns, QPointF(ns.x(), y),
                                           QPointF(pe.x(), y), pe, end]


            elif self.startGripItem.m_location in ["left"]:
                if self.endGripItem.m_location in ["top"]:
                    if start.x() + offset < end.x() - ewidth:
                        if end.y() > start.y() + sheight + offset:
                            self.points = [start, ns, QPointF(ns.x(), ns.y() + sheight),
                                           QPointF(pe.x(), ns.y() + sheight), end]
                        else:
                            y = min(start.y() - sheight, pe.y())
                            self.points = [start, ns, QPointF(ns.x(), y),
                                           QPointF(pe.x(), y), end]
                    elif end.x() + ewidth >= start.x() - offset:
                        x = min(ns.x(), end.x() - ewidth)
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
                    if start.x() + offset < end.x() - ewidth:
                        if end.y() < start.y() - sheight - offset:
                            self.points = [start, ns, QPointF(ns.x(), ns.y() - sheight),
                                           QPointF(pe.x(), ns.y() - sheight), end]
                        else:
                            y = max(start.y() + sheight, pe.y())
                            self.points = [start, ns, QPointF(ns.x(), y),
                                           QPointF(pe.x(), y), end]
                    elif end.x() + ewidth >= start.x() - offset:
                        x = min(ns.x(), end.x() - ewidth)
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
                        if end.y() + eheight <= start.y() - sheight - offset:
                            self.points = [start, ns, QPointF(ns.x(), ns.y() - sheight),
                                           QPointF(pe.x(), ns.y() - sheight), pe, end]
                        elif end.y() - eheight >= start.y() + sheight + offset:
                            self.points = [start, ns, QPointF(ns.x(), ns.y() + sheight),
                                           QPointF(pe.x(), ns.y() + sheight), pe, end]
                        elif end.y() <= start.y():
                            y = min(end.y() - eheight, start.y() - sheight)
                            self.points = [start, ns, QPointF(ns.x(), y),
                                           QPointF(pe.x(), y), pe, end]
                        else:
                            y = max(end.y() + eheight, start.y() + sheight)
                            self.points = [start, ns, QPointF(ns.x(), y),
                                           QPointF(pe.x(), y), pe, end]

                elif self.endGripItem.m_location in ["left"]:
                    self.points = [start, QPointF(pe.x(), start.y()), pe, end]
                    if start.x() + offset < end.x():
                        self.points = [start, ns, QPointF(ns.x(), end.y()), end]
                        if start.y() + sheight + offset > end.y() > start.y() - sheight - offset:
                            self.points = [start, ns, QPointF(ns.x(), ns.y() - sheight),
                                           QPointF(pe.x(), ns.y() - sheight), pe, end]
                    elif end.y() - eheight - offset < start.y() < end.y() + eheight + offset:
                        if end.y() > start.y():
                            self.points = [start, ns, QPointF(ns.x(), pe.y() - eheight),
                                           QPointF(pe.x(), pe.y() - eheight), pe, end]
                        else:
                            self.points = [start, ns, QPointF(ns.x(), pe.y() + eheight),
                                           QPointF(pe.x(), pe.y() + eheight), pe, end]


            elif self.startGripItem.m_location in ["top"]:
                if self.endGripItem.m_location in ["top"]:
                    self.points = [self.startPoint, QPointF(start.x(), pe.y()),
                                   pe, self.endPoint]
                    if start.y() < end.y():
                        self.points = [self.startPoint, ns, QPointF(pe.x(), ns.y()), self.endPoint]
                    if start.x() + swidth > end.x() > start.x() - swidth or end.x() + ewidth > start.x() > end.x() - ewidth:
                        x = max(start.x() + swidth, end.x() + ewidth)
                        x += offset
                        if start.x() > end.x():
                            x = min(start.x() - swidth, end.x() - ewidth)
                            x -= offset
                        self.points = [start, ns, QPointF(x, ns.y()),
                                       QPointF(x, pe.y()), pe, end]

                elif self.endGripItem.m_location in ["bottom"]:
                    self.points = [self.startPoint, ns, QPointF((x0 + x1) / 2, ns.y()), QPointF((x0 + x1) / 2, pe.y()),
                                   pe, self.endPoint]
                    if start.y() - offset > end.y():
                        self.points = [start, QPointF(start.x(), (y0 + y1) / 2), QPointF(end.x(), (y0 + y1) / 2),
                                       self.endPoint]
                    elif start.x() + swidth > end.x() > start.x() - swidth or end.x() + ewidth > start.x() > end.x() - ewidth:
                        x = max(start.x() + swidth, end.x() + ewidth)
                        x += offset
                        if start.x() > end.x():
                            x = min(start.x() - swidth, end.x() - ewidth)
                            x -= offset
                        self.points = [start, ns, QPointF(x, ns.y()),
                                       QPointF(x, pe.y()), pe, end]

                elif self.endGripItem.m_location in ["right"]:
                    y = min(ns.y(), end.y() + eheight + offset)
                    self.points = [start, QPointF(ns.x(), y), QPointF(pe.x(), y), pe, end]
                    if start.x() - swidth - offset < end.x() < start.x() + swidth + offset and end.y() > start.y() + offset:
                        self.points = [start, ns, QPointF(ns.x() + swidth + offset, ns.y()),
                                       QPointF(ns.x() + swidth + offset, pe.y()), end]
                    elif end.y() - eheight < start.y() - offset < end.y() + eheight:
                        self.points = [start, ns, QPointF(start.x(), end.y() - eheight),
                                       QPointF(pe.x(), end.y() - eheight), pe, end]

                elif self.endGripItem.m_location in ["left"]:
                    y = min(ns.y(), end.y() + eheight + offset)
                    self.points = [start, QPointF(ns.x(), y), QPointF(pe.x(), y), pe, end]
                    if start.x() - swidth - offset < end.x() < start.x() + swidth + offset and end.y() > start.y() + offset:
                        self.points = [start, ns, QPointF(ns.x() - swidth - offset, ns.y()),
                                       QPointF(ns.x() - swidth - offset, pe.y()), end]
                    elif end.y() - eheight < start.y() - offset < end.y() + eheight:
                        self.points = [start, QPointF(start.x(), end.y() - eheight),
                                       QPointF(pe.x(), end.y() - eheight), pe, end]

            elif self.startGripItem.m_location in ["bottom"]:
                if self.endGripItem.m_location in ["top"]:
                    self.points = [self.startPoint, ns, QPointF((x0 + x1) / 2, ns.y()), QPointF((x0 + x1) / 2, pe.y()),
                                   pe, self.endPoint]
                    if start.y() < end.y():
                        self.points = [self.startPoint, ns, QPointF(pe.x(), ns.y()), self.endPoint]
                    if start.x() + swidth > end.x() > start.x() - swidth or end.x() + ewidth > start.x() > end.x() - ewidth:
                        x = max(start.x() + swidth, end.x() + ewidth)
                        x += offset
                        self.points = [start, ns, QPointF(x, ns.y()),
                                       QPointF(x, pe.y()), pe, end]

                elif self.endGripItem.m_location in ["bottom"]:
                    self.points = [self.startPoint, ns, QPointF((x0 + x1) / 2, ns.y()), QPointF((x0 + x1) / 2, pe.y()),
                                   pe, self.endPoint]
                    if start.x() + swidth > end.x() > start.x() - swidth or end.x() + ewidth > start.x() > end.x() - ewidth:
                        x = max(start.x() + swidth, end.x() + ewidth)
                        x += offset
                        self.points = [start, ns, QPointF(x, ns.y()),
                                       QPointF(x, pe.y()), pe, end]

                elif self.endGripItem.m_location in ["right"]:
                    y = max(ns.y(), end.y() + eheight + offset)
                    self.points = [start, QPointF(ns.x(), y), QPointF(pe.x(), y), pe, end]
                    if start.x() - swidth - offset < end.x() < start.x() + swidth + offset:
                        self.points = [start, ns, QPointF(ns.x() + swidth + offset, ns.y()),
                                       QPointF(ns.x() + swidth + offset, pe.y()), end]

                elif self.endGripItem.m_location in ["left"]:
                    y = max(ns.y(), end.y() + eheight + offset)
                    self.points = [start, QPointF(ns.x(), y), QPointF(pe.x(), y), pe, end]
                    if start.x() - swidth - offset < end.x() < start.x() + swidth + offset:
                        self.points = [start, ns, QPointF(ns.x() - swidth - offset, ns.y()),
                                       QPointF(ns.x() - swidth - offset, pe.y()), end]

        # path of line
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
        if self.startGripItem:
            self.points[0]= self.startPoint
        if self.endGripItem:
            self.points[len(self.points) - 1] = self.endPoint
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
            item = Grabber(self, i, direction[(i - 1)%2])
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
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if value == 1:
                self.showGripItem()
            else:
                self.hideGripItem()
            return
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
            self.scene().update()
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

    def setPenStyle(self, style):
        """change current pen style for line"""
        self.penStyle = style
