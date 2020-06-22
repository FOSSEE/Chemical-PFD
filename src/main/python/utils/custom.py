"""
Holds the custom window to generate new symbols, can be called while running or throught the build interface.
"""
from PyQt5.QtCore import QRectF, Qt, QSize
from PyQt5.QtGui import (QBrush, QIcon, QImage, QPainter, QPainterPath, QPen,
                         QPixmap, QTransform)
from PyQt5.QtSvg import QGraphicsSvgItem
from PyQt5.QtWidgets import (QBoxLayout, QDialog, QFileDialog,
                             QGraphicsEllipseItem, QGraphicsItem,
                             QGraphicsScene, QGraphicsView, QGridLayout,
                             QInputDialog, QLabel, QLineEdit, QPushButton,
                             QTextEdit)

from shapes import SizeGripItem, directionsEnum

from .app import fileImporter

class ShapeDialog(QDialog):
    """
    The main dialog box for the custom symbol window.
    """
    def __init__(self, parent=None):
        super(ShapeDialog, self).__init__(parent)
        self.resize(500, 300) # resize to a fixed dim
        self.setWindowTitle("Add New Shapes")
        self.createLayout()
        self.graphic = None
        
    def createLayout(self):
        #build layout for the dialog box
        importButton = QPushButton("Import", self)
        importButton.clicked.connect(self.importSVG)
        
        saveButton = QPushButton("Save", self)
        saveButton.clicked.connect(self.saveEvent)
        
        self.symbolName = QLineEdit(self)
        self.symbolName.setPlaceholderText("Enter Symbol Name")
        symbolNameLabel = QLabel("Symbol Name")
        symbolNameLabel.setBuddy(self.symbolName)
        
        self.symbolClass = QLineEdit(self)
        self.symbolClass.setPlaceholderText("Enter Symbol Class Name")
        symbolClassLabel = QLabel("Symbol Class Name")
        symbolClassLabel.setBuddy(self.symbolClass)
        
        self.symbolCategory = QLineEdit(self)
        self.symbolCategory.setPlaceholderText("Enter Symbol Category")
        symbolCategoryLabel = QLabel("Symbol Category")
        symbolCategoryLabel.setBuddy(self.symbolCategory)
        
        addGripItem = QPushButton("Add Grip Item", self)
        addGripItem.clicked.connect(self.addGrip)
        addLineGripItem = QPushButton("Add Line Grip Item", self)
        addLineGripItem.clicked.connect(self.addLineGrip)
        
        self.painter = QGraphicsScene()
        view = QGraphicsView(self.painter)
        
        layout = QGridLayout(self)
        
        subLayout = QBoxLayout(QBoxLayout.LeftToRight)
        subLayout.addWidget(importButton)
        subLayout.addWidget(saveButton)
        subLayout.addStretch(1)
        
        layout.addLayout(subLayout, 0, 0, 1, -1)
        
        subLayout2 = QBoxLayout(QBoxLayout.LeftToRight)
        subLayout2.addWidget(view, stretch=1)
        
        subLayout3 = QBoxLayout(QBoxLayout.TopToBottom)
        subLayout3.addWidget(symbolNameLabel)
        subLayout3.addWidget(self.symbolName)
        subLayout3.addWidget(symbolClassLabel)
        subLayout3.addWidget(self.symbolClass)
        subLayout3.addWidget(symbolCategoryLabel)
        subLayout3.addWidget(self.symbolCategory)
        subLayout3.addStretch(1)
        subLayout3.addWidget(addGripItem)
        subLayout3.addWidget(addLineGripItem)
        subLayout2.addLayout(subLayout3)
        
        layout.addLayout(subLayout2, 1, 0, -1, -1)
        self.setLayout(layout)
        
    def importSVG(self):
        # Imports svg file through user input, adds it to the scene and stores it as a reference
        self.name = QFileDialog.getOpenFileName(self, 'Open SVG File', '', 'Scalable Vector Graphics (*svg)')
        if self.name:
            self.graphic = QGraphicsSvgItem(self.name[0])
            self.graphic.setZValue(-1)
            self.painter.addItem(self.graphic)
    
    def saveEvent(self):
        # executes the build procedure
        
        #check if all necessary values are there, each is seperate to show qalerts later on
        if self.graphic is None:
            return
        
        itemName = self.symbolName.text()
        if itemName is '':
            return
        
        className = self.symbolClass.text()
        if className is '':
            return

        category = self.symbolCategory.text()
        if category == "":
            category = "misc"
        
        # get rect for calculating grip positions
        graphicRect = self.graphic.boundingRect()

        #save file
        name = QFileDialog.getSaveFileName(self, 'Save Icon', className, 'PNG (*.png)')
        if name:
            QIcon(self.name[0]).pixmap(QSize(64, 64)).toImage().save(name[0])
        else:
            return
        
        #calculate grip positions and build a list
        gripList = []
        x, y, w, h = graphicRect.getRect()
        for i in self.grips:
            pos = i.pos()
            entry = [abs((x-pos.x())/w)*100, abs((y-pos.y())/h)*100, i.location]
            if isinstance(i, gripRect):
                if i.location in ["top", "bottom"]:
                    entry.append(i.height)
                else:
                    entry.append(i.width)
            gripList.append(entry)

        # format list in class definition flavor
        grips = ",\n    ".join([str(i) for i in gripList]) if gripList else ""
        if grips:
            grips = "self.grips = [" + grips + "]\n"
        
        # build output dialog box
        temp = QDialog(self)
        tempLayout = QBoxLayout(QBoxLayout.TopToBottom)
        output = OutputBox(temp, f"""
<b> Class Definition:</b>
<pre>
class {className}(NodeItem):
    def __init__(self):
        super({className}, self).__init__("svg/{category}/{str.split(name[0], "/")[-1][:-4]}")
    {grips}
</pre>
<b> Items.json entry:</b>
<pre>
"{category}": {{
    "{itemName}": {{
        "name": "{itemName}",
        "icon": ".\\{category}\\{str.split(name[0], "/")[-1]}",
        "class": "{category}",
        "object": "{className}",
        "args": []
    }}
}}</pre>""")
        tempLayout.addWidget(output)
        temp.setLayout(tempLayout)
        temp.exec()
      
    @property
    def grips(self):
        return [i for i in self.painter.items() if isinstance(i, gripAbstract)]
    
    def addGrip(self):
        #adds a grip dot to the scene
        grip = gripDot()
        self.painter.addItem(grip)
    
    def addLineGrip(self):
        #adds a line grip item
        rect = gripRect()
        self.painter.addItem(rect)

class gripAbstract(QGraphicsItem):
    """
    Abstract class for mouse click behaviour
    """
    def __init__(self):
        super(gripAbstract, self).__init__()
        self.location = "top"
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        
    def mouseDoubleClickEvent(self, event):
        self.location, _ = QInputDialog.getItem(None, "Change location", "Select location", directionsEnum,
                                                     directionsEnum.index(self.location), False)   
        
class gripRect(gripAbstract):
    """
    simulates line grip item with resizeablity
    (Haha grip items on grip items. Progress)
    """
    def __init__(self, x=0, y=0, w=80, h=10 ):
        super(gripRect, self).__init__()
        self.rotation = 0
        self.sizeGripItems = []
        self.width = w
        self.height = h
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
    
    #bounding rect and paint need to be implemented 
    def boundingRect(self):
        return QRectF(-self.width / 2, -self.height / 2, self.width, self.height)
    
    def paint(self, painter, option, index):
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.red))
        painter.drawRect(self.boundingRect())
       
    def addGripItems(self):
        # adds the resizeable line grip items from the shape file :D
        for i, (direction) in enumerate((Qt.Vertical,
                                        Qt.Horizontal,
                                        Qt.Vertical,
                                        Qt.Horizontal)):
            self.sizeGripItems.append(SizeGripItem(i, direction, parent=self))
            
    def updateSizeGripItem(self, index_no_updates=None):
        #update positions for existing grip items
        index_no_updates = index_no_updates or []
        for i, item in enumerate(self.sizeGripItems):
            if i not in index_no_updates:
                item.updatePosition()
    
    def itemChange(self, change, value):
        #do the needful when item is updated
        if change == QGraphicsItem.ItemPositionHasChanged:
            # update grips
            self.updateSizeGripItem()
            return
        # check if item is add on scene
        if change == QGraphicsItem.ItemSceneHasChanged and self.scene():
            # add grips and update them
            self.addGripItems()
            self.updateSizeGripItem()
            return
        return super(gripRect, self).itemChange(change, value)
    
    def resize(self, index, movement):
        #resize method
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

class gripDot(gripAbstract):
    """
    class for circular grips
    """      
    def boundingRect(self):
        return QRectF(0, 0, 10, 10)
    
    def paint(self, painter, option, index):
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.red))
        painter.drawEllipse(self.boundingRect())
        
class OutputBox(QTextEdit):
    """
    Defines a read only text box for class output
    """
    def __init__(self, parent, text):
        super(OutputBox, self).__init__(parent)
        self.setReadOnly(True)
        self.setFontWeight(10)
        self.setHtml(text)
        
def main():     # 1. Instantiate ApplicationContext
    #if app is launched directly
    from .app import app
    import sys
    main = ShapeDialog()
    main.show()
    exit_code = app.app.exec_()      # 2. Invoke app.app.exec_()
    sys.exit(exit_code)