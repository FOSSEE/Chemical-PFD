from json import load
from .app import fileImporter

paperSizes = load(open(fileImporter("config/paperSizes.json")))

sheetDimensionList = list(paperSizes.keys())

ppiList = paperSizes[sheetDimensionList[0]].keys()

toolbarItems = load(open(fileImporter("config/items.json")))

defaultToolbarItems = toolbarItems.keys()


