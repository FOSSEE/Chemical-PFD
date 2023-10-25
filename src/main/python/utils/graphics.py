from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtCore import Qt, QPointF, pyqtSignal
from PyQt5.QtWidgets import QGraphicsScene, QApplication
from PyQt5.QtGui import QPen, QKeySequence, QTransform, QCursor
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsProxyWidget, QGraphicsItem, QUndoStack, QAction, QUndoView, QScrollBar

from .undo import *
from .dialogs import showUndoDialog

import shapes



class CustomView(QGraphicsView):
    """
    Defines custom QGraphicsView with zoom features and drag-drop accept event, overriding wheel event
    """
    
    def __init__(self, scene = None, parent=None):
        if scene is not None: #overloaded constructor
            super(CustomView, self).__init__(scene, parent)
        else:
            super(CustomView, self).__init__(parent)
        self._zoom = 1
        self.setDragMode(True) #sets pannable using mouse
        self.setAcceptDrops(True) #sets ability to accept drops
        self.parent = parent
    
    #following four functions are required to be overridden for drag-drop functionality
    def dragEnterEvent(self, QDragEnterEvent):
        #defines acceptable drop items
        if QDragEnterEvent.mimeData().hasText():
            QDragEnterEvent.acceptProposedAction()
        
    def dragMoveEvent(self, QDragMoveEvent):
        #defines acceptable drop items
        if QDragMoveEvent.mimeData().hasText():
            QDragMoveEvent.acceptProposedAction()
            
    def dragLeaveEvent(self, QDragLeaveEvent):
        #accept any drag leave event, avoid unnecessary logging
        QDragLeaveEvent.accept()
    
    def dropEvent(self, QDropEvent):
        #defines item drop, fetches text, creates corresponding QGraphicItem and adds it to scene
        if QDropEvent.mimeData().hasText():
            #QDropEvent.mimeData().text() defines intended drop item, the pos values define position
            obj = QDropEvent.mimeData().text().replace(',', '').split('/')
            graphic = getattr(shapes, obj[0])(*map(lambda x: int(x) if x.isdigit() else x, obj[1:]))
            mappedFromGlobal = self.viewport().mapFromGlobal(QCursor.pos())
            graphic.setPos(mappedFromGlobal.x() + self.horizontalScrollBar().value() , mappedFromGlobal.y() + self.verticalScrollBar().value())
            self.scene().addItemPlus(graphic)
            graphic.setParent(self)
            QDropEvent.acceptProposedAction()
            self.parentFileWindow.isEdited = True
    
    def wheelEvent(self, QWheelEvent):
        #overload wheelevent, to zoom if control is pressed, else scroll normally
        if QWheelEvent.modifiers() & Qt.ControlModifier: #check if control is pressed
            if QWheelEvent.source() == Qt.MouseEventNotSynthesized: #check if precision mouse(mac)
                # angle delta is 1/8th of a degree per scroll unit
                if self.zoom + QWheelEvent.angleDelta().y()/2880 > 0.1: # hit and trial value (2880)
                    self.zoom += QWheelEvent.angleDelta().y()/2880
            else:
                # precision delta is exactly equal to amount to scroll
                if self.zoom + QWheelEvent.pixelDelta().y() > 0.1:
                    self.zoom += QWheelEvent.angleDelta().y()
            QWheelEvent.accept() # accept event so that scrolling doesnt happen simultaneously
        else:
            return super(CustomView, self).wheelEvent(QWheelEvent) # scroll if ctrl not pressed
    
    @property
    def zoom(self):
        # property for zoom
        return self._zoom
    
    @zoom.setter
    def zoom(self, value):
        # set scale according to zoom value being set
        temp = self.zoom
        self._zoom = value
        self.scale(self.zoom / temp, self.zoom / temp)

class CustomScene(QGraphicsScene):
    """
    Extends QGraphicsScene with undo-redo functionality
    """
    labelAdded = pyqtSignal(shapes.QGraphicsItem)
    itemMoved = QtCore.pyqtSignal(QtWidgets.QGraphicsItem, QtCore.QPointF)

    def __init__(self, *args, parent=None, parentFileWindow=None):
        super(CustomScene, self).__init__(*args,  parent=parent)
        self.movingItems = []  # List to store selected items for moving
        self.oldPositions = {}  # Dictionary to store old positions of moved items
        self.undoStack = QUndoStack(self) #Used to store undo-redo moves
        self.createActions() #creates necessary actions that need to be called for undo-redo

    def createActions(self):
        # helper function to create delete, undo and redo shortcuts
        self.deleteAction = QAction("Delete Item", self)
        self.deleteAction.setShortcut(Qt.Key_Delete)
        self.deleteAction.triggered.connect(self.deleteItem)

        self.undoAction = self.undoStack.createUndoAction(self, "Undo")
        self.undoAction.setShortcut(QKeySequence.Undo)
        self.redoAction = self.undoStack.createRedoAction(self, "Redo")
        self.redoAction.setShortcut(QKeySequence.Redo)

    def createUndoView(self, parent):
        # creates an undo stack view for current QGraphicsScene
        undoView = QUndoView(self.undoStack, parent)
        showUndoDialog(undoView, parent)
        # self.parentFileWindow.isEdited = True

    def deleteItem(self):
        # (slot) used to delete all selected items, and add undo action for each of them
        if self.selectedItems():
            for item in self.selectedItems():
                if issubclass(item.__class__,shapes.NodeItem) or isinstance(item,shapes.Line):
                    itemToDelete = item
                    self.count = 0
                    if(issubclass(itemToDelete.__class__,shapes.NodeItem)):
                        for i in itemToDelete.lineGripItems:
                            for j in i.lines:
                                self.count+=1
                                self.undoStack.push(deleteCommand(j, self))
                    self.undoStack.push(deleteCommand(itemToDelete, self))
                    # self.parentFileWindow.isEdited = True

    def itemMoved(self, movedItem, lastPos):
        #item move event, checks if item is moved
        self.undoStack.push(moveCommand(movedItem, lastPos))
        self.advance()
        # self.parentFileWindow.isEdited = True

    def addItemPlus(self, item):
        # extended add item method, so that a corresponding undo action is also pushed
        self.undoStack.push(addCommand(item, self))
        # self.parentFileWindow.isEdited = True

    """def mousePressEvent(self, event):
        bdsp = event.buttonDownScenePos(Qt.LeftButton)  # Get click position
        point = QPointF(bdsp.x(), bdsp.y())  # Create a QPointF from click position
        itemList = self.items(point)  # Get items at the specified point
        if itemList:
            item = itemList[0]  # Select the first item in the list
            if event.button() == Qt.LeftButton:
                modifiers = QApplication.keyboardModifiers()
                if modifiers == Qt.ControlModifier:
                    # Ctrl key is pressed, add item to the moving items list
                    if item not in self.movingItems:
                        self.movingItems.append(item)
                        self.oldPositions[item] = item.pos()
                else:
                    # Ctrl key is not pressed, clear the moving items list and selection
                    self.movingItems.clear()
                    self.clearSelection()
                    item.setSelected(True)

        return super(CustomScene, self).mousePressEvent(event)


    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            for item in self.movingItems:
                if self.oldPositions[item] != item.pos():
                    # Item position has changed, invoke the callback function
                    self.itemMoved(item, self.oldPositions[item])
            self.movingItems.clear()  # Clear the moving items list
            self.oldPositions.clear()  # Clear the old positions dictionary
        
        return super(CustomScene, self).mouseReleaseEvent(event)


    def mouseMoveEvent(self, mouseEvent):
        if self.movingItems:
            # Move all selected items together
            for item in self.movingItems:
                newPos = item.pos() + mouseEvent.scenePos() - mouseEvent.lastScenePos()
                item.setPos(newPos)

        item = self.itemAt(mouseEvent.scenePos().x(), mouseEvent.scenePos().y(), QTransform())
        if isinstance(item, shapes.SizeGripItem):
            item.parentItem().showLineGripItem()

        return super(CustomScene, self).mouseMoveEvent(mouseEvent)"""

    # The above is the mouse events for moving multiple images at once.

    def mousePressEvent(self, event):
        bdsp = event.buttonDownScenePos(Qt.LeftButton)  # get click pos
        point = QPointF(bdsp.x(), bdsp.y())  # create a QPointF from click pos
        itemList = self.items(point)  # get items at said point
        if event.button() == Qt.LeftButton:
            if itemList:
                self.movingItems = itemList
                self.initialPositions = {}
                for item in self.movingItems:
                    self.initialPositions[item] = item.pos()
            else:
                self.movingItems = []
        self.clearSelection()
        return super(CustomScene, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.movingItems:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ControlModifier:
                for item in self.movingItems:
                    item.setPos(item.pos() + event.scenePos() - event.lastScenePos())
            else:
                super(CustomScene, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.movingItems:
            for item in self.movingItems:
                if item.pos() != self.initialPositions[item]:
                    self.itemMoved(item, self.initialPositions[item])
            self.movingItems = []
            self.initialPositions = {}
        return super(CustomScene, self).mouseReleaseEvent(event)

    # The above mouse events are for moving items on top of each other.

    """def mousePressEvent(self, event):
        # overloaded mouse press event to check if an item was moved
        bdsp = event.buttonDownScenePos(Qt.LeftButton) #get click pos
        point = QPointF(bdsp.x(), bdsp.y()) #create a Qpoint from click pos
        itemList = self.items(point) #get items at said point
        self.movingItem = itemList[0] if itemList else None #set first item in list as moving item
        if self.movingItem and event.button() == Qt.LeftButton:
            self.oldPos = self.movingItem.pos() #if left click is held, then store old pos
        self.clearSelection() #clears selected items
        return super(CustomScene, self).mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        # overloaded mouse release event to check if an item was moved
        if self.movingItem and event.button() == Qt.LeftButton:
            if self.oldPos != self.movingItem.pos():
                #if item pos had changed, when mouse was realeased, emit itemMoved signal
                self.itemMoved(self.movingItem, self.oldPos)
            self.movingItem = None #clear movingitem reference
        return super(CustomScene, self).mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, mouseEvent):
        item = self.itemAt(mouseEvent.scenePos().x(), mouseEvent.scenePos().y(),
                                   QTransform())
        if isinstance(item,shapes.SizeGripItem):
            item.parentItem().showLineGripItem()
        super(CustomScene,self).mouseMoveEvent(mouseEvent)"""

    # The above is the original mouse events

    def reInsertLines(self):
        currentIndex = self.undoStack.index()
        i = 2
        skipper = 0   
        while i != self.count+2+skipper:
            currentCommand = self.undoStack.command(currentIndex-i)
            if not self.undoStack.text(currentIndex-i).__contains__('Move'):
                currentLine = currentCommand.diagramItem
                startGrip = currentCommand.startGripItem
                endGrip = currentCommand.endGripItem
                index_LineGripStart = currentCommand.indexLGS
                index_LineGripEnd = currentCommand.indexLGE
                startGrip.lineGripItems[index_LineGripStart].lines.append(currentLine)
                endGrip.lineGripItems[index_LineGripEnd].lines.append(currentLine)
            else:
                skipper+=1
            self.undoStack.setIndex(currentIndex-i)
            i+=1
