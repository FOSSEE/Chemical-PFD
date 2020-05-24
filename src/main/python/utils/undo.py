"""
Contains custom undo commands that can be pushed to undo stack
"""
from PyQt5.QtWidgets import QUndoCommand

class addCommand(QUndoCommand):
    """
    QUndoCommand for add item event
    """
    def __init__(self, addItem, scene, parent = None):
        super(addCommand, self).__init__(parent)
        self.scene = scene
        self.diagramItem = addItem
        self.itemPos = addItem.pos()
        self.setText(f"Add {self.diagramItem} {self.itemPos}")
        
    def undo(self):
        self.scene.removeItem(self.diagramItem)
        self.scene.update()
        
    def redo(self):
        self.scene.addItem(self.diagramItem)
        self.diagramItem.setPos(self.itemPos)
        self.scene.clearSelection()
        self.scene.update()
        
class deleteCommand(QUndoCommand):
    """
    QUndoCommand for delete item event
    """
    def __init__(self, item, scene, parent = None):
        super(deleteCommand, self).__init__(parent)
        self.scene = scene
        item.setSelected(False)
        self.diagramItem = item
        self.setText(f"Delete {self.diagramItem} {self.diagramItem.pos()}")
        
    def undo(self):
        self.scene.addItem(self.diagramItem)
        self.scene.update()
        
    def redo(self):
        self.scene.removeItem(self.diagramItem)
        
class moveCommand(QUndoCommand):
    """
    QUndoCommand for move item event
    """
    def __init__(self, item, lastPos, parent = None):
        super(moveCommand, self).__init__(parent)
        self.diagramItem = item
        self.lastPos = lastPos
        self.newPos = item.pos()
        
    def undo(self):
        self.diagramItem.setPos(self.lastPos)
        self.diagramItem.scene().update()
        self.setText(f"Move {self.diagramItem} {self.newPos}")
        
    def redo(self):
        self.diagramItem.setPos(self.newPos)
        self.setText(f"Move {self.diagramItem} {self.newPos}")
        
    def mergeWith(self, move):
        #merges multiple move commands so that a move event is not added twice.
        item = move.diagramItem
        
        if self.diagramItem != item:
            return False
        
        self.newPos = item.pos()
        self.setText(f"Move {self.diagramItem} {self.newPos}")
        return True