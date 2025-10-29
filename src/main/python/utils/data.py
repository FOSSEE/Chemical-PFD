import os
from json import load
from utils.pathutils import resource_path  

try:
    paperSizesPath = resource_path("resources/base/config/paperSizes.json")
    with open(paperSizesPath, "r") as f:
        paperSizes = load(f)

    toolbarItemsPath = resource_path("resources/base/config/items.json")
    with open(toolbarItemsPath, "r") as f:
        toolbarItems = load(f)

    # Extract keys
    sheetDimensionList = list(paperSizes.keys())
    ppiList = list(paperSizes[sheetDimensionList[0]].keys())
    defaultToolbarItems = toolbarItems.keys()

except FileNotFoundError as e:
   
    paperSizes = {}
    toolbarItems = {}
    sheetDimensionList = []
    ppiList = []
    defaultToolbarItems = []
