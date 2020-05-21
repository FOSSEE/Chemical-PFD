from fbs_runtime.application_context.PyQt5 import ApplicationContext

importTool = ApplicationContext()

def fileImporter(file):
    return importTool.get_resource(file)