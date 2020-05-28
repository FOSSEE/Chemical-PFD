"""
Declare fbs application so that it can be imported in other modules.
"""

from fbs_runtime.application_context.PyQt5 import ApplicationContext
app = ApplicationContext()

def fileImporter(file):
    # Helper function to fetch files from src/main/resources
    return app.get_resource(file)
