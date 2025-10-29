import os
import sys
import json
import pandas as pd

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
from utils.config import rLGPlus


directionsEnum = [
    "top",
    "right",
    "bottom",
    "left"
]

orientationEnum = [
    Qt.Horizontal,
    Qt.Vertical
]

rLGPlus_file_path = r"C:\Users\koyan\Chemical-PFD\src\main\resources\grips\rLGPlus.json"

rLGPlus = {}


def load_rLGPlus():
    if os.path.exists(rLGPlus_file_path):
        try:
            with open(rLGPlus_file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to decode JSON: {e}")
            return {}
    else:
        print(f"[ERROR] File not found: {rLGPlus_file_path}")
        return {}


rLGPlus = load_rLGPlus()

if rLGPlus:
    print("rLGPlus loaded successfully.")
else:
    print("rLGPlus is empty or failed to load.")


def load_grip_data():
    print("GRIP FILE PATH:", rLGPlus_file_path)
    print("EXISTS?", os.path.exists(rLGPlus_file_path))

    try:
        with open(rLGPlus_file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            print("Loaded lines:", lines)
            return lines
    except Exception as e:
        print("[ERROR] Could not load:", e)
        return []


class ItemLabel(QGraphicsTextItem):
    def __init__(self, text, parent=None):
        super().__init__(parent=parent)
        self.setPlainText(text)
        self.setDefaultTextColor(Qt.black)
        self.setZValue(1)

        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

        if parent:
            self.setPos(parent.boundingRect().bottomLeft())

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
        self.setPath(path)
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mouseReleaseEvent(self, event):
        """
        Automatically deselects grip item on mouse release
        """
        self.setSelected(False)
        super(GripItem, self).mouseReleaseEvent(event)


class SizeGripItem(QGraphicsPathItem):
    """
    Extends grip items for vertical and horizontal directions, with hover events and directional changes
    """

    def __init__(self, index, direction=Qt.Horizontal, parent=None):
        super(SizeGripItem, self).__init__(parent=parent)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setPen(QPen(Qt.NoPen))
        self.setZValue(2)
        self._direction = direction
        self._m_index = index

    def initWithParent(self):
        """Call this AFTER parentItem is assigned"""
        if self.parentItem():
            self._direction = (orientationEnum.index(self._direction) + self.parentItem().rotation) % 4
            self.updatePosition()

    @property
    def m_index(self):
        return (self._m_index + self.parentItem().rotation) % 4
    
    @property
    def direction(self):
        parent = self.parentItem()
        if parent is None:
            return 0  

        try:
            return parent.rotation() % 360
        except AttributeError:
            return 0


    def updatePath(self,m_index):
        """updates path of size grip item
        """
        bx = self.parentItem().boundingRect().x()
        by = self.parentItem().boundingRect().y()
        height = self.parentItem().boundingRect().height()
        width = self.parentItem().boundingRect().width()

        path = QPainterPath()
        if(m_index == 0):#top
            by = by+10
            path.moveTo(bx+(width/2)-10,by)
            path.lineTo(bx+(width/2)+10,by)
            path.lineTo(bx+(width/2),by-20)
            path.lineTo(bx+(width/2)-10,by)
        if(m_index == 1):#left
            bx = bx+10
            path.moveTo(bx,by+(height/2)-10)
            path.lineTo(bx,by+(height/2)+10)
            path.lineTo(bx-20,by+(height/2))
            path.lineTo(bx,by+(height/2)-10)
        if(m_index == 2):#bottom
            by = by-10
            path.moveTo(bx+(width/2)-10,by+height)
            path.lineTo (bx+(width/2)+10,by+height)
            path.lineTo (bx+(width/2),by+height+20)
            path.lineTo (bx+(width/2)-10,by+height)
        if(m_index == 3):#right
            bx = bx-10
            path.moveTo(bx+width,by+(height/2)-10)
            path.lineTo(bx+width,by+(height/2)+10)
            path.lineTo(bx+width+20,by+(height/2))
            path.lineTo(bx+width,by+(height/2)-10)
        self.setPath(path)

    def updatePosition(self):
        """updates position of grip items
        """
        self.updatePath(self.m_index)
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
        if self.direction == Qt.Horizontal:
            self.setCursor(QCursor(Qt.SizeHorCursor))
        else:
            self.setCursor(QCursor(Qt.SizeVerCursor))
        super(SizeGripItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """
        reverts cursor to default on mouse leave
        """
        self.setCursor(QCursor(Qt.ArrowCursor))
        super(SizeGripItem, self).hoverLeaveEvent(event)

    def itemChange(self, change, value):
        """
        Moves position of grip item on resize
        """
        if change == QGraphicsItem.ItemPositionChange and self.isEnabled():
            parent = self.parentItem()
            if parent is None:
                return value 

            p = QPointF(self.pos())
            if self.direction == Qt.Horizontal:
                p.setX(value.x())
            elif self.direction == Qt.Vertical:
                p.setY(value.y())

            movement = p - self.pos()

            transform = QTransform()
            transform.translate(-movement.x() / 2, -movement.y() / 2)
            self.setTransform(transform, True)

            if hasattr(parent, "resize"):
                parent.resize(self.m_index, movement)

            return p

        return super(SizeGripItem, self).itemChange(change, value)


    def mouseReleaseEvent(self, event):
        super(SizeGripItem, self).mouseReleaseEvent(event)
        self.resetTransform()
        self.updatePosition()
        self.parentItem().setFlag(QGraphicsSvgItem.ItemIsMovable, True)

    def show(self):
        self.setPen(QPen(QColor(128, 128, 128,150), 2))
        super(SizeGripItem,self).show()

    def hide(self):
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(Qt.transparent)
        super(SizeGripItem,self).hide()

class LineGripItem(QGraphicsPathItem):
    """Extends grip items for connecting lines , with hover events and mouse events
    """
    circle = QPainterPath()
    circle.addEllipse(QRectF(-5, -5, 10, 10))

    def __init__(self, index, grip, parent=None):
        super(LineGripItem, self).__init__(parent=parent)
        self.setPath(LineGripItem.circle)
        self.m_index = index
        self.position = QPointF(grip[0], grip[1])
        self._m_location = directionsEnum.index(grip[2])
        self.size = grip[3] if len(grip) == 4 else None
        self.tempLine = None
        self.lines = []
        self.previousHoveredItem = None
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setPen(QPen(QColor("black"), -1))
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    @property
    def m_location(self):
        if self.parentItem().__class__ == Line:
            return directionsEnum[self._m_location]
        index = (self._m_location + self.parentItem().rotation)
        if index%2:
            index = (index + 2*self.parentItem().flipH)%4
        else:
            index = (index + 2*self.parentItem().flipV)%4
        return directionsEnum[index]
    
    @m_location.setter
    def m_location(self, location):
        self._m_location = directionsEnum.index(location)

    def shape(self):
        qp = QPainterPathStroker()
        qp.setWidth(8)
        path = qp.createStroke(self.path())
        return path

    def paint(self, painter, option, widget):
        painter.setPen(self.pen())
        painter.drawPath(self.shape())
        painter.setBrush(self.brush())
        if self.size:
            painter.save()
            pen = self.pen()
            pen.setWidth(1)
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
            for line in self.lines:
                if line.scene():
                    line.scene().removeItem(line)
        return super(LineGripItem, self).itemChange(change, value)

    def updatePosition(self):
        width = self.parentItem().boundingRect().width()
        height = self.parentItem().boundingRect().height() 
        if self.size:
            rect_width = rect_height = 4
            if self.m_location in ["left", "right"]:
                rect_height = (self.size * height) / 100
            else:
                rect_width = (self.size * width) / 100
            path = QPainterPath() 
            path.addRect(QRectF(-rect_width / 2, -rect_height / 2, rect_width, rect_height)) # add rect to path
            self.setPath(path) # set path to grip
        # position according to svg co-ordinate
        x = (self.position.x() * width) / 100
        y = (self.position.y() * height) / 100
        # change position into items coordinate
        x -= width / 2
        y -= height / 2
        y = -y
        self.setEnabled(False)
        self.setPos(QPointF(x, y)) # set pos of grip
        self.setEnabled(True)
        # update all lines connected to it
        for line in self.lines:
            line.updateLine()

    def mousePressEvent(self, mouseEvent):
        """Handle all mouse press for this item
        """
        if mouseEvent.button() != Qt.LeftButton:
            return
        # initialize a line and add on scene
        # restrict circle grip to one line
        if self.size is None and len(self.lines) < 0:
            pass
        else:
            startPoint = self.parentItem().mapToScene(self.pos()) # first point of line
            mpos = self.mapToScene(mouseEvent.pos()) # position of mouse
            gap = 0 # distance from center of grip
            if self.size and self.m_location in ["top", "bottom"]:
                gap = (startPoint.x() - mpos.x()) / self.boundingRect().width()
                startPoint.setX(mpos.x())

            elif self.size:
                gap = (startPoint.y() - mpos.y()) / self.boundingRect().height()
                startPoint.setY(mpos.y())

            endPoint = startPoint
            self.tempLine = Line(startPoint, endPoint) # create a line object
            self.tempLine.startGap = gap # set gap to line
            self.scene().addItem(self.tempLine) # add line on scene
        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """Handle all mouse move for this item
        """
        # if line get started then update it's end point
        if self.tempLine:
            endPoint = mouseEvent.scenePos() # mouse position
            self.tempLine.updateLine(endPoint=endPoint)
        # find item below cursor
        item = self.scene().itemAt(mouseEvent.scenePos().x(), mouseEvent.scenePos().y(),
                                   QTransform())
        # hide grip of previous hovered item
        if self.previousHoveredItem and item != self.previousHoveredItem and \
                item not in self.previousHoveredItem.lineGripItems:
            self.previousHoveredItem.hideLineGripItem()
            #self.previousHoveredItem.hideSizeGripItem()
        super().mouseMoveEvent(mouseEvent)
        # show grip of current hoverde item
        if isinstance(item, NodeItem):
            self.previousHoveredItem = item
            item.showLineGripItem()

    def mouseReleaseEvent(self, mouseEvent):
        """Handle all mouse release for this item"""
        super().mouseReleaseEvent(mouseEvent)
    
        # set final position of line
        if self.tempLine:
            tag = 0
            items = self.scene().items(QPointF(mouseEvent.scenePos().x(), mouseEvent.scenePos().y()))
            for item in items:
                # end point on grip
                if isinstance(item, LineGripItem) and item != self:
                    endPoint = item.parentItem().mapToScene(item.pos())
                    gap = 0
                    # restrict line to one grip
                    if item.size is None and len(item.lines) > 0:
                        break
                    # in case of rectangle grip
                    if item.size and item.m_location in ["top", "bottom"]:
                        mpos = self.mapToScene(mouseEvent.pos())
                        gap = (endPoint.x() - mpos.x()) / item.boundingRect().width()
                        endPoint.setX(mpos.x())
                    elif item.size:
                        mpos = self.mapToScene(mouseEvent.pos())
                        gap = (endPoint.y() - mpos.y()) / item.boundingRect().height()
                        endPoint.setY(mpos.y())

                    self.tempLine.endGap = gap
                    self.tempLine.setStartGripItem(self)
                    self.tempLine.setEndGripItem(item)
                    if self.tempLine.startGripItem.parentItem() != self.tempLine.endGripItem.parentItem():
                        # update line with end point so it sets final path
                        self.tempLine.updateLine(endPoint=endPoint)
                    
                        # Adjusting line for repositioned rectangular grips
                        if 'rLGPlus' in globals() and self.parentItem().__class__.__name__ in rLGPlus:
                            for tgrip in rLGPlus[self.parentItem().__class__.__name__]:
                                if float(tgrip[3]) == 0:
                                    if self.m_location == tgrip[0]:
                                        tempx, tempy = int(tgrip[1]), int(tgrip[2])
                                        self.tempLine.startPoint.setX(self.tempLine.startPoint.x() + tempx)
                                        self.tempLine.startPoint.setY(self.tempLine.startPoint.y() + tempy)
                                else:
                                    if self.m_location == tgrip[0] and self.size == float(tgrip[3]):
                                        tempx, tempy = int(tgrip[1]), int(tgrip[2])
                                        self.tempLine.startPoint.setX(self.tempLine.startPoint.x() + tempx)
                                        self.tempLine.startPoint.setY(self.tempLine.startPoint.y() + tempy)

                        if 'rLGPlus' in globals() and item.parentItem().__class__.__name__ in rLGPlus:
                            for tgrip in rLGPlus[item.parentItem().__class__.__name__]:
                                if float(tgrip[3]) == 0:
                                    if item.m_location == tgrip[0]:
                                        tempx, tempy = int(tgrip[1]), int(tgrip[2])
                                        self.tempLine.endPoint.setX(self.tempLine.endPoint.x() + tempx)
                                        self.tempLine.endPoint.setY(self.tempLine.endPoint.y() + tempy)
                                else:
                                    if item.m_location == tgrip[0] and item.size == float(tgrip[3]):
                                        tempx, tempy = int(tgrip[1]), int(tgrip[2])
                                        self.tempLine.endPoint.setX(self.tempLine.endPoint.x() + tempx)
                                        self.tempLine.endPoint.setY(self.tempLine.endPoint.y() + tempy)

                        self.lines.append(self.tempLine)
                        item.lines.append(self.tempLine)
                        tag = 1
                        break
                # end point on line
                elif isinstance(item, Line) and item != self.tempLine:
                    self.tempLine.setStartGripItem(self)
                    endPoint = mouseEvent.scenePos()
                    self.tempLine.refLine = item
                    self.tempLine.refIndex = findIndex(item, endPoint)
                    self.tempLine.updateLine(endPoint=endPoint)
                    item.midLines.append(self.tempLine)
                    self.lines.append(self.tempLine)
                    tag = 1
                    break

            self.scene().removeItem(self.tempLine)  # remove temp line from scene
            # if line end point is on grip or line
            if tag:
                self.scene().addItemPlus(self.tempLine)  # add line on scene

        self.tempLine = None
        self.previousHoveredItem = None

    def show(self):
        """ shows line grip item
        """
        self.setPen(QPen(QColor(0,0,0,150), 1.5))
        self.setBrush(QColor(140,199,198,255))

    def hide(self):
        """ hides line grip item
        """
        if not self.parentItem().isSelected():
            self.setPen(QPen(Qt.transparent))
            self.setBrush(Qt.transparent)




from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer
from PyQt5.QtWidgets import QGraphicsTextItem
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt


class NodeItem(QGraphicsSvgItem):
    def __init__(self, unitOperationType, label=None, type_name=None, parent=None):
        super().__init__(parent)
        self.m_type = str(unitOperationType)
        from utils.app import fileImporter  # ✅ Keep at top

        svg_path = fileImporter("resources", "base", "svg", *unitOperationType.split("/")) + ".svg"

        if not os.path.exists(svg_path):
            svg_path = fileImporter("resources", "base", "svg", "default.svg")


        self.m_renderer = QSvgRenderer(svg_path)
        self.setSharedRenderer(self.m_renderer)

        self.width = self.m_renderer.defaultSize().width()
        self.height = self.m_renderer.defaultSize().height()

        self.label = label
        self.typeName = type_name

        self.setFlags(
            QGraphicsSvgItem.ItemIsMovable |
            QGraphicsSvgItem.ItemIsSelectable |
            QGraphicsSvgItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setZValue(2)

        self.lineGripItems = []
        self.sizeGripItems = []
        self._rotation = 0
        self.flipState = [False, False]

        # Label
        self.name_label = QGraphicsTextItem(self)
        font = QFont()
        font.setPointSize(10)
        self.name_label.setFont(font)
        self.name_label.setDefaultTextColor(Qt.black)

        self.setLabelText(self.label if label else (self.typeName or "Unnamed"))
        self.activateGrip = False


    def setLabelText(self, text):
        self.name_label.setPlainText(text)
        self.label = text 
        label_width = self.name_label.boundingRect().width()
        item_width = self.boundingRect().width()
        x = (item_width - label_width) / 2
        y = self.boundingRect().height() + 10
        self.name_label.setPos(x, y)

    def setData(self, data):
        self.legend = data.get('legend', 'N/A')
        self.suffix = data.get('suffix', 'N/A')

        formatted_label = f"{self.legend}-{self.suffix}"
        self.setLabelText(formatted_label)

        if not self.typeName:
            self.typeName = self.m_type

    @property
    def flipH(self):
        return self.flipState[0]
    
    @property
    def flipV(self):
        return self.flipState[1]
    
    def updateTransformation(self):
        # update transformation on flipstate or rotation change
        transform = QTransform()
        h = -1 if self.flipH else 1
        w = -1 if self.flipV else 1
        transform.rotate(90*self.rotation)
        transform.scale(h, w)
        self.setTransform(transform)
        self.setTransform(transform)
        for i in self.lineGripItems:
            i.setTransform(transform)
            i.updatePosition()
                
    @flipH.setter
    def flipH(self, state):
        self.flipState[0] = state
        self.updateTransformation()

    @flipV.setter
    def flipV(self, state):
        self.flipState[1] = state
        self.updateTransformation()
            
    @property
    def rotation(self):
        return self._rotation
    
    @rotation.setter
    def rotation(self, rotation):
        self._rotation = rotation % 4
        self.updateTransformation()
        
    def boundingRect(self):
        """Overrides QGraphicsSvgItem's boundingRect() virtual public function and
        returns a valid bounding
        """
        return QRectF(-self.width / 2, -self.height / 2, self.width, self.height)

    def paint(self, painter, option, widget):
        """
            Paints the contents of an item in local coordinates.
            :param painter: QPainter instance
            :param option: QStyleOptionGraphicsItem instance
            :param widget: QWidget instance
        """
        # check if render is set
        if not self.m_renderer:
            QGraphicsSvgItem.paint(self, painter, option, widget)
        else:
            self.m_renderer.render(painter, self.boundingRect())  # render svg using painter

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
        transform = QTransform()
        transform.translate(movement.x() / 2, movement.y() / 2)
        self.setTransform(transform, True)
        self.updateSizeGripItem([index])

    def addGripItem(self):
        """adds grip items
        """
        if self.scene():
            # add grip for resizing
            for i, (direction) in enumerate(
                    (
                            Qt.Vertical,
                            Qt.Horizontal,
                            Qt.Vertical,
                            Qt.Horizontal,
                    )
            ):
                item = SizeGripItem(i, direction, parent=self)
                self.sizeGripItems.append(item)
            # add grip items for connecting lines
            for i in range(len(self.grips)):
                grip = self.grips[i]
                item = LineGripItem(i, grip, parent=self)
                self.lineGripItems.append(item)

    def updateLineGripItem(self):
        """
        updates line grip items
        """
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
        """Overloads and extends QGraphicsSvgItem to also update grip items"""
        newPos = value

        # check if item selected has changed
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if value is True:
                self.showLineGripItem()
                self.showSizeGripItem()
            else:
                self.hideLineGripItem()
                if not self.activateGrip:
                    self.hideSizeGripItem()
            return

        # check if transformation has changed
        if change == QGraphicsItem.ItemTransformHasChanged:
            self.updateLineGripItem()
            return

        # check if position has changed
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Before updating the line grip item positions, ensure rLGPlus is accessible
            if 'rLGPlus' in globals() and self.parentItem().__class__.__name__ in rLGPlus:
                for tgrip in rLGPlus[self.parentItem().__class__.__name__]:
                    if float(tgrip[3]) == 0:
                        if self.m_location == tgrip[0]:
                            tempx, tempy = int(tgrip[1]), int(tgrip[2])
                            self.tempLine.startPoint.setX(self.tempLine.startPoint.x() + tempx)
                            self.tempLine.startPoint.setY(self.tempLine.startPoint.y() + tempy)
                    else:
                        if self.m_location == tgrip[0] and self.size == float(tgrip[3]):
                            tempx, tempy = int(tgrip[1]), int(tgrip[2])
                            self.tempLine.startPoint.setX(self.tempLine.startPoint.x() + tempx)
                            self.tempLine.startPoint.setY(self.tempLine.startPoint.y() + tempy)

            # Apply other transformations or movements
            self.updateLineGripItem()
            self.updateSizeGripItem()

            # Restrict movable area of Node Item
            if self.parent() is not None:
                rect = self.parent().sceneRect()
                width = self.boundingRect().width()
                height = self.boundingRect().height()
                eWH1 = QPointF(newPos.x() + width, newPos.y() + height)
                eWH2 = QPointF(newPos.x() - width, newPos.y() - height)
                if not rect.__contains__(eWH1) or not rect.__contains__(eWH2):
                    newPos.setX(min(rect.right() - width + 40, max(newPos.x(), rect.left() + 90)))
                    newPos.setY(min(rect.bottom() - height, max(newPos.y(), rect.top() + 70)))
                    self.setPos(newPos)

            return super(NodeItem, self).itemChange(change, newPos)

        # Check if item is added to the scene
        if change == QGraphicsItem.ItemSceneHasChanged and self.scene():
            self.addGripItem()
            self.updateLineGripItem()
            self.updateSizeGripItem()
            return

        return super(NodeItem, self).itemChange(change, value)

    def hoverEnterEvent(self, event):
        """defines shape highlighting on Mouse Over
        """
        self.showLineGripItem()
        super(NodeItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """defines shape highlighting on Mouse Leave
        """
        self.hideLineGripItem()
        #self.hideSizeGripItem()
        super(NodeItem, self).hoverLeaveEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        self.activateGrip = not self.activateGrip
        if self.activateGrip == False:
            self.hideSizeGripItem()
            self.parent().update()
        else:
            self.showSizeGripItem()
        super(NodeItem,self).mouseDoubleClickEvent(event)

    def showLineGripItem(self):
        """shows line grip items of svg item
        """
        for item in self.lineGripItems:
            item.show()

    def hideLineGripItem(self):
        """hide line grip items of svg item
        """
        for item in self.lineGripItems:
            item.hide()
    
    def showSizeGripItem(self):
        """shows size grip items of svg item
        """
        for item in self.sizeGripItems:
            item.show()

    def hideSizeGripItem(self):
        """hide size grip items of svg item
        """
        self.activateGrip = False
        for item in self.sizeGripItems:
            item.hide()

    def contextMenuEvent(self, event):
        """Pop up menu
        :return:
        """
        # create a menu and add action
        contextMenu = QMenu()
        contextMenu.addAction("Rotate right(E)", lambda : setattr(self, "rotation", self.rotation + 1))
        contextMenu.addAction("Rotate left(Q)", lambda : setattr(self, "rotation", self.rotation - 1))
        contextMenu.addAction("Flip Horizontally", lambda: setattr(self, "flipH", not self.flipH))
        contextMenu.addAction("Flip Vertically", lambda: setattr(self, "flipV", not self.flipV))
        action = contextMenu.exec_(event.screenPos())

    def __getstate__(self):
        return {
            "_classname_": self.__class__.__name__,
            "width": self.width,
            "height": self.height,
            "pos": (self.pos().x(), self.pos().y()),
            "lineGripItems": [(hex(id(i)), i.m_index) for i in self.lineGripItems],
            "label": self.label,
            "rotation": self.rotation,
            "flipstate": self.flipState
        }

    def __setstate__(self, dict):
        self.prepareGeometryChange()
        self.width = dict['width']
        self.height = dict['height']
        self.updateSizeGripItem()


class InflowLine(NodeItem):
    def __init__(self, label=None):
        super().__init__("Piping/Inflow Line", label, "Inflow Line")
        self.setLabelText(label or "I-01")
        self.grips = [
            [100, 50, "right"]
        ]


class OutflowLine(NodeItem):
    def __init__(self, label=None):
        super().__init__("Piping/Outflow Line", label, "Outflow Line")
        self.setLabelText(label or "O-01")
        self.grips = [
            [0, 50, "left"]
        ]

class DuplexPump(NodeItem):
    def __init__(self, label=None):
        super().__init__("Pumps/Duplex Pump", label, "Duplex Pump")
        self.setLabelText(label or "P-01-A/B")
        self.grips = [
            [100, 68.8031698, "right"],
            [0, 88.1365808, "left"]
        ]


class PlungerPump(NodeItem):
    def __init__(self, label=None):
        super().__init__("Pumps/Plunger Pump", label, "Plunger Pump")
        self.setLabelText(label or "P-02-A/B")
        self.grips = [
            [87.0328592, 100, "top"],
            [87.0328592, 0, "bottom"]
        ]


class ProportioningPump(NodeItem):
    def __init__(self, label=None):
        super().__init__("Pumps/Proportioning Pump", label, "Proportioning Pump")
        self.setLabelText(label or "P-03-A/B")
        self.grips = [
            [100, 83.0966226, "right"],
            [0, 83.0966226, "left"]
        ]


class ReciprocatingPump(NodeItem):
    def __init__(self, label=None):
        super().__init__("Pumps/Reciprocating Pump", label, "Reciprocating Pump")
        self.setLabelText(label or "P-04-A/B")
        self.grips = [
            [100, 78.3969475, "right"],
            [0, 78.3969475, "left"]
        ]

class BlowingEgg(NodeItem):
    def __init__(self, label=None):
        super().__init__("Pumps/Blowing Egg", label, "Blowing Egg")
        self.setLabelText(label or "P-05")
        self.grips = [
            [15.2887853, 56.4147177, "top"],
            [84.7112147, 56.4147177, "top"]
        ]


class EjectorVaporService(NodeItem):
    def __init__(self, label=None):
        super().__init__("Pumps/Ejector(Vapor Service)", label, "Ejector(Vapor Service)")
        self.setLabelText(label or "P-06")
        self.grips = [
            [18, 100, "top"],
            [0, 50, "left"],
            [100, 50, "right"]
        ]


class HandPumpWithDrum(NodeItem):
    def __init__(self, label=None):
        super().__init__("Pumps/Hand Pump with Drum", label, "Hand Pump with Drum")
        self.setLabelText(label or "P-07")
        self.grips = [
            [92.8093483, 70.60413752309337, "right"],
            [7.913824600849647, 70.60413752309337, "left"],
            [4.136894788615162, 86.9886362, "left"]
        ]

class CentrifugalCompressor(NodeItem):
    def __init__(self, label=None):
        super().__init__("Compressors/Centrifugal Compressor", label, "Centrifugal Compressor")
        self.setLabelText(label or "C-01-A/B")
        self.grips = [
            [41.316753407496, 89.824108247573, "top"],
            [62.0517030576456, 79.183192150093, "top"],
            [41.316753407496, 6.447877022097, "bottom"],
            [62.0517030576456, 16.14847772052, "bottom"]
        ]



class EjectorCompressor(NodeItem):
    def __init__(self, label=None):
        super().__init__("Compressors/Ejector Compressor", label, "Ejector Compressor")
        self.setLabelText(label or "C-02")
        self.grips = [
            [13.1018813062, 100, "top"],
            [0, 50, "left"],
            [100, 50, "right"]
        ]


class Fan(NodeItem):
    def __init__(self, label=None):
        super().__init__("Compressors/Fan", label, "Fan")
        self.setLabelText(label or "F-01")
        self.grips = [
            [50, 79.92762310350343, "top"],
            [0, 79.92762310350343, "left"],
            [100, 79.92762310350343, "right"]
        ]


class PositiveDisplacementCompressor(NodeItem):
    def __init__(self, label=None):
        super().__init__("Compressors/Positive Displacement Compressor", label, "Positive Displacement Compressor")
        self.setLabelText(label or "C-03")
        self.grips = [
            [50, 100, "top"],
            [21.15509548928236, 30, "left"],
            [79.57853462426666, 30, "right"]
        ]


class ReciprocatingCompressor(NodeItem):
    def __init__(self, label=None):
        super().__init__("Compressors/Reciprocating Compressor", label, "Reciprocating Compressor")
        self.setLabelText(label or "C-04")
        self.grips = [
            [22.85680252121469, 83, "left"],
            [46.81088180183039, 83, "right"]
        ]


class Turbine(NodeItem):
    def __init__(self, label=None):
        super().__init__("Compressors/Turbine", label, "Turbine")
        self.setLabelText(label or "T-01")
        self.grips = [
            [18.06209745144267, 79.11931909160472, "top"],
            [45.2091373550176, 91.385325275219, "top"],
            [18.06209745144267, 16.41537491819628, "bottom"],
            [45.2091373550176, 4.5725942986116, "bottom"]
        ]


class OilGasOrPulverizedFuelFurnace(NodeItem):
    def __init__(self, label=None):
        super().__init__("Furnaces and Boilers/Oil Gas or Pulverized Fuel Furnace", label, "Oil Gas or Pulverized Fuel Furnace")
        self.setLabelText(label or "F-02")
        self.grips = [
            [58.27673386073162, 100, "top"],
            [0, 19.692723451106, "left"],
            [17.2777337415748, 33.3944873323144, "left"],
            [100, 33.3944873323144, "right"],
            [57.9723659874, 0, "bottom"]
        ]


class SolidFuelFurnace(NodeItem):
    def __init__(self, label=None):
        super().__init__("Furnaces and Boilers/Solid Fuel Furnace", label, "Solid Fuel Furnace")
        self.setLabelText(label or "F-03")
        self.grips = [
            [50, 100, "top"],
            [0, 33.39352642259468, "left"],
            [100, 33.39352642259468, "right"],
            [50, 0, "bottom"]
        ]


class Exchanger905(NodeItem):
    def __init__(self, label=None):
        super().__init__("Heating or Cooling Arrangements/905Exchanger", label, "905 Exchanger")
        self.setLabelText(label or "E-01")
        self.grips = [
            [15.85, 13.5, "bottom"],
            [60.5, 13.5, "bottom"],
            [15.85, 88.88, "top"],
            [60.5, 88.88, "top"]
        ]


class KettleReboiler907(NodeItem):
    def __init__(self, label=None):
        super().__init__("Heating or Cooling Arrangements/907Kettle Reboiler", label, "907 Kettle Reboiler")
        self.setLabelText(label or "E-02")
        self.grips = [
            [18, 20.33, "bottom"],
            [70, 20.33, "bottom"],
            [18, 75, "top"],
            [70, 96, "top"]
        ]


class Exchanger(NodeItem):
    def __init__(self, label=None):
        super().__init__("Heating or Cooling Arrangements/Exchanger", label, "Exchanger")
        self.setLabelText(label or "E-03")
        self.grips = [
            [100, 31.74474612706027, "right"],
            [100, 62.70549343934227, "right"],
            [35.66, 100, "top"],
            [36.66, 0, "bottom"]
        ]


class HeatExchanger(NodeItem):
    def __init__(self, label=None):
        super().__init__("Heating or Cooling Arrangements/Heat Exchanger", label, "Heat Exchanger")
        self.setLabelText(label or "E-04")
        self.grips = [
            [0, 47.14356681569796, "left"],
            [100, 47.14356681569796, "right"],
            [50.92839727035332, 100, "top"],
            [50.92839727035332, 0, "bottom"]
        ]


class ImmersionCoil(NodeItem):
    def __init__(self, label=None):
        super().__init__("Heating or Cooling Arrangements/Immersion Coil", label or "H-01", "Immersion Coil")
        self.grips = [
            [44.56, 100, "top"],
            [88.23, 100, "top"]
        ]


class KettleReboiler(NodeItem):
    def __init__(self, label=None):
        super().__init__("Heating or Cooling Arrangements/Kettle Reboiler", label or "H-02", "Kettle Reboiler")
        self.grips = [
            [100, 26.3, "right"],
            [0, 26.3, "left"],
            [50, 100, "top"],
            [50, 0, "bottom"]
        ]


class HorizontalVessel(NodeItem):
    def __init__(self, label=None):
        super().__init__("Process Vessels/Horizontal Vessel", label or "V-01", "Horizontal Vessel")
        self.grips = [
            [50, 100, "top"],
            [0, 50, "left"],
            [100, 50, "right"],
            [50, 0, "bottom"]
        ]


class PackedVessel(NodeItem):
    def __init__(self, label=None):
        super().__init__("Process Vessels/Packed Vessel", label or "V-02", "Packed Vessel")
        self.grips = [
            [50, 100, "top"],
            [0, 50, "left"],
            [100, 50, "right"],
            [50, 0, "bottom"]
        ]


class TraysOrPlates(NodeItem):
    def __init__(self, label=None):
        super().__init__("Process Vessels/Trays or plates", label or "V-03", "Trays or plates")
        self.grips = []


class VerticalVessel(NodeItem):
    def __init__(self, label=None):
        super().__init__("Process Vessels/Vertical Vessel", label or "V-04", "Vertical Vessel")
        self.grips = [
            [50, 100, "top"],
            [-10, 50, "left"],
            [110, 50, "right"],
            [50, 0, "bottom"]
        ]

class SeparatorsForLiquidsDecanter(NodeItem):
    def __init__(self, label=None):
        super().__init__("Separators/Separators for Liquids, Decanter", label or "S-01", "Separators for Liquids, Decanter")
        self.grips = [
            [50, 100, "top"],
            [0, 50, "left"],
            [100, 50, "right"],
            [50, 0, "bottom"]
        ]

class FixedRoofTank(NodeItem):
    def __init__(self, label=None):
        super().__init__("Storage Vessels Tanks/Fixed Roof Tank", label or "T-01", "Fixed Roof Tank")
        self.grips = [
            [50, 100, "top"],
            [-6, 50, "left"],
            [107, 50, "right"],
            [50, -10, "bottom"]
        ]


class FloatingRoofTank(NodeItem):
    def __init__(self, label=None):
        super().__init__("Storage Vessels Tanks/Floating Roof Tank", label or "T-02", "Floating Roof Tank")
        self.grips = [
            [-7, 50, "left"],
            [107, 50, "right"],
            [50, -10, "bottom"]
        ]


class SeparatorsForLiquidsDecanter(NodeItem):
    def __init__(self, label=None):
        super().__init__("Separators/Separators for Liquids, Decanter", label or "S-02", "Separators for Liquids, Decanter")
        self.grips = [
            [50, 110, "top"],
            [-10, 50, "left"],
            [110, 50, "right"],
            [50, -10, "bottom"]
        ]


class GateValve(NodeItem):
    def __init__(self, label=None):
        super().__init__("Valves/Gate Valve", label or "VLV-01", "Gate Valve")
        self.grips = [
            [0, 50, "left"],
            [100, 50, "right"]
        ]

class ButterflyValve(NodeItem):
    def __init__(self, label=None):
        super().__init__("Valves/Butterfly Valve", label or "VLV-02", "Butterfly Valve")
        self.grips = [
            [0, 50, "left"],
            [100, 50, "right"]
        ]

class FloatValve(NodeItem):
    def __init__(self, label=None):
        super().__init__("Valves/Float Valve", label or "VLV-03", "Float Valve")
        self.grips = [
            [0, 50, "left"],
            [100, 50, "right"]
        ]


class CentrifugalPump(NodeItem):
    def __init__(self, label=None):
        super().__init__("Pumps/Centrifugal Pump", label or "P-01", "Centrifugal Pump")
        self.grips = [
            [100, 97.2, "right"],
            [0, 58.78, "left"]
        ]


class OneCellFiredHeaterFurnace(NodeItem):
    def __init__(self, label=None):
        super().__init__("Furnaces and Boilers/One Cell Fired Heater, Furnace", label or "H-03", "One Cell Fired Heater")
        self.grips = [
            [50, 100, "top"],
            [0, 28, "left"],
            [25, 87.5, "left"],
            [100, 28, "right"],
            [75, 87.5, "right"],
            [50, -5, "bottom"]
        ]


class TwoCellFiredHeaterFurnace(NodeItem):
    def __init__(self, label=None):
        super().__init__("Furnaces and Boilers/Two Cell Fired Heater, Furnace", label or "H-04", "Two Cell Fired Heater")
        self.grips = [
            [50, 100, "top"],
            [-5, 33.33, "left"],
            [33.33, 91.66, "left"],
            [105, 33.33, "right"],
            [66.66, 91.66, "right"],
            [16.67, -10, "bottom"],
            [83.33, -10, "bottom"]
        ]


class ReducerExpander(NodeItem):
    def __init__(self, label=None):
        super().__init__("Fittings/Reducer, Expander", label or "F-01", "Reducer, Expander")
        self.grips = [
            [100, 50, "right"],
            [0, 50, "left"]
        ]


class Filter(NodeItem):
    def __init__(self, label=None):
        super().__init__("Fittings/Filter", label or "F-02", "Filter")
        self.grips = [
            [0, 50, "left"],
            [100, 50, "right"]
        ]


class ContinuousDryer(NodeItem):
    def __init__(self, label=None):
        super().__init__("Dryers/Continuous Dryer", label or "D-01", "Continuous Dryer")
        self.grips = [
            [8.13, 35.2, "top"],
            [98.9, 28, "bottom"],
            [50, 110, "top"]
        ]


class JawCrusher(NodeItem):
    def __init__(self, label=None):
        super().__init__("Size Reduction Equipements/Jaw Crusher", label or "CR-01", "Jaw Crusher")
        self.grips = [
            [79.65, 100, "top"],
            [0, 0, "bottom"]
        ]


class RollerCrusher(NodeItem):
    def __init__(self, label=None):
        super().__init__("Size Reduction Equipements/Roller Crusher", label or "CR-02", "Roller Crusher")
        self.grips = [
            [50, 100, "top"],
            [50, 0, "bottom"]
        ]


class GeneralSymbol(NodeItem):
    def __init__(self, label=None):
        super().__init__("Feeders/General Symbol", label or "G-01", "General Symbol")
        self.grips = [
            [20, 100, "top"],
            [80, 0, "bottom"]
        ]

