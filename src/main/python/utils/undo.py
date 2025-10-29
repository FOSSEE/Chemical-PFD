"""
Contains custom undo commands that can be pushed to undo stack
"""
from PyQt5.QtWidgets import QUndoCommand
from re import compile
import shapes

def repl(x):
    return f"{x[0][0]} {x[0][1].lower()}"

regex = compile(r"([a-z][A-Z])")

def objectName(obj):
    name = regex.sub(repl, obj.m_type if obj.__class__.__name__ == 'NodeItem' else obj.__class__.__name__)
    return name[0].upper() + name[1:] + ' symbol'

# ------------------------- Add Command -------------------------
class addCommand(QUndoCommand):
    """
    QUndoCommand for add item event
    """
    def __init__(self, addItem, scene, parent=None, parentFileWindow=None):
        super().__init__(parent)
        self.scene = scene
        self.diagramItem = addItem
        self.itemPos = addItem.pos()
        if issubclass(self.diagramItem.__class__, shapes.Line) and addItem is not None:
            self.startGripItem = addItem.startGripItem.parentItem()
            self.endGripItem = addItem.endGripItem.parentItem()
            self.indexLGS, self.indexLGE = self.findLGIndex()
        self.setText(f"Add {objectName(self.diagramItem)} at {self.itemPos.x()}, {self.itemPos.y()}")
        self.parentFileWindow = parentFileWindow
        print(f"[DEBUG] Created AddCommand for {self.diagramItem}")

    def undo(self):
        if self.diagramItem in self.scene.items():
            self.scene.removeItem(self.diagramItem)
            self.scene.update()
            self.scene.advance()
            self.parentFileWindow.isEdited = True
            print(f"[DEBUG] Undo AddCommand: Removed {self.diagramItem}")

    def redo(self):
        if self.diagramItem not in self.scene.items():
            self.scene.addItem(self.diagramItem)
            self.diagramItem.setPos(self.itemPos)
            self.scene.clearSelection()
            self.scene.advance()
            if issubclass(self.diagramItem.__class__, shapes.Line):
                self.reconnectLines()
            self.parentFileWindow.isEdited = True
            print(f"[DEBUG] Redo AddCommand: Added {self.diagramItem} at {self.itemPos}")

    def findLGIndex(self):
        startIndex = None
        endIndex = None
        for indexLG, i in enumerate(self.startGripItem.lineGripItems):
            for j in i.lines:
                if j == self.diagramItem:
                    startIndex = indexLG
        for indexLG, i in enumerate(self.endGripItem.lineGripItems):
            for j in i.lines:
                if j == self.diagramItem:
                    endIndex = indexLG
        return startIndex, endIndex

    def reconnectLines(self):
        if self.diagramItem not in self.startGripItem.lineGripItems[self.indexLGS].lines:
            self.startGripItem.lineGripItems[self.indexLGS].lines.append(self.diagramItem)
        if self.diagramItem not in self.endGripItem.lineGripItems[self.indexLGE].lines:
            self.endGripItem.lineGripItems[self.indexLGE].lines.append(self.diagramItem)
        print(f"[DEBUG] Reconnected lines for {self.diagramItem}")

# ------------------------- Delete Command -------------------------
class deleteCommand(QUndoCommand):
    """
    QUndoCommand for delete item event
    """
    def __init__(self, item, scene, parent=None, parentFileWindow=None):
        super().__init__(parent)
        self.scene = scene
        item.setSelected(False)
        self.diagramItem = item
        if issubclass(self.diagramItem.__class__, shapes.Line):
            self.startGripItem = item.startGripItem.parentItem()
            self.endGripItem = item.endGripItem.parentItem()
            self.indexLGS, self.indexLGE = self.findLGIndex()
        self.setText(f"Delete {objectName(self.diagramItem)} at {self.diagramItem.pos().x()}, {self.diagramItem.pos().y()}")
        self.parentFileWindow = parentFileWindow
        print(f"[DEBUG] Created DeleteCommand for {self.diagramItem}")

    def undo(self):
        if self.diagramItem not in self.scene.items():
            self.scene.addItem(self.diagramItem)
            self.scene.update()
            self.scene.advance()
            self.scene.reInsertLines()
            if issubclass(self.diagramItem.__class__, shapes.Line):
                self.reconnectLines()
            self.parentFileWindow.isEdited = True
            print(f"[DEBUG] Undo DeleteCommand: Re-added {self.diagramItem}")

    def redo(self):
        if self.diagramItem in self.scene.items():
            self.scene.removeItem(self.diagramItem)
            self.scene.advance()
            self.parentFileWindow.isEdited = True
            print(f"[DEBUG] Redo DeleteCommand: Removed {self.diagramItem}")

    def findLGIndex(self):
        startIndex = None
        endIndex = None
        for indexLG, i in enumerate(self.startGripItem.lineGripItems):
            for j in i.lines:
                if j == self.diagramItem:
                    startIndex = indexLG
        for indexLG, i in enumerate(self.endGripItem.lineGripItems):
            for j in i.lines:
                if j == self.diagramItem:
                    endIndex = indexLG
        return startIndex, endIndex

    def reconnectLines(self):
        if self.diagramItem not in self.startGripItem.lineGripItems[self.indexLGS].lines:
            self.startGripItem.lineGripItems[self.indexLGS].lines.append(self.diagramItem)
        if self.diagramItem not in self.endGripItem.lineGripItems[self.indexLGE].lines:
            self.endGripItem.lineGripItems[self.indexLGE].lines.append(self.diagramItem)
        print(f"[DEBUG] Reconnected lines for {self.diagramItem}")

# ------------------------- Move Command -------------------------
class moveCommand(QUndoCommand):
    """
    QUndoCommand for move item event
    """
    def __init__(self, item, lastPos, parent=None, parentFileWindow=None):
        super().__init__(parent)
        self.diagramItem = item
        self.lastPos = lastPos
        self.newPos = item.pos()
        self.parentFileWindow = parentFileWindow
        print(f"[DEBUG] Created MoveCommand for {self.diagramItem} from {self.lastPos} to {self.newPos}")

    def undo(self):
        self.diagramItem.setPos(self.lastPos)
        self.diagramItem.scene().update()
        self.setText(f"Move {objectName(self.diagramItem)} to {self.newPos.x()}, {self.newPos.y()}")
        self.parentFileWindow.isEdited = True
        print(f"[DEBUG] Undo MoveCommand: {self.diagramItem} moved back to {self.lastPos}")

    def redo(self):
        self.diagramItem.setPos(self.newPos)
        self.setText(f"Move {objectName(self.diagramItem)} to {self.newPos.x()}, {self.newPos.y()}")
        self.parentFileWindow.isEdited = True
        print(f"[DEBUG] Redo MoveCommand: {self.diagramItem} moved to {self.newPos}")

    def mergeWith(self, move):
        item = move.diagramItem
        if self.diagramItem != item:
            return False
        self.newPos = item.pos()
        self.setText(f"Move {objectName(self.diagramItem)} to {self.newPos.x()}, {self.newPos.y()}")
        self.parentFileWindow.isEdited = True
        print(f"[DEBUG] Merged MoveCommand: {self.diagramItem} to {self.newPos}")
        return True

# ------------------------- Resize Command -------------------------
class resizeCommand(QUndoCommand):
    """
    Defines the resize event for the custom scene.
    """
    def __init__(self, new, canvas, widget, parent=None, parentFileWindow=None):
        super().__init__(parent)
        self.parent = canvas
        self.old = self.parent.canvasSize, self.parent.ppi, self.parent.landscape
        self.new = new
        self.widget = widget
        self.setText(f'Change canvas dimensions to {new[0]} at {new[1]} ppi')
        self.parentFileWindow = parentFileWindow
        print(f"[DEBUG] Created ResizeCommand: {self.old} -> {self.new}")

    def undo(self):
        self.parent.canvasSize, self.parent.ppi, self.parent.landscape = self.old
        self.widget.resizeHandler()
        self.parentFileWindow.isEdited = True
        print(f"[DEBUG] Undo ResizeCommand: Canvas restored to {self.old}")

    def redo(self):
        self.parent.canvasSize, self.parent.ppi, self.parent.landscape = self.new
        self.widget.resizeHandler()
        self.parentFileWindow.isEdited = True
        print(f"[DEBUG] Redo ResizeCommand: Canvas resized to {self.new}")
