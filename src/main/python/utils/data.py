"""
Imports data from json configs, so that they can be imported from this module.
"""

from json import load
from .app import fileImporter

paperSizes = load(open(fileImporter("config/paperSizes.json")))

sheetDimensionList = list(paperSizes.keys())

ppiList = list(paperSizes[sheetDimensionList[0]].keys())

toolbarItems = load(open(fileImporter("config/items.json")))

defaultToolbarItems = toolbarItems.keys()


