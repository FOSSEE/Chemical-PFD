import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.component_mapper import get_component_data

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

from .undo import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtCore import Qt, QPointF, pyqtSignal
from PyQt5.QtWidgets import QGraphicsScene, QApplication
from PyQt5.QtGui import QPen, QKeySequence, QTransform, QCursor
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsProxyWidget, QGraphicsItem, QUndoStack, QAction, QUndoView, QScrollBar

from .undo import *
from .dialogs import showUndoDialog
import shapes

class CustomView(QGraphicsView):
    def __init__(self, scene=None, parent=None):
        super().__init__(scene if scene else QGraphicsScene(), parent)
        self._zoom = 1
        self.setDragMode(True)
        self.setAcceptDrops(True)
        self.parent = parent

        self.legend_counter = {}

    
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
    
    def dropEvent(self, event):
        component_type = event.mimeData().text().replace(",", "")
        component_data = get_component_data(component_type)

        if not hasattr(self, "legend_counter"):
            self.legend_counter = {}

        if component_data:
            graphic = self.createGraphicItem(component_type)

            if graphic is None:
                return

            scene_pos = self.mapToScene(event.pos())
            graphic.setPos(scene_pos)
            graphic.setData(component_data)

            # Extract legend and suffix
            legend = component_data.get('legend', '').strip()
            suffix = component_data.get('suffix', '').strip()

            if legend not in self.legend_counter:
                self.legend_counter[legend] = 1

            count = self.legend_counter[legend]
            self.legend_counter[legend] += 1

            # Format label based on suffix
            if suffix:
                formatted_label = f"{legend}-{count:02d}-{suffix}"
            else:
                formatted_label = f"{legend}-{count:02d}"

            graphic.setLabelText(formatted_label)


            # Optional: update grips
            if hasattr(graphic, "updateLineGripItem"):
                graphic.updateLineGripItem()
            if hasattr(graphic, "updateSizeGripItem"):
                graphic.updateSizeGripItem()

            # ✅ Yahan undo ke through add karo
            self.scene().addItemPlus(graphic)

        event.acceptProposedAction()

    def createGraphicItem(self, component_type):
        import shapes  # ensure shapes is imported
        if hasattr(shapes, component_type):
            cls = getattr(shapes, component_type)
            return cls()
        else:
            print(f"Component type '{component_type}' not found in shapes.")
            return None

    def updateCanvas(self):
        self.viewport().update()

    
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

from PyQt5.QtWidgets import QGraphicsScene, QAction, QUndoStack
from PyQt5.QtCore import pyqtSignal
import shapes
from .undo import addCommand, moveCommand, deleteCommand  # Assuming your commands are in undo.py

class CustomScene(QGraphicsScene):
    """
    Extends QGraphicsScene with undo-redo functionality
    """
    labelAdded = pyqtSignal(shapes.QGraphicsItem)
    itemMoved = pyqtSignal(shapes.QGraphicsItem, QtCore.QPointF)

    def __init__(self, *args, parent=None, parentFileWindow=None, mdi=None):
        super(CustomScene, self).__init__(*args, parent=parent)
        self.mdi = mdi  # Store mdi reference
        self.movingItems = []  # List to store selected items for moving
        self.oldPositions = {}  # Dictionary to store old positions of moved items
        self.undoStack = QUndoStack(self)  # Used to store undo-redo moves
        self.createActions()  # Creates necessary actions for undo-redo
        self.parentFileWindow = parentFileWindow

    def createActions(self):
        self.deleteAction = QAction("Delete Item", self)
        self.deleteAction.setShortcut(Qt.Key_Delete)
        self.deleteAction.triggered.connect(self.deleteItem)

        self.undoAction = self.undoStack.createUndoAction(self, "Undo")
        self.undoAction.setShortcut(QKeySequence.Undo)
        self.redoAction = self.undoStack.createRedoAction(self, "Redo")
        self.redoAction.setShortcut(QKeySequence.Redo)
    
    def createUndoView(self, parent):
        undoView = QUndoView(self.undoStack, parent)
        showUndoDialog(undoView, parent)
        self.parentFileWindow.isEdited = True
        print("[DEBUG] Undo view opened")

    def addItemPlus(self, item):
        """Add item via undo command so redo/undo work."""
        cmd = addCommand(item, self, parentFileWindow=self.parentFileWindow)
        self.undoStack.push(cmd)
        self.updateUndoRedoState()

    def itemMoved(self, movedItem, lastPos):
        """ Handles moving items and pushing the move action to undo stack """
        print(f"Moving item: {movedItem} from {lastPos} to {movedItem.pos()}")
        move_command = moveCommand(movedItem, lastPos, parentFileWindow=self.parentFileWindow)
        self.undoStack.push(move_command)  # Push move command to undo stack
        self.updateUndoRedoState()

    def deleteItem(self):
        """ Deletes selected items and pushes the delete action to undo stack """
        if self.selectedItems():
            print(f"Deleting {len(self.selectedItems())} items")
            for item in self.selectedItems():
                delete_command = deleteCommand(item, self, parentFileWindow=self.parentFileWindow)
                self.undoStack.push(delete_command)  # Push delete command to undo stack
                self.updateUndoRedoState()

    def undo(self):
        """ Undo the last action """
        print("Undo triggered in CustomScene")
        if self.undoStack.canUndo():
            self.undoStack.undo()
            self.updateSelectionAfterUndoRedo()

    def redo(self):
        """ Redo the last undone action """
        print("Redo triggered in CustomScene")
        if self.undoStack.canRedo():
            self.undoStack.redo()
            self.updateSelectionAfterUndoRedo()

    def updateUndoRedoState(self):
        """ Update the state of undo/redo actions based on the stack """
        self.undoAction.setEnabled(self.undoStack.canUndo())
        self.redoAction.setEnabled(self.undoStack.canRedo())

    def updateSelectionAfterUndoRedo(self):
        """ Update selection of items after undo/redo """
        print("Updating selection after undo/redo.")
        # Here, implement any additional logic to update selection if necessary.

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
                self.parentFileWindow.isEdited = True
            else:
                skipper+=1
            self.undoStack.setIndex(currentIndex-i)
            self.parentFileWindow.isEdited = True
            i+=1
            