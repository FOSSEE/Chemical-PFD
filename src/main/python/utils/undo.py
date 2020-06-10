"""
Contains custom undo commands that can be pushed to undo stack
"""
from PyQt5.QtWidgets import QUndoCommand
from re import compile

def repl(x):
    return f"{x[0][0]} {x[0][1].lower()}"

regex = compile(r"([a-z][A-Z])")

def objectName(obj):
    name = regex.sub(repl, obj.m_type if obj.__class__.__name__ == 'NodeItem' else obj.__class__.__name__)
    # if obj.__class__.__name__ != 'line':
    #     name = 'Draw ' + name[0].upper() + name[1:]
    # else:
    #     name = 'Add ' + 
    return name[0].upper() + name[1:] + ' symbol'

class addCommand(QUndoCommand):
    """
    QUndoCommand for add item event
    """
    def __init__(self, addItem, scene, parent = None):
        super(addCommand, self).__init__(parent)
        self.scene = scene
        self.diagramItem = addItem
        self.itemPos = addItem.pos()
        self.setText(f"Add {objectName(self.diagramItem)}")
        
    def undo(self):
        self.scene.removeItem(self.diagramItem)
        self.scene.update()
        self.scene.advance()
        
    def redo(self):
        self.scene.addItem(self.diagramItem)
        self.diagramItem.setPos(self.itemPos)
        self.scene.clearSelection()
        self.scene.advance()
        
class deleteCommand(QUndoCommand):
    """
    QUndoCommand for delete item event
    """
    def __init__(self, item, scene, parent = None):
        super(deleteCommand, self).__init__(parent)
        self.scene = scene
        item.setSelected(False)
        self.diagramItem = item
        self.setText(f"Delete {objectName(self.diagramItem)} at {self.diagramItem.pos().x()}, {self.diagramItem.y()}")
        
    def undo(self):
        self.scene.addItem(self.diagramItem)
        self.scene.update()
        self.scene.advance()
        
    def redo(self):
        self.scene.removeItem(self.diagramItem)
        self.scene.advance()
        
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
        self.setText(f"Move {objectName(self.diagramItem)} to {self.newPos.x()}, {self.newPos.y()}")
        
    def redo(self):
        self.diagramItem.setPos(self.newPos)
        self.setText(f"Move {objectName(self.diagramItem)} to {self.newPos.x()}, {self.newPos.y()}")
        
    def mergeWith(self, move):
        #merges multiple move commands so that a move event is not added twice.
        item = move.diagramItem
        
        if self.diagramItem != item:
            return False
        
        self.newPos = item.pos()
        self.setText(f"Move {objectName(self.diagramItem)} to {self.newPos.x()}, {self.newPos.y()}")
        return True
    
class resizeCommand(QUndoCommand):
    """
    """
    def __init__(self, new, canvas, widget, parent = None):
        super(resizeCommand, self).__init__(parent)
        self.parent = canvas
        self.old = self.parent.canvasSize, self.parent.ppi
        self.new = new
        self.widget = widget
        self.setText(f'Change canvas dimensions to {new[0]} at {new[1]} ppi')
    
    def undo(self):
        self.parent.canvasSize, self.parent.ppi = self.old
        self.widget.resizeHandler()
    
    def redo(self):
        self.parent.canvasSize, self.parent.ppi = self.new
        self.widget.resizeHandler()