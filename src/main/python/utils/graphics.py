from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPen, QKeySequence
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsProxyWidget, QGraphicsItem, QUndoStack, QAction, QUndoView

from .undo import *
from .dialogs import showUndoDialog

import shapes

class customView(QGraphicsView):
    """
    Defines custom QGraphicsView with zoom features and drag-drop accept event, overriding wheel event
    """
    def __init__(self, scene = None, parent=None):
        if scene is not None: #overloaded constructor
            super(customView, self).__init__(scene, parent)
        else:
            super(customView, self).__init__(parent)
        self._zoom = 1
        self.setDragMode(True) #sets pannable using mouse
        self.setAcceptDrops(True) #sets ability to accept drops
        if scene:
            #create necessary undo redo actions to accept keyboard shortcuts
            self.addAction(scene.undoAction)
            self.addAction(scene.redoAction)
            self.addAction(scene.deleteAction)
    
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
            graphic = getattr(shapes, QDropEvent.mimeData().text())(QDropEvent.pos().x()-150, QDropEvent.pos().y()-150, 300, 300)
            graphic.setPen(QPen(Qt.black, 2))
            graphic.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
            self.scene().addItemPlus(graphic) 
            QDropEvent.acceptProposedAction()
     
    def wheelEvent(self, QWheelEvent):
        #overload wheelevent, to zoom if control is pressed, else scroll normally
        if Qt.ControlModifier: #check if control is pressed
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
            return super().wheelEvent(self, QWheelEvent) # scroll if ctrl not pressed
    
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
        
class customScene(QGraphicsScene):
    """
    Extends QGraphicsScene with undo-redo functionality
    """
    def __init__(self, *args, parent=None):
        super(customScene, self).__init__(*args,  parent=parent)
        
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

    def deleteItem(self):
        # (slot) used to delete all selected items, and add undo action for each of them
        if self.selectedItems():
            for item in self.selectedItems():
                self.undoStack.push(deleteCommand(item, self))
            
    def itemMoved(self, movedItem, lastPos):
        #item move event, checks if item is moved
        self.undoStack.push(moveCommand(movedItem, lastPos))
    
    def addItemPlus(self, item):
        # extended add item method, so that a corresponding undo action is also pushed
        self.undoStack.push(addCommand(item, self))
        
    def mousePressEvent(self, event):
        # overloaded mouse press event to check if an item was moved
        bdsp = event.buttonDownScenePos(Qt.LeftButton) #get click pos
        point = QPointF(bdsp.x(), bdsp.y()) #create a Qpoint from click pos
        itemList = self.items(point) #get items at said point
        self.movingItem = itemList[0] if itemList else None #set first item in list as moving item
        if self.movingItem and event.button() == Qt.LeftButton:
            self.oldPos = self.movingItem.pos() #if left click is held, then store old pos
        self.clearSelection() #clears selected items
        return super(customScene, self).mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        # overloaded mouse release event to check if an item was moved
        if self.movingItem and event.button() == Qt.LeftButton:
            if self.oldPos != self.movingItem.pos():
                #if item pos had changed, when mouse was realeased, emit itemMoved signal
                self.itemMoved(self.movingItem, self.oldPos)
            self.movingItem = None #clear movingitem reference
        return super(customScene, self).mouseReleaseEvent(event)
