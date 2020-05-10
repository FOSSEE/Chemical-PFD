import re

from PyQt5.QtCore import QFile, QIODevice
from PyQt5.QtXml import QDomDocument


class SvgHandler():
    def __init__(self, file):
        self.doc = QDomDocument("doc")
        self.file = file
        if not self.doc.setContent(self.file):
            print("Cannot parse the content")
            self.file.close()
            exit(-1)
        self.file.close()
        self.docElem = self.doc.documentElement()

    def checkViewBox(self):
        viewbox = self.docElem.attributes().namedItem("viewBox").nodeValue().split(" ")
        width = self.docElem.attributes().namedItem("width").nodeValue()
        height = self.docElem.attributes().namedItem("height").nodeValue()
        if viewbox[2] == width and viewbox[3] == height:
            return True
        else:
            return False

    def setColor(self, value):
        paths = self.docElem.elementsByTagName("path")
        for index in range(paths.size()):
            path = paths.at(index)
            style = path.attributes().namedItem("style")
            output = re.sub("stroke:[^;]*;", f"stroke:{value};", style.nodeValue())
            style.setNodeValue(output)

    def setStrokeWidth(self,value):
        paths = self.docElem.elementsByTagName("path")
        for index in range(paths.size()):
            path = paths.at(index)
            style = path.attributes().namedItem("style")
            output = re.sub("stroke-width:[^;]*;", f"stroke-width:{value};", style.nodeValue())
            style.setNodeValue(output)
        print(self.doc.toString())
        # output = re.sub('="stroke-width:[\d.]*;', f'="stroke-width:{target};', self.svg)
        # output = re.sub('stroke-width:[\d.]*;', f'stroke-width:{target};', self.svg)
