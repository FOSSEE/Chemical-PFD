"""
Declare fbs application and various contextual variables so that it can be imported in other modules.
"""

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import QSettings, pyqtProperty, QResource
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget
from json import JSONEncoder, dumps, loads, dump, load
from os.path import join

from resources import resources #application resources defined in resources.qrc

app = ApplicationContext()
settings = QSettings(QSettings.IniFormat, QSettings.UserScope ,"FOSSEE", "Chemical-PFD")
version = app.build_settings['version']

def fileImporter(*file):
    # Helper function to fetch files from src/main/resources
    return app.get_resource(join(*file))

#set application stylesheet
with open(fileImporter("app.qss"), "r") as stylesheet:
    app.app.setStyleSheet(stylesheet.read())

class JSON_Encoder:
    """
    Defines serialization methods for differnt data types for json module
    """
    def _encode(obj):
        if isinstance(obj, dict):
            ## We'll need to iterate not just the value that default() usually gets passed
            ## But also iterate manually over each key: value pair in order to trap the keys.

            for key, val in list(obj.items()):
                if isinstance(val, dict):
                    val = loads(dumps(val, cls=JSON_Typer)) # This, is a EXTREMELY ugly hack..
                                                            # But it's the only quick way I can think of to 
                                                            # trigger a encoding of sub-dictionaries. (I'm also very tired, yolo!)
                else:
                    val = JSON_Encoder._encode(val)
                del(obj[key])
                obj[JSON_Encoder._encode(key)] = val
            return obj
        elif hasattr(obj, '__getstate__'):
            return obj.__getstate__()
        elif isinstance(obj, (list, set, tuple)):
            r = []
            for item in obj:
                r.append(loads(dumps(item, cls=JSON_Typer)))
            return r
        else:
            return obj

class JSON_Typer(JSONEncoder):
    """
    derived class for redirecting encode calls
    """
    def default(self, o):
        return o.__getstate__()
    
    def _encode(self, obj):
        return JSON_Encoder._encode(obj)

    def encode(self, obj):
        return super(JSON_Typer, self).encode(self._encode(obj))

memMap = {} #memory map for id references for loading projects