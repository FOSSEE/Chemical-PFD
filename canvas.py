from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsScene, QMenu, QGraphicsView


from shapes import NodeItem


class Canvas(QGraphicsScene):
    MoveItem, InsertLine = 1, 2
    myMode = MoveItem

    def __init__(self, parent=None):
        QGraphicsScene.__init__(self, parent)
        self.lines = []
        self.circles = []

    def setMode(self, mode):
        """This function is used to toggle between move and add line
        :return:
        """
        Canvas.myMode = mode


