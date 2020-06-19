from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import (
    QBrush, QImage, QPainter, QPainterPath, QPen, QPixmap, QTransform)
from PyQt5.QtSvg import QGraphicsSvgItem
from PyQt5.QtWidgets import (QBoxLayout, QDialog, QFileDialog,
                             QGraphicsEllipseItem, QGraphicsItem,
                             QGraphicsScene, QGraphicsView, QGridLayout,
                             QLabel, QLineEdit, QPushButton, QInputDialog, QTextEdit)

from shapes import SizeGripItem, directionsEnum

from .app import fileImporter

class ShapeDialog(QDialog):
    
    def __init__(self, parent=None):
        super(ShapeDialog, self).__init__(parent)
        self.resize(500, 300)
        self.setWindowTitle("Add New Shapes")
        self.createLayout()
        self.graphic = None
        
    def createLayout(self):
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
        name = QFileDialog.getOpenFileName(self, 'Open SVG File', '', 'Scalable Vector Graphics (*svg)')
        if name:
            self.graphic = QGraphicsSvgItem(name[0])
            self.graphic.setZValue(-1)
            self.painter.addItem(self.graphic)
    
    def saveEvent(self):
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
        
        graphicRect = self.graphic.boundingRect()
        
        image = QImage(64, 64, QImage.Format_ARGB32)
        printer = QPainter(image)
        self.graphic.renderer().render(printer, graphicRect)
        printer.end()
        
        #save file
        name = QFileDialog.getSaveFileName(self, 'Save Icon', className, 'PNG (*.png)')
        if name:
            image.save(name[0], "PNG")
        else:
            return
        
        gripList = []
        x, y, w, h = graphicRect.getRect()
        for i in self.grips:
            pos = i.pos()
            entry = [abs((x-pos.x())/w), abs((y-pos.y())/h), i.location]
            if isinstance(i, gripRect):
                if i.location in ["top", "bottom"]:
                    entry.append(h)
                else:
                    entry.append(w)
            gripList.append(entry)

        temp = QDialog(self)
        tempLayout = QBoxLayout(QBoxLayout.TopToBottom)
        output = OutputBox(temp, f"""
        class {className}(NodeItem):
            def __init__(self):
                super({className}, self).__init__("svg/{category}/{name[0]}")
            self.grips = {gripList}
        """)
        tempLayout.addWidget(output)
        temp.setLayout(tempLayout)
        temp.exec()
      
    @property
    def grips(self):
        return [i for i in self.painter.items() if isinstance(i, gripAbstract)]
    
    def addGrip(self):
        grip = gripDot()
        self.painter.addItem(grip)
    
    def addLineGrip(self):
        rect = gripRect()
        self.painter.addItem(rect)

class gripAbstract(QGraphicsItem):
    
    def __init__(self):
        super(gripAbstract, self).__init__()
        self.location = "top"
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        
    def mouseDoubleClickEvent(self, event):
        self.location, _ = QInputDialog.getItem(None, "Change location", "Select location", directionsEnum,
                                                     directionsEnum.index(self.location), False)   
        
class gripRect(gripAbstract):
    def __init__(self, x=0, y=0, w=80, h=10 ):
        super(gripRect, self).__init__()
        self.rotation = 0
        self.sizeGripItems = []
        self.width = w
        self.height = h
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
    def boundingRect(self):
        return QRectF(-self.width / 2, -self.height / 2, self.width, self.height)
    
    def paint(self, painter, option, index):
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.red))
        painter.drawRect(self.boundingRect())
        
    def addGripItems(self):
        for i, (direction) in enumerate((Qt.Vertical,
                                        Qt.Horizontal,
                                        Qt.Vertical,
                                        Qt.Horizontal)):
            self.sizeGripItems.append(SizeGripItem(i, direction, parent=self))
            
    def updateSizeGripItem(self, index_no_updates=None):
        index_no_updates = index_no_updates or []
        for i, item in enumerate(self.sizeGripItems):
            if i not in index_no_updates:
                item.updatePosition()
    
    def itemChange(self, change, value):
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
    def boundingRect(self):
        return QRectF(0, 0, 10, 10)
    
    def paint(self, painter, option, index):
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.red))
        painter.drawEllipse(self.boundingRect())
        
class OutputBox(QTextEdit):
    
    def __init__(self, parent, text):
        super(OutputBox, self).__init__(parent)
        self.setReadOnly(True)
        self.resize(600, 300)
        self.text = text
        self.setMarkdown("```python\n"+text+"\n```")