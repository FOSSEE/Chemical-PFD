import os
import sys
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication
from json import JSONEncoder

# ✅ Smart path importer (PyInstaller/dev compatible)
def fileImporter(*paths, ext=None):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    full_path = os.path.join(base_path, *paths)
    if ext and not full_path.lower().endswith(ext.lower()):
        full_path += ext

    exists = os.path.exists(full_path)
    return full_path

app = QApplication.instance()
if app is not None:
    qss_path = fileImporter("app.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())
    else:
        print("Stylesheet not found:", qss_path)

settings = QSettings(QSettings.IniFormat, QSettings.UserScope, "FOSSEE", "Chemical-PFD")
version = "1.0.0"
settings.setValue("version", version)

class JSON_Encoder:
    @staticmethod
    def encode(obj):
        if isinstance(obj, dict):
            return {JSON_Encoder.encode(k): JSON_Encoder.encode(v) for k, v in obj.items()}
        elif hasattr(obj, '__getstate__'):
            return obj.__getstate__()
        elif isinstance(obj, (list, set, tuple)):
            return [JSON_Encoder.encode(i) for i in obj]
        else:
            return obj

class JSON_Typer(JSONEncoder):
    def default(self, o):
        return getattr(o, '__getstate__', lambda: str(o))()

    def encode(self, obj):
        return super().encode(JSON_Encoder.encode(obj))

memMap = {}
