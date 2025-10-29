import sys
import os
import ast
import shapes
import pickle
import json
import fitz  # PyMuPDF
import pandas as pd
from PyQt5.QtCore import QPointF
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QMessageBox, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from shapes import SizeGripItem, NodeItem, LineGripItem, GripItem  # Add other items as needed
from PyQt5.QtWidgets import QAction, QFileDialog
from docx import Document


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from shapes.shapes import NodeItem
from shapes.shapes import ItemLabel
from PyQt5.QtGui import QTextDocument
from utils.component_mapper import get_component_data
from PyQt5.QtWidgets import QGraphicsTextItem
from PyQt5.QtWidgets import QApplication
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtSvg import QGraphicsSvgItem  # Corrected: SVG item comes from QtSvg
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QSize, QPoint, QRectF
from PyQt5.QtGui import QBrush, QColor, QImage, QPainter, QPalette, QPen, QKeySequence, QFont
from PyQt5.QtWidgets import QUndoView
from PyQt5.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QVBoxLayout,
    QHBoxLayout, QLabel, QMainWindow, QMenu, QMessageBox,
    QPushButton, QWidget, QMdiArea, QSplitter, QGraphicsItem,
    QGraphicsTextItem
)
from PyQt5.QtWidgets import QMainWindow, QGraphicsView, QGraphicsScene, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel
import sys
from utils.graphics import CustomView, CustomScene
from utils.canvas import canvas
from utils.fileWindow import FileWindow
from utils.data import ppiList, sheetDimensionList
from utils.undo import addCommand, deleteCommand, moveCommand, resizeCommand
from utils import dialogs
from utils.toolbar import toolbar
from utils.app import settings
from PyQt5.QtWidgets import QApplication
from collections import defaultdict  
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QMdiArea, QMdiSubWindow, QVBoxLayout, QWidget, QSplitter, QMenuBar, QAction
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QUndoStack

class appWindow(QMainWindow):
    def __init__(self, parent=None):
        super(appWindow, self).__init__(parent)
        self.undoStack = QUndoStack(self)

        self.legend_counter = defaultdict(int)
        self.createMenuBar()

        self.counterr = 0
        self.mdi = QMdiArea(self)  # Create area for files to be displayed
        self.mdi.setObjectName('mdi area')
        self.setCentralWidget(self.mdi)
        self.toolbarWidget = self.createToolbar()
        self.toolbarWidget.populateToolbar()

        splitter = QSplitter()
        splitter.addWidget(self.toolbarWidget)  # Left: toolbar
        splitter.addWidget(self.mdi)            # Right: canvas
        splitter.setStretchFactor(1, 1)         # Canvas expands more
        
        self.mdi.setOption(QMdiArea.DontMaximizeSubWindowOnActivation, True) 
        self.mdi.setTabsClosable(True)
        self.mdi.setTabsMovable(True)
        self.mdi.setDocumentMode(False)
        
        centralWidget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        layout.setContentsMargins(0, 0, 0, 0)
        centralWidget.setLayout(layout)

        self.setCentralWidget(centralWidget)
        self.mdi.subWindowActivated.connect(self.tabSwitched)
        
        self.readSettings()

    def createGraphicItem(self, item_type, index=None, direction=Qt.Horizontal, grip=None):
        """
        This method creates and returns a corresponding QGraphicsItem based on the provided item_type.
    
        :param item_type: The type of item to create (e.g., "NodeItem", "LineItem", "SizeGripItem").
        :param index: The index for items that require it (e.g., SizeGripItem, LineGripItem).
        :param direction: The direction for items that require it (e.g., SizeGripItem).
        :param grip: The grip for LineGripItem (required for LineGripItem).
    
        :return: A QGraphicsItem of the specified type.
        """
    
        if item_type == "NodeItem":
            return NodeItem()  # Create and return a NodeItem
        
        elif item_type == "LineGripItem":
            if index is None or grip is None:
                raise ValueError("Both 'index' and 'grip' must be provided for LineGripItem.")
            return LineGripItem(index=index, grip=grip)  # Create and return LineGripItem
    
        elif item_type == "SizeGripItem":
            # Ensure index and direction are passed when creating SizeGripItem
            if index is None:
                index = 0  # Default value for index if not provided
            return SizeGripItem(index=index, direction=direction)  # Create and return SizeGripItem   

        elif item_type == "GripItem":
            return GripItem()  # Create and return a GripItem
    
        elif item_type == "ItemLabel":
            return ItemLabel()  # Create and return an ItemLabel
    
        else:
            raise ValueError(f"Unknown item type: {item_type}")

    def saveDiagram(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        filePath, selectedFilter = QFileDialog.getSaveFileName(
            self,
            "Save File",
            downloads_folder,  # Set default directory to Downloads
            "PDF File (*.pdf);;JPEG Image (*.jpg);;Process Flow Diagram (*.pfd)",
            options=options
        )
        if not filePath:
            return

        subwin = self.mdi.currentSubWindow()
        if not subwin or not hasattr(subwin, 'tabber'):
            QMessageBox.warning(self, "No Diagram", "No active diagram found.")
            return

        if selectedFilter == "PDF File (*.pdf)" or filePath.endswith(".pdf"):
            if not filePath.endswith(".pdf"):
                filePath += ".pdf"
            self.saveAsPDF(filePath)
        elif selectedFilter == "JPEG Image (*.jpg)" or filePath.endswith(".jpg"):
            if not filePath.endswith(".jpg"):
                filePath += ".jpg"
            self.saveAsJPG(filePath)
        elif selectedFilter == "Process Flow Diagram (*.pfd)" or filePath.endswith(".pfd"):
            if not filePath.endswith(".pfd"):
                filePath += ".pfd"
            self.saveAsCustom(filePath)  # Call your custom save method


    def saveAsPDF(self, filePath):
        subwin = self.mdi.currentSubWindow()
        if not subwin:
            return
        scene = subwin.tabber.currentWidget().painter
        if not scene.items():
            QMessageBox.warning(self, "No Diagram", "No diagram to save.")
            return
        rect = scene.itemsBoundingRect()
        if rect.isEmpty():
            QMessageBox.warning(self, "Nothing to Save", "Diagram is empty.")
            return
        padding_right = 100
        padding_bottom = 50
        rect.setWidth(rect.width() + padding_right)
        rect.setHeight(rect.height() + padding_bottom)
        scene.setSceneRect(rect)

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filePath)
        printer.setPageMargins(10, 10, 10, 10, QPrinter.Millimeter)
        printer.setPaperSize(QPrinter.A4)
        painter = QPainter(printer)
        if not painter.isActive():
            QMessageBox.critical(self, "Error", "Failed to open PDF file for writing.")
            return
        page_rect = printer.pageRect(QPrinter.DevicePixel)
        scale_x = page_rect.width() / rect.width()
        scale_y = page_rect.height() / rect.height()
        scale = min(scale_x, scale_y)

        painter.translate(page_rect.x(), page_rect.y())
        painter.scale(scale, scale)

        scene.render(painter, target=QtCore.QRectF(rect), source=rect)
        painter.end()

        QMessageBox.information(self, "Saved", f"PDF diagram saved to:\n{filePath}")


    def saveAsJPG(self, filePath):
        subwin = self.mdi.currentSubWindow()
        if not subwin:
            return
        scene = subwin.tabber.currentWidget().painter  
        if not scene.items():
            QMessageBox.warning(self, "No Diagram", "No diagram to save.")
            return
        rect = scene.itemsBoundingRect()
        if rect.isEmpty():
            QMessageBox.warning(self, "Nothing to Save", "Diagram is empty.")
            return
        image = QImage(rect.size().toSize(), QImage.Format_ARGB32)
        image.fill(Qt.white)

        painter = QPainter(image)
        scene.render(painter, QtCore.QRectF(image.rect()), rect)
        painter.end()
        image.save(filePath, "JPG")
        QMessageBox.information(self, "Saved", f"Diagram saved to:\n{filePath}") 

    from docx import Document

    def saveAsCustom(self, filePath):
        subwin = self.mdi.currentSubWindow()
        if not subwin or not hasattr(subwin, 'tabber'):
            QMessageBox.warning(self, "No Diagram", "No active diagram found.")
            return

        scene = subwin.tabber.currentWidget().painter
        diagram_data = []

        for item in scene.items():
            item_data = {
                'type': type(item).__name__,  # class name
                'pos': {'x': item.pos().x(), 'y': item.pos().y()},
                'label': getattr(item, 'labelText', ""),
            }
            if hasattr(item, '_m_index'):
                item_data['index'] = item._m_index
            if hasattr(item, '_direction'):
                item_data['direction'] = item._direction.name if hasattr(item._direction, 'name') else item._direction

            diagram_data.append(item_data)

        with open(filePath, 'w') as f:
            json.dump(diagram_data, f, indent=2)

        QMessageBox.information(self, "Saved", f"Diagram saved as PFD to:\n{filePath}")


    def handleGenerateReport(self):
        data = self.collectReportData()
        if not data:
            QMessageBox.warning(self, "No Data", "No components found to generate the report.")
            return

        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Report As",
            downloads_folder,  # Set default directory to Downloads
            "PDF Files (*.pdf);;Excel Files (*.xlsx)"
        )
        if not file_path:
            return
        if selected_filter == "PDF Files (*.pdf)" or file_path.endswith(".pdf"):
            if not file_path.endswith(".pdf"):
                file_path += ".pdf"
            self.generate_pdf_report(data, file_path)
        elif selected_filter == "Excel Files (*.xlsx)" or file_path.endswith(".xlsx"):
            if not file_path.endswith(".xlsx"):
                file_path += ".xlsx"
            self.exportReportAsExcel(file_path, data)
    
    def createMenuBar(self):
        titleMenu = self.menuBar()

        # File Menu
        self.menuFile = titleMenu.addMenu('File')
        newAction = self.menuFile.addAction("New", self.newProject)
        openAction = self.menuFile.addAction("Open", self.openFile)
        saveAction = self.menuFile.addAction("Save", self.saveDiagram)

        newAction.setShortcut(QKeySequence.New)
        openAction.setShortcut(QKeySequence.Open)
        saveAction.setShortcut(QKeySequence.Save)

        self.menuEdit = titleMenu.addMenu('Edit')
        undoAction = self.undo = self.menuEdit.addAction(
            "Undo", lambda x=self: x.activeScene.painter.undoAction.trigger()
        )
        redoAction = self.redo = self.menuEdit.addAction(
            "Redo", lambda x=self: x.activeScene.painter.redoAction.trigger()
        )

        undoAction.setShortcut(QKeySequence.Undo)
        redoAction.setShortcut(QKeySequence.Redo)

        self.menuEdit.addAction("Show Undo Stack", lambda x=self: x.activeScene.painter.createUndoView(self))
        self.menuEdit.addSeparator()
        self.menuEdit.addAction("Add new symbols", self.addSymbolWindow)

        self.menuGenerate = titleMenu.addMenu('Generate')
        imageAction = self.menuGenerate.addAction("Image", self.saveImage)
        reportAction = self.menuGenerate.addAction("Report", self.handleGenerateReport)

        imageAction.setShortcut(QKeySequence("Ctrl+P"))
        reportAction.setShortcut(QKeySequence("Ctrl+R"))


    def createToolbar(self):
        self.toolbar = toolbar(self)
        self.toolbar.setObjectName("Toolbar")
        self.toolbar.setMinimumWidth(150)
        self.toolbar.setMaximumWidth(220)
        self.toolbar.setFloating(False)
        self.toolbar.toolbuttonClicked.connect(self.toolButtonClicked)
        self.toolbar.populateToolbar()
        return self.toolbar  # ✅ Important


    def toolButtonClicked(self, object):
        """Handle component addition to the canvas when a toolbar item is clicked."""
        if self.is_edit_mode and self.mdi.currentSubWindow():
            currentDiagram = self.mdi.currentSubWindow().tabber.currentWidget().painter  # Get the current scene
        
            try:
                cls = getattr(shapes, object['object'])  # Get the class from shapes dynamically
            except AttributeError:
                print(f"Error: '{object['object']}' not found in shapes.py")
                return
        
            graphic = cls(*object.get('args', []))
            graphic.setPos(50, 50)  # Example initial position for the new component
            name = object.get('name') or object['object']
            graphic.typeName = name  # Set the name/type of the item
        
            if isinstance(graphic, NodeItem):
                label = self.generateLabel(name)
                graphic.setLabelText(label)
                graphic.setData(0, label)
                label_item = ItemLabel(label, graphic)
                label_item.setParentItem(graphic)
                currentDiagram.addItem(label_item)
        
            currentDiagram.addItem(graphic)                          

            self.addGripsToDiagram(graphic)

    from PyQt5.QtWidgets import (QDialog,
        QFileDialog, QMessageBox, QMainWindow, QMdiArea, QVBoxLayout, QWidget, QMenuBar, QSplitter, 
        QHBoxLayout, QPushButton, QLabel, QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsTextItem
    )

    from PyQt5.QtGui import QPixmap, QImage
    import fitz  # PyMuPDF
    from collections import defaultdict
    from utils.custom import ShapeDialog
    from utils.fileWindow import FileWindow
    from utils.data import ppiList, sheetDimensionList
    from utils import dialogs
    from utils.toolbar import toolbar
    from utils.app import settings
    from PyQt5.QtCore import QTimer, Qt

    def generate_label(self, legend, suffix):
        """
        Generate label as Legend-Suffix-Count (or Legend-Count if suffix is empty).
        Example: C-A/B-01 or FT-01
        """
        key = f"{legend}-{suffix}"
        self.legend_counter[key] += 1
        count = self.legend_counter[key]

        if suffix:
            label = f"{legend}-{suffix}-{count:02d}"
        else:
            label = f"{legend}-{count:02d}"

        return label

    def addSymbolWindow(self):
        ShapeDialog(self).exec()

    def newProject(self):
        project = FileWindow(self.mdi)
        project.setObjectName("New Project")
        project.setWindowFlags(Qt.FramelessWindowHint)
        self.mdi.addSubWindow(project)

        def safe_new_diagram():
            try:
                if not project.tabList:
                    project.newDiagram()
                    project.resizeHandler() 
            except Exception as e:
                print(f"Error in newDiagram(): {e}")

        QTimer.singleShot(0, safe_new_diagram)
        project.fileCloseEvent.connect(self.fileClosed)  
        self.mdi.setViewMode(QMdiArea.TabbedView)
        project.show()

    from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication

    def openFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "All Files (*.*);;PDF File (*.pdf);;Image Files (*.jpg *.jpeg *.png);;Process Flow Diagram (*.pfd)",
            options=options
        )
        if not filePath:
            return

        ext = os.path.splitext(filePath)[1].lower()

        if ext == ".pfd":
            self.openPFD(filePath)
        elif ext in [".jpg", ".jpeg", ".png"]:
            self.openJPG(filePath)
        elif ext == ".pdf":
            self.openPDF(filePath)
        else:
            QMessageBox.warning(self, "Unsupported", f"Unsupported file type: {ext}")
            return

        self.repaint()
        QApplication.processEvents()

    def handlePDF(self, file):
        try:
            self.previewPDF(file)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load PDF: {e}")

    def handleJPG(self, file):
        print(f"Loading JPG: {file}")
        try:
            self.previewImage(file)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load JPG: {e}")

    def handlePFD(self, file):
        print(f"Loading PFD: {file}")
        try:
            self.previewPFD(file)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load PFD: {e}")


    import fitz
    from PyQt5.QtGui import QImage, QPixmap
    from PyQt5.QtWidgets import QGraphicsPixmapItem

    def openPDF(self, filePath):
        diagram = canvas(self.mdi, parentFileWindow=self)
        diagram.setObjectName(os.path.basename(filePath))

        pdf = fitz.open(filePath)
        page = pdf[0]

        zoom = 2.0 
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

        pixmap_item = QGraphicsPixmapItem(QPixmap.fromImage(image))
        diagram.painter.addItem(pixmap_item)

        subWin = self.mdi.addSubWindow(diagram)
        subWin.setWindowTitle(os.path.basename(filePath))
        subWin.show()

        
    def openJPG(self, filePath):
        diagram = canvas(self.mdi, parentFileWindow=self)
        diagram.setObjectName(os.path.basename(filePath))

        pixmap_item = QGraphicsPixmapItem(QPixmap(filePath))
        diagram.painter.addItem(pixmap_item)

        subWin = self.mdi.addSubWindow(diagram)
        subWin.setWindowTitle(os.path.basename(filePath))
        subWin.show()
       
    from docx import Document
    import ast

    def openPFD(self, filePath):
        try:
            with open(filePath, 'r') as f:
                diagram_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open PFD: {e}")
            return

        diagram = canvas(self.mdi, parentFileWindow=self)
        diagram.setObjectName(os.path.basename(filePath))

        for item_data in diagram_data:
            cls = globals().get(item_data['type'])
            if cls:
                kwargs = {}
                if 'index' in item_data:
                    kwargs['index'] = item_data['index']
                if 'direction' in item_data:
                    kwargs['direction'] = item_data['direction']

                item = cls(**kwargs) if kwargs else cls()
                item.setPos(item_data['pos']['x'], item_data['pos']['y'])
                if 'label' in item_data and hasattr(item, 'labelText'):
                    item.labelText = item_data['label']

                diagram.painter.addItem(item)

        subWin = self.mdi.addSubWindow(diagram)
        subWin.setWindowTitle(os.path.basename(filePath))
        subWin.show()


    def saveProject(self):
        """Save the current diagram to a file."""
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save Project', '', 'Process Flow Diagram (*.pfd);;All Files (*)')

        if file_path:
            try:
                scene = self.mdi.currentSubWindow().tabber.currentWidget().painter
                components = []
                for item in scene.items():
                    item_data = {
                        'type': item.__class__.__name__, 
                        'pos': (item.pos().x(), item.pos().y()), 
                        'text': item.toPlainText() if hasattr(item, 'toPlainText') else None, 
                        'label': item.label.toPlainText() if hasattr(item, 'label') else None, 
                    }
                    components.append(item_data)

                with open(file_path, 'wb') as f:
                    pickle.dump(components, f)
                print(f"Project saved to: {file_path}")
            except Exception as e:
                print(f"Error saving project: {e}")
                QMessageBox.warning(self, "Error", f"Failed to save project.\nError: {e}")
 
    def saveImage(self):
        current_sub_window = self.mdi.currentSubWindow()
        if not current_sub_window:
            QMessageBox.warning(self, "No Diagram", "No active diagram found to save.")
            return

        currentDiagram = current_sub_window.tabber.currentWidget().painter
        if not currentDiagram:
            QMessageBox.warning(self, "No Diagram", "No diagram to save as image.")
            return

        name, _ = QFileDialog.getSaveFileName(
            self,
            'Save File',
            f'New_Image_{self.counterr}',
            'PNG Files (*.png);;JPEG Files (*.jpg)'
        )
        if not name:
            return

        image = QImage(currentDiagram.sceneRect().size().toSize(), QImage.Format_ARGB32)
        image.fill(Qt.white) 
        painter = QPainter(image)
        currentDiagram.render(painter)
        painter.end()

        if image.save(name):
            self.counterr += 1
            QMessageBox.information(self, "Saved", f"Image saved successfully:\n{name}")
        else:
            QMessageBox.warning(self, "Error", f"Failed to save image:\n{name}")



    from PyQt5.QtPrintSupport import QPrinter
    from PyQt5.QtWidgets import QFileDialog, QMessageBox

    def generate_pdf_report(self, data, file_path):
        from PyQt5.QtGui import QTextDocument
        from PyQt5.QtPrintSupport import QPrinter

        html = "<h2>List of Equipment</h2><table border='1' cellspacing='0' cellpadding='4'>"
        html += "<tr><th>Sl No</th><th>Tag No</th><th>Type</th><th>Description</th></tr>"
        for row in data:
            html += f"<tr><td>{row['Sl No']}</td><td>{row['Tag No']}</td><td>{row['Type']}</td><td>{row['Description']}</td></tr>"
        html += "</table>"

        doc = QTextDocument()
        doc.setHtml(html)

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)
        printer.setPageMargins(12, 16, 12, 20, QPrinter.Millimeter)

        doc.print_(printer)
        QMessageBox.information(self, "Success", f"PDF report saved:\n{file_path}")


    def exportReportAsPDF(self, filePath, data):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as pdf_canvas

        c = pdf_canvas.Canvas(filePath, pagesize=A4)
        width, height = A4

        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, height - 50, "LIST OF EQUIPMENT")

        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, height - 80, "Sl No")
        c.drawString(100, height - 80, "Tag No")
        c.drawString(250, height - 80, "Type")
        c.drawString(450, height - 80, "Description")

        c.setFont("Helvetica", 10)
        y = height - 100
        line_height = 20  
        for row in data:
            c.drawString(50, y, str(row["Sl No"]))
            c.drawString(100, y, row["Tag No"])
            c.drawString(250, y, row["Type"])
            c.drawString(450, y, row["Description"])
            y -= line_height
            if y < 100:  
                c.showPage()  
                y = height - 50
                c.setFont("Helvetica-Bold", 10)
                c.drawString(50, y, "Sl No")
                c.drawString(100, y, "Tag No")
                c.drawString(250, y, "Type")
                c.drawString(450, y, "Description")
                y -= line_height


    def exportReportAsExcel(self, filePath, data):
        import pandas as pd

        df = pd.DataFrame(data)
        try:
            df.to_excel(filePath, index=False)
            QMessageBox.information(self, "Saved", f"Excel Report saved to:\n{filePath}")
            print("Generating Excel report at:", filePath)
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Error", f"Failed to save the Excel report:\n{e}")



    def collectReportData(self):
        subwin = self.mdi.currentSubWindow()
        if not subwin:
            return []
        scene = subwin.tabber.currentWidget().painter
        if not scene:
            return []
        data = []
        sl_no = 1
        for item in reversed(scene.items()):
            if not isinstance(item, NodeItem):
                continue

            typeName = getattr(item, 'typeName', None)
            label = getattr(item, "label", None)  

            if not label or not typeName:
                continue

            data.append({
                "Sl No": sl_no,
                "Tag No": label,
                "Type": typeName,
                "Description": ""
            })
            sl_no += 1

        return data

    def tabSwitched(self, window):
        if not window:
            return

        widget = window.widget() 

        if hasattr(widget, "tabCount") and callable(getattr(widget, "tabCount")):
            if widget.tabCount(): 
                if hasattr(widget, "resizeHandler"):
                    widget.resizeHandler()


    def resizeEvent(self, event):
        for i in self.mdi.subWindowList():
            i.resizeHandler()
        self.toolbar.resize()
        super(appWindow, self).resizeEvent(event)
                
    def closeEvent(self, event):
        if len(self.activeFiles) and not dialogs.saveEvent(self):
            event.ignore()
        else:
            event.accept()
        self.writeSettings()  
    
    def fileClosed(self, index):
        pass
    
    def writeSettings(self):
        settings.beginGroup("MainWindow")
        settings.setValue("maximized", self.isMaximized())
        if not self.isMaximized():
            settings.setValue("size", self.size())
            settings.setValue("pos", self.pos())
        settings.endGroup()
    
    def readSettings(self):
        settings.beginGroup("MainWindow")
        self.resize(settings.value("size", QSize(1280, 720)))
        self.move(settings.value("pos", QPoint(320, 124)))
        if settings.value("maximized", False, type=bool):
            self.showMaximized()
        settings.endGroup()

    @property   
    def activeFiles(self):
        return [i for i in self.mdi.subWindowList() if i.tabCount]

    @property
    def count(self):
        return len(self.mdi.subWindowList())
    
    @property
    def activeScene(self):
        return self.mdi.currentSubWindow().tabber.currentWidget()

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_A:
                for item in self.mdi.activeSubWindow().tabber.currentWidget().items:
                    item.setSelected(True)
            else:
                return
            event.accept()
        elif event.key() == Qt.Key_Q:
            if self.mdi.activeSubWindow() and self.mdi.activeSubWindow().tabber.currentWidget():
                for item in self.mdi.activeSubWindow().tabber.currentWidget().painter.selectedItems():
                    item.rotation -= 1
        elif event.key() == Qt.Key_E:
            if self.mdi.activeSubWindow() and self.mdi.activeSubWindow().tabber.currentWidget():
                for item in self.mdi.activeSubWindow().tabber.currentWidget().painter.selectedItems():
                    item.rotation += 1


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = appWindow()
    main.show()
    sys.exit(app.exec_())
