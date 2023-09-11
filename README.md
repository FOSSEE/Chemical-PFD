# Chemical PFD Tool ##
Repository for a Process Flow Diagram Software 

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
[![CodeFactor](https://www.codefactor.io/repository/github/frg-fossee/chemical-pfd/badge/master)](https://www.codefactor.io/repository/github/frg-fossee/chemical-pfd/overview/master)
![Python](https://img.shields.io/badge/python-v3.6-blue.svg)
![version](https://img.shields.io/badge/version-0.0.1-blue)
[![python-mixedCase-style](https://img.shields.io/badge/code%20style-mixed-brightgreen.svg?style=flat)](https://wiki.c2.com/?CamelCase)
[![Dependencies](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)](https://github.com/FOSSEE/Chemical-PFD/network/dependencies)
[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](https://opensource.org/licenses/GPL-3.0)
 
## Screenshots
> Main window
<p align="center"><img width="95%" src="https://i.imgur.com/YHBTTHE.png"></p>

## Tech/framework used

#### Built with
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- [FBS](https://build-system.fman.io/)

## Features ####
> 1. Drag and Drop symbols from toolbar to scene
> 2. Undo Redo action
> 3. Save and Load files
> 4. Connect symbols with lines, and add labels
> 5. Create stream table
> 6. Use various paper sizes
> 7. Work on multiple diagrams and file at once
> 8. View diagrams side by side
> 9. Zoom In/out on the scene

## Code overview #

> #### src/main/python/main.py
> main application entry point, defines the main window and runs it.

> #### src/main/python/shapes
> Contains the shape and line definitions and logic.

> #### src/main/python/utils
> contains the sub window definitions along with various utility methods.


## Installation
#### clone this repository by running
```bash
git clone https://github.com/FOSSEE/Chemical-PFD.git
```
or by simply pressing the Clone or Download button and using your own preferred way of obtaining a working copy of the repository
#### requirements can be installed using (PIP should be up-to-date! tested on 20.0.2)
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
#### Then run using
```bash
fbs run
```
or 
```bash
python3 build.py run
```
additionally, if fbs doesnt work, you can manually run the program as
```bash
python3 ./src/main/python/main.py
```
that is run the **main.py** file located in **./src/main/python/main.py**
any output generated when run this way would be saved in **./src/main/python/**



## Building
There are two methods of doing this,
### Manually
#### Compiling the resources
Using pyrcc5, the resource.qrc can be compiled to a python file
```bash
pyrcc5 -o src/main/python/resources/resources.py src/main/ui/resources.rcc
```

#### Building binaries
Using fbs's freeze feature.
```bash
fbs freeze
```

#### Releasing
One can now build installer using fbs,
```bash
fbs release
```
note: Windows user will need [nsis](https://sourceforge.net/projects/nsis/) installed on their system and added to env path.
Additionally multiple things might need to be done, follow the onscreen instruction.


### Build.py script

#### Resource compilation and building binaries
can be done, by using build.py build
```bash
python3 build.py build
```

#### TODO

## Adding symbols
The process of adding symbols, is simple.

### Obtain svg for symbol
It is necessary that the symbol is in svg format.
One can use any of the many svg tools out there. 
We recommend [Inkscape](https://inkscape.org/)

### Preparing class entries

#### Class definition
Under src/main/python/shapes/shape.py, using the following as an example, one can create his own class definition for the symbol. The grip list is the percentage position of the grip item object along with the parent's width and height, the third value is its position and the fourth value if specified is the width/height if the grip is a line grip item.
```python
class HorizontalVessel(NodeItem):
    def __init__(self):
        super(HorizontalVessel, self).__init__("svg/Process Vessels/Horizontal Vessel")
        self.grips = [
            [50, 100, "top", 87.08554680344],
            [0, 50, "left"],
            [100, 50, "right"],
            [50, 0, "bottom", 87.08554680344]
        ]
```

#### Items.json Entry
The items.json is present in src/main/resources/base/config/items.json
Once the class name and category has been decided, an items.json entry can be configured as follows,
```javascript
{
    "Process Vessels": {
        "Horizontal Vessel": {
            "name": "Horizontal Vessel",
            "icon": ".\\Process Vessels\\Horizontal Vessel.png",
            "class": "Process Vessels",
            "object": "HorizontalVessel",
            "args": []
        },
    }
}
```

#### Toolbar icon
A 64x64 toolbar icon as a png needs to be prepared to be shown in the toolbar. It needs to be placed in src/main/resources/base/toolbar/ in the corresponding folder in the json file.

### Automating
Most of the above process can be automated, following are a few procedures one can use

#### Python Script(For making icons and items.json entries for multiple svgs)
You can find the script [here](https://gist.github.com/Blakeinstein/c349216ac1de86c66024d607140c9dfb)

#### Using the symbol generator (For class + items.json)
You can launch the tool while running the app, by clicking Add new Symbols in the edit menu.
Or by directly launching the edit symbol menu using build.py

```bash
python3 build.py symbolGen
```

## API Reference

The QtForPython docs were used to implement the program, one can reference them here 
- [QtForPython](https://doc.qt.io/qtforpython/contents.html)
The docs for Qt for C++ library can be found here
- [Qt](https://doc.qt.io/)

