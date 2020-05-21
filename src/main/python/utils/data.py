import json
from .funcs import fileImporter

paperSizes = json.load(open(fileImporter("config/paperSizes.json")))

sheetDimensionList = list(paperSizes.keys())

ppiList = paperSizes[sheetDimensionList[0]].keys()

toolbarItems = json.load(open(fileImporter("config/items.json")))

defaultToolbarItems = toolbarItems.keys()


