from fbs_runtime.application_context.PyQt5 import ApplicationContext
app = ApplicationContext()

def fileImporter(file):
    return app.get_resource(file)
