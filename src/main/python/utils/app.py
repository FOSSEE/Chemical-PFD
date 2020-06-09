"""
Declare fbs application so that it can be imported in other modules.
"""

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import QSettings
from json import JSONEncoder, dumps, loads, dump, load

app = ApplicationContext()
settings = QSettings(QSettings.IniFormat, QSettings.UserScope ,"FOSSEE", "Chemical-PFD")

def fileImporter(file):
    # Helper function to fetch files from src/main/resources
    return app.get_resource(file)

class JSON_Encoder:
    
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
    
    def default(self, o):
        return o.__getstate__()
    
    def _encode(self, obj):
        return JSON_Encoder._encode(obj)

    def encode(self, obj):
        return super(JSON_Typer, self).encode(self._encode(obj))
    
shapeGrips = {}
lines = {}