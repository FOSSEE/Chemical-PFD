import sys
from random import randint, random

from PyQt5.QtGui import QIcon
from PyQt5.QtSvg import QSvgRenderer, QGraphicsSvgItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QGraphicsView, QAction, QToolButton, \
    QButtonGroup, QMessageBox, QLayout, QVBoxLayout, QLabel, QToolBar
from PyQt5.QtCore import QRectF, QFileInfo, QPoint, QRect, QSize,Qt

from canvas import Canvas
from shapes import NodeItem



class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("Connecting Circles")
        self.InitWindow()

    def InitWindow(self):
        self.createActions()
        self.createToolbars()


        desktop = app.desktop()
        self.scene = Canvas()
        self.scene.setSceneRect(0, 0,200,200 )

        self.view = QGraphicsView()
        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)
        self.show()
        self.setGeometry(800,200,800,800)

    def pointerGroupClicked(self):
        """Toggle between pointer
        and line pointer
        """
        Canvas.myMode = self.connectionTypeGroup.checkedId()

    def createActions(self):
        """This function is used to create
            action for toolbar button
        :return:
        """
        self.addAction = QAction(QIcon('images/add.png'), "Add Item", self)
        self.addAction.triggered.connect(self.addNodeItem)

        self.deleteAction = QAction(QIcon('images/delete.png'), "Delete circle", self)
        self.deleteAction.triggered.connect(self.deleteCircle)

        # self.generateReportAction = QAction(QIcon('images/report.gif'), "Generate Report", self)
        # self.generateReportAction.triggered.connect(self.saveAsPdf)
        #
        # self.saveAction = QAction(QIcon('images/image.png'), "Save", self)
        # self.saveAction.triggered.connect(self.saveAsPng)

    def createToolbars(self):
        self.editToolBar = QToolBar('edit tool bar')
        self.addToolBar( Qt.RightToolBarArea, self.editToolBar)
        # self.editToolBar = self.addToolBar("Edit")
        # self.editToolBar.setFixedWidth(100)
        self.editToolBar.setIconSize(QSize(50, 50))
        self.editToolBar.addAction(self.addAction)
        self.editToolBar.addAction(self.deleteAction)
        # self.editToolBar.addAction(self.generateReportAction)
        # self.editToolBar.addAction(self.saveAction)
        # self.editToolBar.setMovable(False)

        pointerButton = QToolButton()
        pointerButton.setCheckable(True)
        pointerButton.setChecked(True)
        pointerButton.setIcon(QIcon('images/pointer.png'))
        linePointerButton = QToolButton()
        linePointerButton.setCheckable(True)
        linePointerButton.setIcon(QIcon('images/linepointer.png'))

        self.connectionTypeGroup = QButtonGroup()
        self.connectionTypeGroup.addButton(pointerButton, Canvas.MoveItem)
        self.connectionTypeGroup.addButton(linePointerButton, Canvas.InsertLine)
        self.connectionTypeGroup.buttonClicked[int].connect(self.pointerGroupClicked)

        # self.lineToolbar = self.addToolBar("Pointer type")
        self.lineToolbar = QToolBar('pointer type')
        self.addToolBar(  Qt.RightToolBarArea, self.lineToolbar)
        # self.lineToolbar.setFixedHeight(100)
        self.lineToolbar.setIconSize(QSize(50, 50))
        self.lineToolbar.addWidget(linePointerButton)
        self.lineToolbar.addWidget(pointerButton)
        # self.lineToolbar.setMovable(False)

    def addNodeItem(self):
        """This function is used to add circle to canvas
        :return:
        """

        item = NodeItem('Pump')
        item.addOnCanvas(self.scene)



        # renderer = QSvgRenderer('svg/Bag.svg')
        # black = QGraphicsSvgItem()
        # black.setSharedRenderer(renderer)
        # black.setElementId('g12968')
        # print(black.boundingRect())
        #
        # self.scene.addItem(black)









    def deleteCircle(self):
        """This function is used to delete all selected circle
        :return:
        """
        circles = self.scene.selectedItems()
        for circle in circles:
            circle.removeFromCanvas()



if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        application = Window()
        # application.showMaximized()
        sys.exit(app.exec())
    except Exception as e:
        print(e)
