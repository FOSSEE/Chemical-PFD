"""
Declare fbs application so that it can be imported in other modules.
"""

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import QSettings

app = ApplicationContext()
settings = QSettings(QSettings.IniFormat, QSettings.UserScope ,"FOSSEE", "Chemical-PFD")

def fileImporter(file):
    # Helper function to fetch files from src/main/resources
    return app.get_resource(file)
