from PyQt5.QtCore import Qt, QRect, QPoint, QSize
from PyQt5.QtWidgets import QLayout, QSizePolicy

class flowLayout(QLayout):
    """
    Custom layout that flows horizontally first, then vertically.
    From Qt examples.
    """
    def __init__(self, parent=None, margin=0, spacing=12):
        super(flowLayout, self).__init__(parent)

        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)

        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        # Delete layout call
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        # add item to layout
        self.itemList.append(item)

    def count(self):
        # return a list of items
        return len(self.itemList)

    def itemAt(self, index):
        # return item at index
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        # pop item at index
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        # define orientation
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        # height for width flag, height value for a particular width
        return True

    def heightForWidth(self, width):
        # returns the height for a given width
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        # change layout geometry
        super(flowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)
        
    def sizeHint(self):
        # returns the expected size
        return self.minimumSize()

    def minimumSize(self):
        # calucalate minimum possible size below which, resize is impossible
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        margin, _, _, _ = self.getContentsMargins()

        size += QSize(2 * margin, 2 * margin)
        return size

    def doLayout(self, rect, testOnly):
        # build layout, testOnly defines if the geometry needs to be changed or not
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(QSizePolicy.ToolButton, QSizePolicy.ToolButton, Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(QSizePolicy.ToolButton, QSizePolicy.ToolButton, Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX + spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()
